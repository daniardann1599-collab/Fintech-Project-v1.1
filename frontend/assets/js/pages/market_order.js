import { apiRequest } from "../core/api.js";
import { requireAuth, logout } from "../core/auth.js";
import { clearAlert, showAlert, toErrorMessage } from "../core/ui.js";

const els = {
  alert: document.getElementById("order-alert"),
  form: document.getElementById("order-form"),
  symbol: document.getElementById("order-symbol"),
  market: document.getElementById("order-market"),
  side: document.getElementById("order-side"),
  account: document.getElementById("order-account"),
  quantity: document.getElementById("order-quantity"),
  name: document.getElementById("order-name"),
  hint: document.getElementById("order-hint"),
  logout: document.getElementById("logout-btn"),
};

function resolveSelection() {
  const params = new URLSearchParams(window.location.search);
  const symbol = params.get("symbol") || window.localStorage.getItem("selected_market_symbol");
  const market = params.get("market") || window.localStorage.getItem("selected_market");
  return { symbol, market };
}

function mapMarketToApi(market) {
  if (!market) return null;
  return market;
}

async function loadAccounts() {
  const accounts = await apiRequest("/accounts");
  if (!els.account) return;
  if (!accounts.length) {
    els.account.innerHTML = `<option value="">No accounts</option>`;
    return;
  }
  els.account.innerHTML = accounts
    .map((account) => `<option value="${account.id}">#${account.id} (${account.currency})</option>`)
    .join("");
}

function updateHint(market) {
  if (!els.hint) return;
  if (market === "SP500") {
    els.hint.textContent = "Use USD accounts for S&P 500 orders.";
  } else {
    els.hint.textContent = "";
  }
}

function bindForm(selected) {
  if (!els.form) return;

  els.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const side = els.side.value;
    const accountId = Number(els.account.value);
    const quantity = Number(els.quantity.value);
    const name = els.name.value.trim();
    const apiMarket = mapMarketToApi(selected.market);

    if (!selected.symbol || !apiMarket || !accountId || !quantity) {
      showAlert(els.alert, "error", "Order form is incomplete.");
      return;
    }

    const endpoint = side === "SELL" ? "/investments/sell" : "/investments/buy";

    try {
      await apiRequest(endpoint, {
        method: "POST",
        body: {
          account_id: accountId,
          market: apiMarket,
          symbol: selected.symbol,
          name: name || undefined,
          quantity,
        },
      });
      showAlert(els.alert, "success", `Order ${side.toLowerCase()} submitted.`);
      els.form.reset();
      els.symbol.value = selected.symbol;
      els.market.value = selected.market;
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });
}

async function init() {
  const session = await requireAuth("CUSTOMER");
  if (!session) return;

  const selection = resolveSelection();
  if (!selection.symbol || !selection.market) {
    showAlert(els.alert, "error", "Select a stock from the market page first.");
  }

  if (els.symbol) els.symbol.value = selection.symbol || "";
  if (els.market) els.market.value = selection.market || "";
  updateHint(selection.market);

  await loadAccounts();
  bindForm(selection);

  els.logout?.addEventListener("click", logout);
}

init();
