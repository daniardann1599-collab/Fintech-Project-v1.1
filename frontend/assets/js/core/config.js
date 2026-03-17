export const API_BASE_URL =
  window.localStorage.getItem("bank_api_base") || "http://localhost:8000";

export const APP_ROUTES = {
  landing: "/index.html",
  login: "/login.html",
  register: "/register.html",
  customer: "/customer.html",
  admin: "/admin.html",
};
