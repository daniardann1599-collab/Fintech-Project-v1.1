import { APP_ROUTES } from "../core/config.js";
import { loginWithPassword, redirectByRole } from "../core/auth.js";
import { getSession } from "../core/storage.js";
import { clearAlert, showAlert, toErrorMessage } from "../core/ui.js";

const form = document.getElementById("login-form");
const alertBox = document.getElementById("login-alert");

const existingSession = getSession();
if (existingSession?.token && existingSession?.user?.role) {
  redirectByRole(existingSession.user.role);
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearAlert(alertBox);

  const email = form.email.value.trim();
  const password = form.password.value;

  if (!email || !password) {
    showAlert(alertBox, "error", "Email and password are required.");
    return;
  }

  const submitButton = form.querySelector("button[type='submit']");
  submitButton.disabled = true;

  try {
    const { user } = await loginWithPassword(email, password);
    showAlert(alertBox, "success", "Authentication successful. Redirecting...");
    setTimeout(() => redirectByRole(user.role), 450);
  } catch (error) {
    showAlert(alertBox, "error", toErrorMessage(error, "Login failed"));
  } finally {
    submitButton.disabled = false;
  }
});

const registerLink = document.getElementById("go-register");
registerLink?.addEventListener("click", () => {
  window.location.href = APP_ROUTES.register;
});
