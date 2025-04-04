from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from ecom_user.authentication import EcomUserJWTAuthentication
from ecom_user.models import EcomUser
from ecom_user.serializers import (
    ChangeCurrentPasswordSerializer,
    UserAccountSerializer,
    UserNavbarSerializer,
    UserPhoneSerializer,
    UserPhoneVerificationSerializer,
)
from ecom_user.sms_service import (
    create_phone_verify_cache_key,
    create_sms_cooldown_cache_key,
    process_phone_verification,
)
from ecom_user.throttle import CodeSubmitAnonRateThrottle, SMSAnonRateThrottle


class UserLoginViewSet(ViewSet):
    """
    Provides the following actions:
    - request_code: Sends a verficiation code SMS to user which is to be used in the next action.
    - verify_code: Requires a verification code to be inputted, which is requested via previous action.
      If the request is succesful, a pair of access and refresh token will be included in the body of the
      response. Note that if its the first time which the phone number is being registered, then
      an EcomUser instance will be created with an unusable password using the phone number.
    """

    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"], throttle_classes=[SMSAnonRateThrottle])
    def request_code(self, request):
        # time.sleep(3)
        serializer = UserPhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inputted_phone = serializer.validated_data["phone"]
        sms_cooldown_cache_key = create_sms_cooldown_cache_key(inputted_phone)
        code_cooldown_time = cache.ttl(sms_cooldown_cache_key)
        if code_cooldown_time:
            return Response(
                {
                    "error": "Request blocked by SMS rate limiter",
                    "cooldown_time": f"{code_cooldown_time}",
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"X-Rate-Limit-Type": "SMS_LIMIT"},
            )
        process_phone_verification(serializer.validated_data["phone"])
        return Response(
            {
                "success": f"verification code sent to user for phone {inputted_phone} via SMS"
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(
        detail=False, methods=["post"], throttle_classes=[CodeSubmitAnonRateThrottle]
    )
    def verify_code(self, request):
        serializer = UserPhoneVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cache_key = create_phone_verify_cache_key(serializer.validated_data["phone"])
        cached_code = cache.get(cache_key)
        if not cached_code:
            return Response(
                {"error": "verification code is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if serializer.validated_data["verification_code"] != cached_code:
            return Response(
                {"error": "verification code is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cache.delete(cache_key)
        try:
            user = EcomUser.objects.get(phone=serializer.validated_data["phone"])
        except EcomUser.DoesNotExist:
            user = serializer.save()
        refresh = RefreshToken.for_user(user)
        refresh["user_type"] = (
            "normal"  # payload for distinguishing normal users from admin users
        )
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class UserAccountViewSet(ViewSet):
    """
    Provides the following actions (requires the current user to be authenticated):
    - account_info: retrieves the current authenticated user's account info.
    - update_info: update the current user account info (except phone, email and password)
    - navbar_info: retrieves the current authenticated user's navbar info
    - change_password: for changing current password.
    - change_phone_request: for changing user's current phone password by requesting an OTP via SMS,
      a verification code is sent to the new phone and then used in the next action
      to complete the phone number update process.
    - change_phone_verify: for verifying the new phone number, the verification code from previous action
      should be inputted inorder to complete the phone number update process.
    """

    authentication_classes = [EcomUserJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def navbar_info(self, request):
        serializer = UserNavbarSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def get_info(self, request):
        serializer = UserAccountSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["put"])
    def update_info(self, request):
        serializer = UserAccountSerializer(
            self.request.user, request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["put"])
    def change_password(self, request):
        serializer = ChangeCurrentPasswordSerializer(request.user, request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=["put"], throttle_classes=[SMSAnonRateThrottle])
    def change_phone_request(self, request):
        serializer = UserPhoneSerializer(request.user, request.data)
        serializer.is_valid(raise_exception=True)
        new_phone = serializer.validated_data["phone"]
        sms_cooldown_cache_key = create_sms_cooldown_cache_key(new_phone)
        if cache.get(create_sms_cooldown_cache_key(new_phone)):
            return Response(
                f"Too many code requests, please try again in {cache.ttl(sms_cooldown_cache_key)} seconds",
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        process_phone_verification(new_phone)
        return Response(status=status.HTTP_202_ACCEPTED)

    @action(
        detail=False, methods=["put"], throttle_classes=[CodeSubmitAnonRateThrottle]
    )
    def change_phone_verify(self, request):
        serializer = UserPhoneVerificationSerializer(request.user, request.data)
        serializer.is_valid(raise_exception=True)
        cached_code = cache.get(
            create_phone_verify_cache_key(serializer.validated_data["phone"])
        )
        if not cached_code:
            return Response(
                {"error": "server is not expecting a verification code for this phone"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if serializer.validated_data["verification_code"] != cached_code:
            return Response(
                "The inputted code is invalid", status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response("Phone number changed succesfuly", status=status.HTTP_200_OK)
