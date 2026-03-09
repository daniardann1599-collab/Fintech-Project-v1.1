export function showAlert(element, type, message) {
  if (!element) return;
  element.classList.remove("error", "success", "show");
  element.classList.add(type);
  element.textContent = message;
  element.classList.add("show");
}

export function clearAlert(element) {
  if (!element) return;
  element.classList.remove("show", "error", "success");
  element.textContent = "";
}

export function formatCurrency(amount, currency = "USD") {
  const numeric = Number(amount || 0);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(numeric);
}

export function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function toErrorMessage(error, fallback = "Something went wrong") {
  if (!error) return fallback;
  if (error.message) return error.message;
  return fallback;
}

export function switchView(containerSelector, targetViewId) {
  const container = document.querySelector(containerSelector);
  if (!container) return;

  container.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
  const target = container.querySelector(`#${targetViewId}`);
  if (target) target.classList.add("active");
}

export function activateNav(navSelector, key) {
  const nav = document.querySelector(navSelector);
  if (!nav) return;
  nav.querySelectorAll("[data-view]").forEach((node) => {
    node.classList.toggle("active", node.dataset.view === key);
  });
}

export function ensureNumber(value) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return null;
  return parsed;
}
