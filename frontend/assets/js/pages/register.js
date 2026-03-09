import { APP_ROUTES } from "../core/config.js";
import { loginWithPassword, registerUser } from "../core/auth.js";
import { apiRequest } from "../core/api.js";
import { getSession, saveSession } from "../core/storage.js";
import { clearAlert, showAlert, toErrorMessage } from "../core/ui.js";

const form = document.getElementById("register-form");
const alertBox = document.getElementById("register-alert");

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearAlert(alertBox);

  const fullName = form.full_name.value.trim();
  const documentId = form.document_id.value.trim();
  const email = form.email.value.trim();
  const password = form.password.value;
  const confirmPassword = form.confirm_password.value;

  if (!fullName || !documentId || !email || !password || !confirmPassword) {
    showAlert(alertBox, "error", "Please fill all fields.");
    return;
  }
  if (password.length < 8) {
    showAlert(alertBox, "error", "Password must contain at least 8 characters.");
    return;
  }
  if (password !== confirmPassword) {
    showAlert(alertBox, "error", "Password confirmation does not match.");
    return;
  }

  const submitButton = form.querySelector("button[type='submit']");
  submitButton.disabled = true;

  try {
    const user = await registerUser({ email, password, role: "CUSTOMER" });
    await loginWithPassword(email, password);
    const customer = await apiRequest("/customers", {
      method: "POST",
      body: {
        user_id: user.id,
        kyc_full_name: fullName,
        kyc_document_id: documentId,
      },
    });

    const session = getSession();
    saveSession({ ...session, customerId: customer.id });

    showAlert(alertBox, "success", "Registration successful. Redirecting to dashboard...");
    setTimeout(() => {
      window.location.href = APP_ROUTES.customer;
    }, 500);
  } catch (error) {
    showAlert(alertBox, "error", toErrorMessage(error, "Registration failed"));
  } finally {
    submitButton.disabled = false;
  }
});
