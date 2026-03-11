export function renderStockTable({ rows, market, currency, emptyMessage = "No stocks found." }) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return `<tr><td colspan=\"5\">${emptyMessage}</td></tr>`;
  }

  return rows
    .map((row) => {
      const changeClass = row.change_percent > 0 ? "pnl-positive" : row.change_percent < 0 ? "pnl-negative" : "";
      return `
        <tr>
          <td>${row.symbol}</td>
          <td>${row.name}</td>
          <td>${currency} ${Number(row.price).toFixed(2)}</td>
          <td class="${changeClass}">${Number(row.change_percent).toFixed(2)}%</td>
          <td>
            <button class="button button-ghost select-stock" type="button" data-symbol="${row.symbol}" data-market="${market}">Select</button>
          </td>
        </tr>
      `;
    })
    .join("");
}
