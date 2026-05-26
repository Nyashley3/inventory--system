const stockSetButton = document.getElementById('s-set');
const lowList = document.getElementById('low-list');
const stockTableBody = document.querySelector('#stock-table tbody');
const loadStocksButton = document.getElementById('btn-load-stocks');

async function loadAlerts() {
  try {
    const alerts = await apiGet('/api/alerts');
    if (!lowList) return;
    if (!alerts.length) {
      lowList.innerHTML = '<div class="text-muted">No low stock items found.</div>';
      return;
    }
    lowList.innerHTML = alerts.map(a => `<div>${a.product_name} (Branch ${a.branch_id}): ${a.quantity} ≤ ${a.threshold}</div>`).join('');
  } catch (err) {
    showAlert(err.msg || 'Unable to load low stock alerts.', 'danger');
  }
}

async function loadStocks() {
  try {
    const branch = document.getElementById('filter-branch')?.value.trim();
    const product = document.getElementById('filter-product')?.value.trim();
    let url = '/api/stocks';
    const params = [];
    if (branch) params.push('branch_id=' + encodeURIComponent(branch));
    if (product) params.push('product_id=' + encodeURIComponent(product));
    if (params.length) url += '?' + params.join('&');
    const stocks = await apiGet(url);
    if (!stockTableBody) return;
    stockTableBody.innerHTML = '';
    stocks.forEach(s => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${s.branch_id}</td>
        <td>${s.product_name}</td>
        <td>${s.barcode}</td>
        <td>${s.quantity}</td>
        <td>${s.threshold}</td>
        <td>${s.location || '<span class="text-muted">Not set</span>'}</td>
      `;
      stockTableBody.appendChild(row);
    });
  } catch (err) {
    showAlert(err.msg || 'Unable to load stock details.', 'danger');
  }
}

if (stockSetButton) {
  stockSetButton.addEventListener('click', async () => {
    const branch = document.getElementById('s-branch')?.value.trim();
    const product = document.getElementById('s-product')?.value.trim();
    const location = document.getElementById('s-location')?.value.trim();
    const qty = document.getElementById('s-qty')?.value.trim();
    const th = document.getElementById('s-th')?.value.trim();
    if (!branch || !product) {
      showAlert('Branch ID and product ID are required.', 'warning');
      return;
    }
    try {
      await apiPost('/api/stocks', {branch_id: branch, product_id: product, quantity: qty, threshold: th, location});
      showAlert('Stock updated successfully.', 'success');
      loadAlerts();
      loadStocks();
    } catch (err) {
      showAlert(err.msg || 'Could not update stock.', 'danger');
    }
  });
}

if (loadStocksButton) {
  loadStocksButton.addEventListener('click', loadStocks);
}

loadStocks();
loadAlerts();
