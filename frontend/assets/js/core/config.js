export const API_BASE_URL =
  window.localStorage.getItem("bank_api_base") || "https://fintech-project-v11-production.up.railway.app";

export const APP_ROUTES = {
  landing: "/index.html",
  login: "/login.html",
  register: "/register.html",
  customer: "/customer.html",
  admin: "/admin.html",
};
