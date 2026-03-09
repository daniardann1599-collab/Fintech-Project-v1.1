import { apiRequest } from "../core/api.js";
import { requireAuth, logout } from "../core/auth.js";
import {
  activateNav,
  clearAlert,
  formatCurrency,
  formatDate,
  showAlert,
  switchView,
  toErrorMessage,
} from "../core/ui.js";

const state = {
  session: null,
  accounts: [],
  balances: {},
  transfers: [],
  auditLogs: [],
  lookedUpCustomers: [],
};

const els = {
  alert: document.getElementById("admin-alert"),
  nav: document.getElementById("admin-nav"),
  adminName: document.getElementById("admin-name"),
  adminSub: document.getElementById("admin-sub"),
  kpiAudit: document.getElementById("kpi-audit-count"),
  kpiTransfers: document.getElementById("kpi-transfer-count"),
  kpiAccounts: document.getElementById("kpi-account-count"),
  auditBody: document.getElementById("audit-table-body"),
  transferBody: document.getElementById("admin-transfer-table-body"),
  accountsBody: document.getElementById("admin-accounts-table-body"),
  customerBody: document.getElementById("admin-customers-table-body"),
  adjustForm: document.getElementById("adjust-balance-form"),
  createCustomerForm: document.getElementById("admin-create-customer-form"),
  lookupCustomerForm: document.getElementById("admin-lookup-customer-form"),
  updateStatusForm: document.getElementById("admin-update-status-form"),
  flushOutboxBtn: document.getElementById("flush-outbox-btn"),
  accountSelect: document.getElementById("adjust-account-id"),
  logoutBtn: document.getElementById("admin-logout-btn"),
};

function renderTopBar() {
  els.adminName.textContent = `Welcome, ${state.session.user.email}`;
  els.adminSub.textContent = `Role: ADMIN | Last sync: ${new Date().toLocaleTimeString()}`;
  els.kpiAudit.textContent = String(state.auditLogs.length);
  els.kpiTransfers.textContent = String(state.transfers.length);
  els.kpiAccounts.textContent = String(state.accounts.length);
}

function renderAudit() {
  if (!state.auditLogs.length) {
    els.auditBody.innerHTML = `<tr><td colspan="5">No audit logs available.</td></tr>`;
    return;
  }

  els.auditBody.innerHTML = state.auditLogs
    .slice(0, 200)
    .map(
      (row) => `
        <tr>
          <td>#${row.id}</td>
          <td>${row.user_id ?? "-"}</td>
          <td>${row.action}</td>
          <td>${row.outcome}</td>
          <td>${formatDate(row.timestamp)}</td>
        </tr>
      `
    )
    .join("");
}

function renderTransfers() {
  if (!state.transfers.length) {
    els.transferBody.innerHTML = `<tr><td colspan="7">No transfers available.</td></tr>`;
    return;
  }

  els.transferBody.innerHTML = state.transfers
    .map(
      (transfer) => `
      <tr>
        <td>#${transfer.id}</td>
        <td>${transfer.from_account}</td>
        <td>${transfer.to_account}</td>
        <td>${formatCurrency(transfer.amount, state.accounts[0]?.currency || "USD")}</td>
        <td><span class="pill pending">${transfer.status}</span></td>
        <td>${formatDate(transfer.created_at)}</td>
        <td>
          ${
            transfer.status === "PENDING"
              ? `<button class="button button-ghost admin-execute-transfer-btn" data-transfer-id="${transfer.id}">Execute</button>`
              : `<span class="inline-muted">-</span>`
          }
        </td>
      </tr>
    `
    )
    .join("");
}

function renderAccounts() {
  if (!state.accounts.length) {
    els.accountsBody.innerHTML = `<tr><td colspan="6">No accounts available.</td></tr>`;
    return;
  }

  els.accountsBody.innerHTML = state.accounts
    .map(
      (account) => `
      <tr>
        <td>#${account.id}</td>
        <td>${account.customer_id}</td>
        <td>${account.currency}</td>
        <td>${formatCurrency(state.balances[account.id] ?? 0, account.currency)}</td>
        <td>${formatDate(account.created_at)}</td>
        <td><span class="pill success">MANAGED</span></td>
      </tr>
    `
    )
    .join("");
}

function renderCustomers() {
  if (!state.lookedUpCustomers.length) {
    els.customerBody.innerHTML = `<tr><td colspan="6">Use customer lookup by ID to populate records.</td></tr>`;
    return;
  }

  els.customerBody.innerHTML = state.lookedUpCustomers
    .map(
      (customer) => `
      <tr>
        <td>#${customer.id}</td>
        <td>${customer.user_id}</td>
        <td>${customer.kyc_full_name}</td>
        <td>${customer.kyc_document_id}</td>
        <td>${customer.status}</td>
        <td>${formatDate(customer.created_at)}</td>
      </tr>
    `
    )
    .join("");
}

function populateAccountSelector() {
  els.accountSelect.innerHTML = state.accounts
    .map((account) => `<option value="${account.id}">#${account.id} (${account.currency})</option>`)
    .join("");
}

async function loadAdminData() {
  const [accounts, transfers, auditLogs] = await Promise.all([
    apiRequest("/accounts"),
    apiRequest("/transfers"),
    apiRequest("/audit/logs"),
  ]);

  state.accounts = accounts;
  state.transfers = transfers;
  state.auditLogs = auditLogs;

  const balances = await Promise.all(
    accounts.map(async (account) => {
      const balance = await apiRequest(`/accounts/${account.id}/balance`);
      return [account.id, Number(balance.balance || 0)];
    })
  );

  state.balances = {};
  balances.forEach(([id, amount]) => {
    state.balances[id] = amount;
  });

  populateAccountSelector();
  renderTopBar();
  renderAudit();
  renderTransfers();
  renderAccounts();
  renderCustomers();
}

function initNavigation() {
  els.nav?.querySelectorAll("[data-view]").forEach((link) => {
    link.addEventListener("click", () => {
      const key = link.dataset.view;
      activateNav("#admin-nav", key);
      switchView("#admin-views", `view-${key}`);
    });
  });
}

function bindActions() {
  els.logoutBtn?.addEventListener("click", logout);

  els.adjustForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const accountId = Number(els.adjustForm.account_id.value);
    const operation = els.adjustForm.operation.value;
    const amount = Number(els.adjustForm.amount.value);
    const reference = els.adjustForm.reference_id.value.trim();

    if (!accountId || !amount || !reference) {
      showAlert(els.alert, "error", "Balance form is incomplete.");
      return;
    }

    try {
      const endpoint = operation === "DEPOSIT" ? "deposit" : "withdraw";
      await apiRequest(`/accounts/${accountId}/${endpoint}`, {
        method: "POST",
        body: { amount, reference_id: reference },
      });
      showAlert(els.alert, "success", `${operation.toLowerCase()} operation completed.`);
      await loadAdminData();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.lookupCustomerForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const customerId = Number(els.lookupCustomerForm.customer_id.value);
    if (!customerId) {
      showAlert(els.alert, "error", "Provide a valid customer ID.");
      return;
    }

    try {
      const customer = await apiRequest(`/customers/${customerId}`);
      const exists = state.lookedUpCustomers.some((row) => row.id === customer.id);
      if (!exists) state.lookedUpCustomers.unshift(customer);
      renderCustomers();
      showAlert(els.alert, "success", `Customer #${customer.id} loaded.`);
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.createCustomerForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const userId = Number(els.createCustomerForm.user_id.value);
    const fullName = els.createCustomerForm.kyc_full_name.value.trim();
    const documentId = els.createCustomerForm.kyc_document_id.value.trim();

    if (!userId || !fullName || !documentId) {
      showAlert(els.alert, "error", "Customer creation form is incomplete.");
      return;
    }

    try {
      const customer = await apiRequest("/customers", {
        method: "POST",
        body: {
          user_id: userId,
          kyc_full_name: fullName,
          kyc_document_id: documentId,
        },
      });
      state.lookedUpCustomers.unshift(customer);
      renderCustomers();
      showAlert(els.alert, "success", `Customer #${customer.id} created.`);
      els.createCustomerForm.reset();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.updateStatusForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const customerId = Number(els.updateStatusForm.customer_id.value);
    const status = els.updateStatusForm.status.value;

    if (!customerId || !status) {
      showAlert(els.alert, "error", "Status update form is incomplete.");
      return;
    }

    try {
      const customer = await apiRequest(`/customers/${customerId}/status`, {
        method: "PATCH",
        body: { status },
      });
      state.lookedUpCustomers = state.lookedUpCustomers.map((item) => (item.id === customer.id ? customer : item));
      if (!state.lookedUpCustomers.some((item) => item.id === customer.id)) {
        state.lookedUpCustomers.unshift(customer);
      }
      renderCustomers();
      showAlert(els.alert, "success", `Customer #${customer.id} status updated.`);
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.flushOutboxBtn?.addEventListener("click", async () => {
    clearAlert(els.alert);
    try {
      const flushed = await apiRequest("/audit/outbox/flush", { method: "POST" });
      showAlert(els.alert, "success", `Outbox flush complete. Processed: ${flushed.length}`);
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.transferBody?.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    if (!target.classList.contains("admin-execute-transfer-btn")) return;

    const transferId = Number(target.dataset.transferId);
    if (!transferId) return;

    clearAlert(els.alert);
    target.setAttribute("disabled", "true");
    try {
      await apiRequest(`/transfers/${transferId}/execute`, { method: "POST" });
      showAlert(els.alert, "success", `Transfer #${transferId} executed.`);
      await loadAdminData();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    } finally {
      target.removeAttribute("disabled");
    }
  });
}

async function init() {
  state.session = await requireAuth("ADMIN");
  if (!state.session) return;

  initNavigation();
  bindActions();

  try {
    await loadAdminData();
  } catch (error) {
    showAlert(els.alert, "error", toErrorMessage(error, "Unable to load admin data"));
  }
}

init();
