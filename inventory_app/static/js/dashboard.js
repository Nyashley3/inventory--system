const dashboardAlerts = document.getElementById('alerts');
const dashboardSaleResult = document.getElementById('sale-result');
const dashboardSaleButton = document.getElementById('btn-sale');

async function loadAlerts() {
  try {
    const j = await apiGet('/api/alerts');
    if (Array.isArray(j) && j.length) {
      dashboardAlerts.innerHTML = `<div class="alert alert-warning">Low stock: ${j.map(a => `${a.product_name} (b${a.branch_id}: ${a.quantity})`).join(', ')}</div>`;
    } else {
      dashboardAlerts.innerHTML = '<div class="text-muted">No low stock alerts.</div>';
    }
  } catch (err) {
    showAlert(err.msg || 'Could not load stock alerts.', 'danger');
  }
}

if (dashboardSaleButton) {
  dashboardSaleButton.addEventListener('click', async () => {
    const branch = document.getElementById('sale-branch')?.value.trim();
    const pid = document.getElementById('sale-product')?.value.trim();
    const qty = document.getElementById('sale-qty')?.value.trim();
    if (!branch || !pid || !qty) {
      showAlert('Please provide branch ID, product ID, and quantity to record the sale.', 'warning');
      return;
    }

    try {
      const j = await apiPost('/api/sales', {branch_id: branch, items:[{product_id: pid, quantity: qty}]});
      if (dashboardSaleResult) dashboardSaleResult.innerText = JSON.stringify(j, null, 2);
      showAlert('Sale recorded successfully.', 'success');
      loadAlerts();
    } catch (err) {
      showAlert(err.msg || 'Unable to record sale. Please check the branch and product IDs.', 'danger');
    }
  });
}

loadAlerts();
