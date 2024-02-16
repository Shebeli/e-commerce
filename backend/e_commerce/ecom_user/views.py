import random
import string

from django.core.cache import cache
from django.contrib.auth.tokens import default_token_generator
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import get_object_or_404

from .throttle import SMSAnonRateThrottle, RegisterAnonRateThrottle
from .models import EcomUser
from .serializers import (
    UserProfileSerializer,
    PhoneSerializer,
    CreateUserSerializer,
    ChangeCurrentPasswordSerializer,
    ResetPasswordSerializer,
    VerifyCodeSerializer,
    VerifyCodeSerializer,
)
from .sms import (
    send_sms,
    create_forgot_password_message,
    create_verify_register_message,
)


def get_code_cooldown_time(phone: str) -> str:
    cache_key = f"code_cooldown_for_{phone}"
    return cache.ttl(cache_key)


class UserSignUpViewSet(viewsets.ViewSet):
    """
    Provides the following actions:
    - register: Sends a verify register code SMS to user to complete their registration.
    - confirm_register: Input the code recieved from action 'register' by sms
      to complete registaration (returns a token pair upon success)
    """

    def get_register_code_cache_key(self, phone: str) -> str:
        return f"register_code_for_{phone}"

    def create_random_code(length: int = 5) -> str:
        return random.choice(string.digits for _ in range(length))

    @action(detail=False, methods=["post"], throttle_classes=[SMSAnonRateThrottle])
    def register(self, request):
        serializer = PhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        register_code = self.create_random_code()
        inputed_phone = serializer.data["phone"]
        code_cooldown_time = self.get_code_cooldown_time(
            "register_code_for", inputed_phone
        )
        if code_cooldown_time:
            return Response(
                {"cooldown time to request another code": f"{code_cooldown_time}s"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        send_sms(
            reciever_phone_number=inputed_phone,
            message=create_verify_register_message(register_code),
        )
        cache.set(f"register_code_cooldown_for_{inputed_phone}", True, 60 * 2)
        cache.set(
            self.get_register_code_cache_key(inputed_phone), register_code, 60 * 15
        )
        return Response(
            {
                "success": f"forgot pass code sent to user for phone {inputed_phone} by SMS"
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=["post"], throttle_classes=[RegisterAnonRateThrottle])
    def confirm_register(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cached_code = cache.get(
            self.get_register_code_cache_key(serializer.data["phone"])
        )
        if not cached_code:
            return Response(
                {"error": "server is not expecting a verification code for this phone"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if serializer.data["code"] != cached_code:
            return Response(
                {"error": "verification code is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class UserForgotPasswordViewSet(viewsets.ViewSet):
    """
    Provides the following actions:
    - forgot_password: Sends a reset password code to user using SMS.
    - confirm_forgot_password: Input the code recieved from action 'reset_password' and
      allows the user to change their password by giving them a one time generated token
      to the next action reset_password.
    - reset_password: user can input their new password and update their password
      which after wards logs them in by returning a token pair.
    """

    @action(detail=False, methods=["POST"])
    def forgot_password(self, request):
        serializer = PhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(EcomUser, phone=serializer.data["phone"])
        code_cooldown_time = get_code_cooldown_time(user)
        if code_cooldown_time:
            return Response(
                {"cooldown time to request another code": f"{code_cooldown_time}s"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        forgot_code = self.create_random_code()
        send_sms(
            reciever_phone_number=user.phone,
            message=create_forgot_password_message(forgot_code),
        )
        cache.set(f"forgot_pass_cooldown_for_{user.phone}")
        cache.set(f"forgot_pass_code_for_{user.phone}")

        return Response(
            {"success": f"forgot pass code sent to user for phone {user.phone} by SMS"},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=["POST"])
    def confirm_forgot_password(self, request):
        """
        The user is signed in after this action, its recommended to redirect user to reset_password action
        but still can be skipped.
        """
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(EcomUser, phone=serializer.data["phone"])
        cached_code = cache.get(f"forgot_pass_code_for_{user.phone}")
        if not cached_code:
            return Response(
                {"error": "server is not expecting a verification code for this phone"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if serializer.data["code"] != cached_code:
            return Response(
                {"error": "verification code is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        password_reset_token = default_token_generator.make_token()
        return Response(
            {
                "user_id": user.id,
                "password reset token": password_reset_token,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=['PUT'])
    def reset_password(self, request):
        "One time access token should be provided which is retrieved from the previous action, confirm_forgot_password"
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user = serializer.get_user()
        refresh_token = RefreshToken.for_user(user)
        return Response(
            {"refresh": str(refresh_token), "access": str(refresh_token.access)},
            status=status.HTTP_202_ACCEPTED,
        )


class UserProfileViewSet(
    viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin
):
    """
    Required authentication: UserIsAuthenticated
    Provides the following actions:
    - retrieve: retrieves the current authenticated user profile.
    - update: update the current authenticated user profile info (except phone and email)
    """

    serializer_class = UserProfileSerializer
    queryset = EcomUser.objects.all()
    permission_classes = [IsAuthenticated]
