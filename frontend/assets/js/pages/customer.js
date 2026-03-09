import { apiRequest } from "../core/api.js";
import { requireAuth, logout } from "../core/auth.js";
import { getSession, saveSession } from "../core/storage.js";
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
  customer: null,
  accounts: [],
  balances: {},
  totalBalance: 0,
  transfers: [],
  ledgerEntries: [],
};

const els = {
  alert: document.getElementById("customer-alert"),
  nav: document.getElementById("customer-nav"),
  views: document.querySelector("#customer-views"),
  welcomeName: document.getElementById("welcome-name"),
  welcomeSub: document.getElementById("welcome-sub"),
  kpiBalance: document.getElementById("kpi-total-balance"),
  kpiAccounts: document.getElementById("kpi-accounts-count"),
  kpiTransfers: document.getElementById("kpi-transfers-count"),
  accountsTableBody: document.getElementById("accounts-table-body"),
  transfersTableBody: document.getElementById("transfers-table-body"),
  ledgerTableBody: document.getElementById("ledger-table-body"),
  profileCard: document.getElementById("profile-card"),
  accountSelectTransferFrom: document.getElementById("transfer-from-account"),
  accountSelectTransferTo: document.getElementById("transfer-to-account"),
  accountSelectDeposit: document.getElementById("deposit-account"),
  accountSelectLedger: document.getElementById("ledger-account"),
  createAccountForm: document.getElementById("create-account-form"),
  transferForm: document.getElementById("transfer-form"),
  depositForm: document.getElementById("deposit-form"),
  kycForm: document.getElementById("kyc-form"),
  kycPanel: document.getElementById("kyc-panel"),
  logoutBtn: document.getElementById("logout-btn"),
};

function renderAccounts() {
  if (!state.accounts.length) {
    els.accountsTableBody.innerHTML = `<tr><td colspan="5">No accounts yet. Create your first account.</td></tr>`;
    return;
  }

  els.accountsTableBody.innerHTML = state.accounts
    .map((account) => {
      const balance = state.balances[account.id] ?? 0;
      return `
        <tr>
          <td>#${account.id}</td>
          <td>${account.currency}</td>
          <td>${formatCurrency(balance, account.currency)}</td>
          <td>${formatDate(account.created_at)}</td>
          <td><span class="pill success">ACTIVE</span></td>
        </tr>
      `;
    })
    .join("");
}

function renderTransfers() {
  if (!state.transfers.length) {
    els.transfersTableBody.innerHTML = `<tr><td colspan="7">No transfers found.</td></tr>`;
    return;
  }

  els.transfersTableBody.innerHTML = state.transfers
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
              ? `<button class="button button-ghost execute-transfer-btn" data-transfer-id="${transfer.id}">Execute</button>`
              : `<span class="inline-muted">-</span>`
          }
        </td>
      </tr>
    `
    )
    .join("");
}

function renderLedgerEntries() {
  if (!state.ledgerEntries.length) {
    els.ledgerTableBody.innerHTML = `<tr><td colspan="5">No ledger entries for this account.</td></tr>`;
    return;
  }

  els.ledgerTableBody.innerHTML = state.ledgerEntries
    .map(
      (entry) => `
      <tr>
        <td>#${entry.id}</td>
        <td>${entry.type}</td>
        <td>${formatCurrency(entry.amount, state.accounts[0]?.currency || "USD")}</td>
        <td>${entry.reference_id}</td>
        <td>${formatDate(entry.created_at)}</td>
      </tr>
    `
    )
    .join("");
}

function renderProfile() {
  const user = state.session?.user;
  if (!user) return;

  const customer = state.customer;

  els.profileCard.innerHTML = `
    <div class="form-row-2">
      <div class="card">
        <span class="feature-tag">Identity</span>
        <p><strong>User ID:</strong> ${user.id}</p>
        <p><strong>Email:</strong> ${user.email}</p>
        <p><strong>Role:</strong> ${user.role}</p>
      </div>
      <div class="card">
        <span class="feature-tag">KYC Profile</span>
        <p><strong>Customer ID:</strong> ${customer?.id ?? "Not created"}</p>
        <p><strong>Full Name:</strong> ${customer?.kyc_full_name ?? "-"}</p>
        <p><strong>Document ID:</strong> ${customer?.kyc_document_id ?? "-"}</p>
        <p><strong>Status:</strong> ${customer?.status ?? "-"}</p>
      </div>
    </div>
  `;
}

function renderTopBar() {
  const customerName = state.customer?.kyc_full_name || state.session.user.email;
  els.welcomeName.textContent = `Welcome back, ${customerName}`;
  els.welcomeSub.textContent = `Role: ${state.session.user.role} | Last sync: ${new Date().toLocaleTimeString()}`;
  els.kpiBalance.textContent = formatCurrency(state.totalBalance, state.accounts[0]?.currency || "USD");
  els.kpiAccounts.textContent = String(state.accounts.length);
  els.kpiTransfers.textContent = String(state.transfers.length);
}

function populateAccountSelects() {
  const options = state.accounts
    .map((account) => `<option value="${account.id}">#${account.id} (${account.currency})</option>`)
    .join("");

  [els.accountSelectTransferFrom, els.accountSelectTransferTo, els.accountSelectDeposit, els.accountSelectLedger].forEach((select) => {
    if (!select) return;
    select.innerHTML = options || `<option value="">No accounts</option>`;
  });

  if (state.accounts.length) {
    els.accountSelectTransferTo.value = String(state.accounts[state.accounts.length - 1].id);
  }
}

async function loadAccounts() {
  state.accounts = await apiRequest("/accounts");
  state.balances = {};

  const balances = await Promise.all(
    state.accounts.map(async (account) => {
      const result = await apiRequest(`/accounts/${account.id}/balance`);
      return [account.id, Number(result.balance || 0)];
    })
  );

  balances.forEach(([accountId, amount]) => {
    state.balances[accountId] = amount;
  });

  state.totalBalance = Object.values(state.balances).reduce((sum, amount) => sum + amount, 0);
}

async function resolveCustomerProfile() {
  const session = getSession();
  let customerId = session?.customerId || null;

  if (!customerId && state.accounts.length) {
    customerId = state.accounts[0].customer_id;
  }

  if (!customerId) {
    state.customer = null;
    els.kycPanel.classList.remove("hidden");
    return;
  }

  try {
    state.customer = await apiRequest(`/customers/${customerId}`);
    saveSession({ ...session, customerId: state.customer.id });
    els.kycPanel.classList.add("hidden");
  } catch {
    state.customer = null;
    els.kycPanel.classList.remove("hidden");
  }
}

async function loadTransfers() {
  state.transfers = await apiRequest("/transfers");
}

async function loadLedger(accountId) {
  if (!accountId) {
    state.ledgerEntries = [];
    return;
  }
  state.ledgerEntries = await apiRequest(`/ledger/accounts/${accountId}/entries`);
}

async function refreshDashboard() {
  await loadAccounts();
  await resolveCustomerProfile();
  await loadTransfers();
  await loadLedger(state.accounts[0]?.id);
  populateAccountSelects();
  renderTopBar();
  renderAccounts();
  renderTransfers();
  renderLedgerEntries();
  renderProfile();
}

function initNavigation() {
  els.nav?.querySelectorAll("[data-view]").forEach((link) => {
    link.addEventListener("click", () => {
      const key = link.dataset.view;
      activateNav("#customer-nav", key);
      switchView("#customer-views", `view-${key}`);
    });
  });
}

function bindForms() {
  els.logoutBtn?.addEventListener("click", logout);

  els.createAccountForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    if (!state.customer?.id) {
      showAlert(els.alert, "error", "Complete KYC first before creating an account.");
      return;
    }

    try {
      await apiRequest("/accounts", {
        method: "POST",
        body: {
          customer_id: state.customer.id,
          currency: els.createAccountForm.currency.value,
        },
      });
      showAlert(els.alert, "success", "Account created successfully.");
      await refreshDashboard();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.depositForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const accountId = Number(els.depositForm.account_id.value);
    const amount = Number(els.depositForm.amount.value);
    const reference = els.depositForm.reference_id.value.trim();

    if (!accountId || !amount || !reference) {
      showAlert(els.alert, "error", "Deposit form is incomplete.");
      return;
    }

    try {
      await apiRequest(`/accounts/${accountId}/deposit`, {
        method: "POST",
        body: { amount, reference_id: reference },
      });
      showAlert(els.alert, "success", "Deposit posted to ledger.");
      await refreshDashboard();
      els.accountSelectLedger.value = String(accountId);
      await loadLedger(accountId);
      renderLedgerEntries();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.transferForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const fromAccount = Number(els.transferForm.from_account.value);
    const toAccount = Number(els.transferForm.to_account.value);
    const amount = Number(els.transferForm.amount.value);

    if (!fromAccount || !toAccount || !amount) {
      showAlert(els.alert, "error", "Transfer form is incomplete.");
      return;
    }
    if (fromAccount === toAccount) {
      showAlert(els.alert, "error", "Source and destination accounts must be different.");
      return;
    }

    try {
      await apiRequest("/transfers/initiate", {
        method: "POST",
        body: {
          from_account: fromAccount,
          to_account: toAccount,
          amount,
        },
      });
      showAlert(els.alert, "success", "Transfer initiated with PENDING status.");
      await refreshDashboard();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.transfersTableBody?.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    if (!target.classList.contains("execute-transfer-btn")) return;

    const transferId = Number(target.dataset.transferId);
    if (!transferId) return;

    clearAlert(els.alert);
    target.setAttribute("disabled", "true");
    try {
      await apiRequest(`/transfers/${transferId}/execute`, { method: "POST" });
      showAlert(els.alert, "success", `Transfer #${transferId} executed.`);
      await refreshDashboard();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    } finally {
      target.removeAttribute("disabled");
    }
  });

  els.accountSelectLedger?.addEventListener("change", async () => {
    const accountId = Number(els.accountSelectLedger.value);
    try {
      await loadLedger(accountId);
      renderLedgerEntries();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.kycForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const fullName = els.kycForm.kyc_full_name.value.trim();
    const documentId = els.kycForm.kyc_document_id.value.trim();

    if (!fullName || !documentId) {
      showAlert(els.alert, "error", "KYC fields are required.");
      return;
    }

    try {
      const customer = await apiRequest("/customers", {
        method: "POST",
        body: {
          user_id: state.session.user.id,
          kyc_full_name: fullName,
          kyc_document_id: documentId,
        },
      });
      const session = getSession();
      saveSession({ ...session, customerId: customer.id });
      showAlert(els.alert, "success", "KYC profile created.");
      await refreshDashboard();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });
}

async function init() {
  state.session = await requireAuth("CUSTOMER");
  if (!state.session) return;

  initNavigation();
  bindForms();

  try {
    await refreshDashboard();
  } catch (error) {
    showAlert(els.alert, "error", toErrorMessage(error, "Unable to load dashboard data"));
  }
}

init();
