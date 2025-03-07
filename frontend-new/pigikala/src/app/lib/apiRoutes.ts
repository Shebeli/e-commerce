export const API_ROUTES = {
  AUTH: {
    REFRESH: "/api/user/token/refresh",
    ACCESS: "/api/user/token/login",
  },
  USER: {
    LOGIN: "api/user/login/request_code/",
    VERIFY_CODE: "api/user/login/verify_code/",
    NAVBAR_PROFILE: "/api/user/account/navbar_info/",
  },
  PRODUCT: {
    SUB_CATEGORIES: "/api/products/sub-categories/",
    FULL_CATEGORIES: "/api/products/full-categories/",
    PRODUCTS_LIST: "api/products",
  },
};
