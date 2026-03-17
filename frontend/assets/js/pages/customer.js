import { apiRequest } from "../core/api.js";
import { requireAuth, logout } from "../core/auth.js";
import { getSession, saveSession } from "../core/storage.js";
import {
  activateNav,
  clearAlert,
  formatCurrency,
  formatDate,
  formatPercent,
  showAlert,
  switchView,
  toErrorMessage,
} from "../core/ui.js";

const state = {
  session: null,
  profile: null,
  accounts: [],
  balances: {},
  balancesByCurrency: {},
  transfers: [],
  ledgerEntries: [],
  timeDeposits: [],
  loans: [],
  cards: [],
};

const els = {
  alert: document.getElementById("customer-alert"),
  nav: document.getElementById("customer-nav"),
  views: document.querySelector("#customer-views"),
  welcomeName: document.getElementById("welcome-name"),
  welcomeSub: document.getElementById("welcome-sub"),
  balanceGrid: document.getElementById("balance-grid"),
  kpiAccounts: document.getElementById("kpi-accounts-count"),
  kpiTransfers: document.getElementById("kpi-transfers-count"),
  accountsTableBody: document.getElementById("accounts-table-body"),
  transfersTableBody: document.getElementById("transfers-table-body"),
  ledgerTableBody: document.getElementById("ledger-table-body"),
  profileCard: document.getElementById("profile-card"),
  timeDepositsTableBody: document.getElementById("time-deposits-table-body"),
  loansTableBody: document.getElementById("loans-table-body"),
  cardsTableBody: document.getElementById("cards-table-body"),
  accountSelectTransferFrom: document.getElementById("transfer-from-account"),
  accountSelectTransferTo: document.getElementById("transfer-to-account"),
  accountSelectDeposit: document.getElementById("deposit-account"),
  accountSelectWithdraw: document.getElementById("withdraw-account"),
  accountSelectLedger: document.getElementById("ledger-account"),
  timeDepositAccountSelect: document.getElementById("time-deposit-account"),
  loanAccountSelect: document.getElementById("loan-account"),
  loanCurrencyInput: document.getElementById("loan-currency"),
  cardAccountSelect: document.getElementById("card-account"),
  createAccountForm: document.getElementById("create-account-form"),
  transferForm: document.getElementById("transfer-form"),
  depositForm: document.getElementById("deposit-form"),
  withdrawForm: document.getElementById("withdraw-form"),
  timeDepositForm: document.getElementById("time-deposit-form"),
  loanForm: document.getElementById("loan-form"),
  kycForm: document.getElementById("kyc-form"),
  kycPanel: document.getElementById("kyc-panel"),
  profileForm: document.getElementById("profile-form"),
  passwordForm: document.getElementById("password-form"),
  createCardForm: document.getElementById("create-card-form"),
  logoutBtn: document.getElementById("logout-btn"),
};

function getAccountById(accountId) {
  return state.accounts.find((account) => account.id === accountId);
}

function renderBalanceGrid() {
  if (!els.balanceGrid) return;
  const entries = Object.entries(state.balancesByCurrency);
  if (!entries.length) {
    els.balanceGrid.innerHTML = `<article class="kpi"><p class="label">Balances</p><p class="value">No balances yet</p></article>`;
    return;
  }

  els.balanceGrid.innerHTML = entries
    .map(
      ([currency, amount]) => `
      <article class="kpi">
        <p class="label">${currency} balance</p>
        <p class="value">${formatCurrency(amount, currency)}</p>
      </article>
    `
    )
    .join("");
}

function renderAccounts() {
  if (!state.accounts.length) {
    els.accountsTableBody.innerHTML = `<tr><td colspan="7">No accounts yet. Create your first account.</td></tr>`;
    return;
  }

  els.accountsTableBody.innerHTML = state.accounts
    .map((account) => {
      const balance = state.balances[account.id] ?? 0;
      const canDelete = balance === 0;
      const deleteDisabled = canDelete ? "" : "disabled";
      const deleteTitle = canDelete ? "" : 'title="Balance must be 0 to delete"';
      return `
        <tr>
          <td>#${account.id}</td>
          <td>${account.iban || "-"}</td>
          <td>${account.currency}</td>
          <td>${formatCurrency(balance, account.currency)}</td>
          <td>${formatDate(account.created_at)}</td>
          <td><span class="pill success">ACTIVE</span></td>
          <td>
            <button class="button button-ghost delete-account-btn" data-account-id="${account.id}" ${deleteDisabled} ${deleteTitle}>
              Delete
            </button>
          </td>
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
    .map((transfer) => {
      const currency = getAccountById(transfer.from_account)?.currency || "USD";
      const statusClass =
        transfer.status === "COMPLETED" ? "success" : transfer.status === "FAILED" ? "danger" : "pending";
      return `
      <tr>
        <td>#${transfer.id}</td>
        <td>${transfer.from_account}</td>
        <td>${transfer.to_account}</td>
        <td>${formatCurrency(transfer.amount, currency)}</td>
        <td><span class="pill ${statusClass}">${transfer.status}</span></td>
        <td>${formatDate(transfer.created_at)}</td>
        <td>
          ${
            transfer.status === "PENDING"
              ? `<button class="button button-ghost execute-transfer-btn" data-transfer-id="${transfer.id}">Execute</button>`
              : `<span class="inline-muted">-</span>`
          }
        </td>
      </tr>
    `;
    })
    .join("");
}

function renderLedgerEntries() {
  if (!state.ledgerEntries.length) {
    els.ledgerTableBody.innerHTML = `<tr><td colspan="5">No ledger entries for this account.</td></tr>`;
    return;
  }

  const selectedAccountId = Number(els.accountSelectLedger?.value);
  const currency = getAccountById(selectedAccountId)?.currency || "USD";

  els.ledgerTableBody.innerHTML = state.ledgerEntries
    .map(
      (entry) => `
      <tr>
        <td>#${entry.id}</td>
        <td>${entry.type}</td>
        <td>${formatCurrency(entry.amount, currency)}</td>
        <td>${entry.reference_id}</td>
        <td>${formatDate(entry.created_at)}</td>
      </tr>
    `
    )
    .join("");
}

function renderProfile() {
  const profile = state.profile;
  if (!profile) return;

  const statusClass =
    profile.status === "VERIFIED" ? "success" : profile.status === "SUSPENDED" ? "danger" : "pending";
  const statusBadge = profile.status
    ? `<span class="pill ${statusClass}">${profile.status}</span>`
    : `<span class="inline-muted">Not created</span>`;

  els.profileCard.innerHTML = `
    <div class="form-row-2">
      <div class="card">
        <span class="feature-tag">Identity</span>
        <p><strong>User ID:</strong> ${profile.user_id}</p>
        <p><strong>Email:</strong> ${profile.email}</p>
        <p><strong>Role:</strong> ${state.session.user.role}</p>
        <p><strong>Phone:</strong> ${profile.phone ?? "-"}</p>
      </div>
      <div class="card">
        <span class="feature-tag">KYC Profile</span>
        <p><strong>Customer ID:</strong> ${profile.customer_id ?? "Not created"}</p>
        <p><strong>Full Name:</strong> ${profile.full_name ?? "-"}</p>
        <p><strong>Document ID:</strong> ${profile.document_id ?? "-"}</p>
        <p><strong>Status:</strong> ${statusBadge}</p>
        <p><strong>Address:</strong> ${profile.address ?? "-"}</p>
      </div>
    </div>
  `;
}

function populateProfileForm() {
  if (!els.profileForm || !state.profile) return;
  els.profileForm.email.value = state.profile.email || "";
  els.profileForm.phone.value = state.profile.phone || "";
  els.profileForm.address.value = state.profile.address || "";
  els.profileForm.city.value = state.profile.city || "";
  els.profileForm.country.value = state.profile.country || "";
}

function renderTimeDeposits() {
  if (!els.timeDepositsTableBody) return;
  if (!state.timeDeposits.length) {
    els.timeDepositsTableBody.innerHTML = `<tr><td colspan="9">No time deposits yet.</td></tr>`;
    return;
  }

  els.timeDepositsTableBody.innerHTML = state.timeDeposits
    .map((dep) => {
      const canClaim = dep.matured && dep.status !== "COMPLETED";
      const statusClass = dep.status === "COMPLETED" ? "success" : "pending";
      return `
      <tr>
        <td>#${dep.id}</td>
        <td>${dep.account_id}</td>
        <td>${formatCurrency(dep.principal, dep.currency)}</td>
        <td>${dep.annual_rate}%</td>
        <td>${dep.duration_months} months</td>
        <td>${formatDate(dep.maturity_date)}</td>
        <td><span class="pill ${statusClass}">${dep.status}</span></td>
        <td>${formatCurrency(dep.expected_return, dep.currency)}</td>
        <td>
          ${
            canClaim
              ? `<button class="button button-ghost claim-deposit-btn" data-deposit-id="${dep.id}">Claim</button>`
              : `<span class="inline-muted">-</span>`
          }
        </td>
      </tr>
    `;
    })
    .join("");
}

function renderLoans() {
  if (!els.loansTableBody) return;
  if (!state.loans.length) {
    els.loansTableBody.innerHTML = `<tr><td colspan="8">No loan requests yet.</td></tr>`;
    return;
  }

  els.loansTableBody.innerHTML = state.loans
    .map((loan) => {
      const statusClass = loan.status === "APPROVED" ? "success" : loan.status === "REJECTED" ? "danger" : "pending";
      const repayment =
        loan.status === "APPROVED" ? "Repayment schedule to be issued" : "Pending approval";
      return `
      <tr>
        <td>#${loan.id}</td>
        <td>${loan.account_id ?? "-"}</td>
        <td>${formatCurrency(loan.amount, loan.currency)}</td>
        <td>${loan.currency}</td>
        <td><span class="pill ${statusClass}">${loan.status}</span></td>
        <td>${loan.purpose}</td>
        <td>${repayment}</td>
        <td>${formatDate(loan.created_at)}</td>
      </tr>
    `;
    })
    .join("");
}

function renderCards() {
  if (!els.cardsTableBody) return;
  if (!state.cards.length) {
    els.cardsTableBody.innerHTML = `<tr><td colspan="6">No cards yet.</td></tr>`;
    return;
  }

  els.cardsTableBody.innerHTML = state.cards
    .map((card) => {
      const statusClass = card.status === "ACTIVE" ? "success" : "danger";
      const nextStatus = card.status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
      return `
      <tr>
        <td>#${card.id}</td>
        <td>${card.account_id}</td>
        <td>${card.card_number}</td>
        <td>${card.expiry_month}/${card.expiry_year}</td>
        <td><span class="pill ${statusClass}">${card.status}</span></td>
        <td>
          <button class="button button-ghost toggle-card-btn" data-card-id="${card.id}" data-next-status="${nextStatus}">
            Set ${nextStatus}
          </button>
          <button class="button button-ghost delete-card-btn" data-card-id="${card.id}">
            Delete
          </button>
        </td>
      </tr>
    `;
    })
    .join("");
}

function renderTopBar() {
  const customerName = state.profile?.full_name || state.session.user.email;
  els.welcomeName.textContent = `Welcome back, ${customerName}`;
  els.welcomeSub.textContent = `Role: ${state.session.user.role} | Last sync: ${new Date().toLocaleTimeString()}`;
  els.kpiAccounts.textContent = String(state.accounts.length);
  els.kpiTransfers.textContent = String(state.transfers.length);
}

function populateAccountSelects() {
  const options = state.accounts
    .map((account) => `<option value="${account.id}">#${account.id} (${account.currency})</option>`)
    .join("");

  [
    els.accountSelectTransferFrom,
    els.accountSelectTransferTo,
    els.accountSelectDeposit,
    els.accountSelectWithdraw,
    els.accountSelectLedger,
    els.timeDepositAccountSelect,
    els.loanAccountSelect,
    els.cardAccountSelect,
  ].forEach((select) => {
    if (!select) return;
    select.innerHTML = options || `<option value="">No accounts</option>`;
  });

  if (state.accounts.length && els.accountSelectTransferTo) {
    els.accountSelectTransferTo.value = String(state.accounts[state.accounts.length - 1].id);
  }

  syncLoanCurrency();
}

function syncLoanCurrency() {
  if (!els.loanAccountSelect || !els.loanCurrencyInput) return;
  const accountId = Number(els.loanAccountSelect.value);
  const account = getAccountById(accountId);
  els.loanCurrencyInput.value = account?.currency || "";
}

async function loadAccounts() {
  state.accounts = await apiRequest("/accounts");
  state.balances = {};
  state.balancesByCurrency = {};

  const balances = await Promise.all(
    state.accounts.map(async (account) => {
      const result = await apiRequest(`/accounts/${account.id}/balance`);
      return [account.id, Number(result.balance || 0)];
    })
  );

  balances.forEach(([accountId, amount]) => {
    state.balances[accountId] = amount;
    const account = getAccountById(accountId);
    if (account) {
      state.balancesByCurrency[account.currency] =
        (state.balancesByCurrency[account.currency] || 0) + amount;
    }
  });
}

async function loadProfile() {
  state.profile = await apiRequest("/profile");
  if (state.profile?.customer_id) {
    const session = getSession();
    saveSession({ ...session, customerId: state.profile.customer_id });
    els.kycPanel.classList.add("hidden");
  } else {
    els.kycPanel.classList.remove("hidden");
  }
  populateProfileForm();
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

async function loadTimeDeposits() {
  state.timeDeposits = await apiRequest("/time-deposits");
}

async function loadLoans() {
  state.loans = await apiRequest("/loans");
}

async function loadCards() {
  state.cards = await apiRequest("/cards");
}

async function safeLoad(loader, onErrorMessage, fallback) {
  try {
    await loader();
  } catch (error) {
    if (fallback) fallback();
    if (onErrorMessage) {
      showAlert(els.alert, "error", onErrorMessage);
    }
  }
}

async function refreshDashboard() {
  await loadAccounts();
  await loadProfile();
  await Promise.all([
    safeLoad(loadTransfers),
    safeLoad(loadTimeDeposits),
    safeLoad(loadLoans),
    safeLoad(loadCards),
  ]);
  await loadLedger(state.accounts[0]?.id);
  populateAccountSelects();
  renderTopBar();
  renderBalanceGrid();
  renderAccounts();
  renderTransfers();
  renderLedgerEntries();
  renderProfile();
  renderTimeDeposits();
  renderLoans();
  renderCards();
}

function initNavigation() {
  if (!els.nav) return;
  els.nav.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const link = target.closest("[data-view]");
    if (!link) return;
    event.preventDefault();
    const key = link.dataset.view;
    if (!key) return;
    activateNav("#customer-nav", key);
    switchView("#customer-views", `view-${key}`);
  });
}

function bindForms() {
  els.logoutBtn?.addEventListener("click", logout);

  els.createAccountForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    if (!state.profile?.customer_id) {
      showAlert(els.alert, "error", "Complete KYC first before creating an account.");
      return;
    }

    try {
      await apiRequest("/accounts", {
        method: "POST",
        body: {
          customer_id: state.profile.customer_id,
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

  els.withdrawForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const accountId = Number(els.withdrawForm.account_id.value);
    const amount = Number(els.withdrawForm.amount.value);
    const reference = els.withdrawForm.reference_id.value.trim();

    if (!accountId || !amount || !reference) {
      showAlert(els.alert, "error", "Withdraw form is incomplete.");
      return;
    }

    try {
      await apiRequest(`/accounts/${accountId}/withdraw`, {
        method: "POST",
        body: { amount, reference_id: reference },
      });
      showAlert(els.alert, "success", "Withdrawal posted to ledger.");
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

  els.accountsTableBody?.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    if (!target.classList.contains("delete-account-btn")) return;

    const accountId = Number(target.dataset.accountId);
    if (!accountId) return;

    const confirmDelete = window.confirm(
      `Delete account #${accountId}? This is only allowed if the account has no ledger history or linked items.`
    );
    if (!confirmDelete) return;

    clearAlert(els.alert);
    target.setAttribute("disabled", "true");
    try {
      await apiRequest(`/accounts/${accountId}`, { method: "DELETE" });
      showAlert(els.alert, "success", `Account #${accountId} deleted.`);
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

  els.timeDepositForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const accountId = Number(els.timeDepositForm.account_id.value);
    const amount = Number(els.timeDepositForm.amount.value);
    const annualRate = Number(els.timeDepositForm.annual_rate.value);
    const durationMonths = Number(els.timeDepositForm.duration_months.value);

    if (!accountId || !amount || !annualRate || !durationMonths) {
      showAlert(els.alert, "error", "Time deposit form is incomplete.");
      return;
    }

    try {
      await apiRequest("/time-deposits", {
        method: "POST",
        body: {
          account_id: accountId,
          amount,
          annual_rate: annualRate,
          duration_months: durationMonths,
        },
      });
      showAlert(els.alert, "success", "Time deposit opened.");
      els.timeDepositForm.reset();
      await refreshDashboard();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.timeDepositsTableBody?.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    if (!target.classList.contains("claim-deposit-btn")) return;

    const depositId = Number(target.dataset.depositId);
    if (!depositId) return;

    clearAlert(els.alert);
    target.setAttribute("disabled", "true");
    try {
      await apiRequest(`/time-deposits/${depositId}/claim`, { method: "POST" });
      showAlert(els.alert, "success", `Time deposit #${depositId} claimed.`);
      await refreshDashboard();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    } finally {
      target.removeAttribute("disabled");
    }
  });

  els.loanForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const accountId = Number(els.loanForm.account_id.value);
    const amount = Number(els.loanForm.amount.value);
    const purpose = els.loanForm.purpose.value.trim();
    const currency = els.loanForm.currency.value.trim();

    if (!accountId || !amount || !purpose || !currency) {
      showAlert(els.alert, "error", "Loan form is incomplete.");
      return;
    }

    try {
      await apiRequest("/loans", {
        method: "POST",
        body: { account_id: accountId, amount, currency, purpose },
      });
      showAlert(els.alert, "success", "Loan request submitted.");
      els.loanForm.reset();
      syncLoanCurrency();
      await refreshDashboard();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.loanAccountSelect?.addEventListener("change", syncLoanCurrency);

  els.profileForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const payload = {};
    const email = els.profileForm.email.value.trim();
    const phone = els.profileForm.phone.value.trim();
    const address = els.profileForm.address.value.trim();
    const city = els.profileForm.city.value.trim();
    const country = els.profileForm.country.value.trim();

    if (email) payload.email = email;
    if (phone) payload.phone = phone;
    if (address) payload.address = address;
    if (city) payload.city = city;
    if (country) payload.country = country;

    if (!Object.keys(payload).length) {
      showAlert(els.alert, "error", "Add at least one field to update.");
      return;
    }

    try {
      await apiRequest("/profile", { method: "PUT", body: payload });
      showAlert(els.alert, "success", "Profile updated.");
      await refreshDashboard();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.passwordForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const currentPassword = els.passwordForm.current_password.value;
    const newPassword = els.passwordForm.new_password.value;

    if (!currentPassword || !newPassword) {
      showAlert(els.alert, "error", "Password form is incomplete.");
      return;
    }

    try {
      await apiRequest("/profile/password", {
        method: "POST",
        body: { current_password: currentPassword, new_password: newPassword },
      });
      showAlert(els.alert, "success", "Password updated.");
      els.passwordForm.reset();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.createCardForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAlert(els.alert);

    const accountId = Number(els.createCardForm.account_id.value);
    if (!accountId) {
      showAlert(els.alert, "error", "Select an account for the card.");
      return;
    }

    try {
      await apiRequest("/cards", { method: "POST", body: { account_id: accountId } });
      showAlert(els.alert, "success", "Card created.");
      await refreshDashboard();
    } catch (error) {
      showAlert(els.alert, "error", toErrorMessage(error));
    }
  });

  els.cardsTableBody?.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const cardId = Number(target.dataset.cardId);

    if (target.classList.contains("toggle-card-btn")) {
      const nextStatus = target.dataset.nextStatus;
      if (!cardId || !nextStatus) return;

      clearAlert(els.alert);
      target.setAttribute("disabled", "true");
      try {
        await apiRequest(`/cards/${cardId}/status`, { method: "POST", body: { status: nextStatus } });
        showAlert(els.alert, "success", `Card #${cardId} set to ${nextStatus}.`);
        await refreshDashboard();
      } catch (error) {
        showAlert(els.alert, "error", toErrorMessage(error));
      } finally {
        target.removeAttribute("disabled");
      }
    }

    if (target.classList.contains("delete-card-btn")) {
      if (!cardId) return;
      const confirmDelete = window.confirm(`Delete card #${cardId}? This cannot be undone.`);
      if (!confirmDelete) return;

      clearAlert(els.alert);
      target.setAttribute("disabled", "true");
      try {
        await apiRequest(`/cards/${cardId}`, { method: "DELETE" });
        showAlert(els.alert, "success", `Card #${cardId} deleted.`);
        await refreshDashboard();
      } catch (error) {
        showAlert(els.alert, "error", toErrorMessage(error));
      } finally {
        target.removeAttribute("disabled");
      }
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
