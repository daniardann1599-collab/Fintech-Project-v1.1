import { apiRequest } from "../core/api.js";
import { requireAuth, logout } from "../core/auth.js";
import { clearAlert, formatCurrency, formatPercent, showAlert, toErrorMessage } from "../core/ui.js";

const state = {
  sp500: [],
  search: "",
  sortDirection: "desc",
  lastUpdated: null,
};

const els = {
  alert: document.getElementById("market-alert"),
  sub: document.getElementById("market-sub"),
  search: document.getElementById("market-search"),
  sort: document.getElementById("market-sort"),
  sp500Body: document.getElementById("sp500-table-body"),
  sp500Status: document.getElementById("sp500-status"),
  sectionSp500: document.getElementById("section-sp500"),
  logout: document.getElementById("logout-btn"),
};

function applyFilters(rows) {
  const query = state.search.trim().toUpperCase();
  if (!query) return rows;
  return rows.filter((row) => row.symbol.toUpperCase().includes(query));
}

function sortRows(rows) {
  const factor = state.sortDirection === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => (a.price - b.price) * factor);
}

function renderRows(rows, tbody, market, emptyMessage = "No stocks found.") {
  if (!tbody) return;
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="5">${emptyMessage}</td></tr>`;
    return;
  }

  tbody.innerHTML = rows
    .map((row) => {
      const changeClass = row.change_percent > 0 ? "pnl-positive" : row.change_percent < 0 ? "pnl-negative" : "";
      const currency = "USD";
      return `
        <tr>
          <td>${row.symbol}</td>
          <td>${row.name}</td>
          <td>${formatCurrency(row.price, currency)}</td>
          <td class="${changeClass}">${formatPercent(row.change_percent)}</td>
          <td>
            <button class="button button-ghost select-stock" type="button" data-symbol="${row.symbol}" data-market="${market}">Select</button>
          </td>
        </tr>
      `;
    })
    .join("");
}

function renderTables() {
  const sp500 = sortRows(applyFilters(state.sp500));
  renderRows(sp500, els.sp500Body, "SP500");

  if (els.sort) {
    els.sort.textContent = `Price: ${state.sortDirection === "asc" ? "Low to High" : "High to Low"}`;
  }
}

function updateStatus() {
  const timestamp = state.lastUpdated ? new Date(state.lastUpdated).toLocaleTimeString() : "-";
  if (els.sub) {
    els.sub.textContent = `Last updated: ${timestamp} • Refreshing every 5 seconds`;
  }
  if (els.sp500Status) {
    els.sp500Status.textContent = `Last update: ${timestamp}`;
  }
}

async function loadMarketData() {
  clearAlert(els.alert);
  if (els.sp500Body) els.sp500Body.innerHTML = `<tr><td colspan="5">Loading...</td></tr>`;

  try {
    const sp500 = await apiRequest("/api/market/sp500");
    state.sp500 = Array.isArray(sp500) ? sp500 : [];
  } catch (error) {
    showAlert(els.alert, "error", toErrorMessage(error, "Unable to load S&P 500 data"));
    state.sp500 = [];
  }

  state.lastUpdated = Date.now();
  renderTables();
  updateStatus();
}

function bindControls() {
  els.search?.addEventListener("input", (event) => {
    state.search = event.target.value || "";
    renderTables();
  });

  els.sort?.addEventListener("click", () => {
    state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
    renderTables();
  });

  els.sp500Body?.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const button = target.closest(".select-stock");
    if (!button) return;
    const symbol = button.dataset.symbol;
    const market = button.dataset.market;
    if (!symbol || !market) return;
    window.localStorage.setItem("selected_market_symbol", symbol);
    window.localStorage.setItem("selected_market", market);
    window.location.href = `/investments/order/index.html?symbol=${encodeURIComponent(symbol)}&market=${encodeURIComponent(market)}`;
  });

  els.logout?.addEventListener("click", logout);
}

async function init() {
  const session = await requireAuth("CUSTOMER");
  if (!session) return;

  bindControls();
  await loadMarketData();

  setInterval(async () => {
    try {
      const sp500 = await apiRequest("/api/market/sp500");
      state.sp500 = Array.isArray(sp500) ? sp500 : [];
      state.lastUpdated = Date.now();
      renderTables();
      updateStatus();
    } catch (error) {
      // keep last data; show lightweight status
      if (els.sub) {
        els.sub.textContent = `Market refresh failed: ${toErrorMessage(error)}`;
      }
    }
  }, 5000);
}

init();
