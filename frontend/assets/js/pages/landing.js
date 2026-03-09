import { APP_ROUTES } from "../core/config.js";
import { getSession } from "../core/storage.js";

const continueBtn = document.getElementById("continue-session");

if (continueBtn) {
  const session = getSession();
  if (!session?.token) {
    continueBtn.classList.add("hidden");
  } else {
    continueBtn.addEventListener("click", () => {
      const role = session.user?.role;
      window.location.href = role === "ADMIN" ? APP_ROUTES.admin : APP_ROUTES.customer;
    });
  }
}
