const stockSetButton = document.getElementById('s-set');
const lowList = document.getElementById('low-list');

async function loadAlerts() {
  try {
    const alerts = await apiGet('/api/alerts');
    if (!lowList) return;
    lowList.innerHTML = alerts.map(a => `<div>${a.product_name} (b${a.branch_id}): ${a.quantity} <= ${a.threshold}</div>`).join('');
  } catch (err) {
    showAlert(err.msg || 'Unable to load low stock alerts.', 'danger');
  }
}

if (stockSetButton) {
  stockSetButton.addEventListener('click', async () => {
    const branch = document.getElementById('s-branch')?.value.trim();
    const product = document.getElementById('s-product')?.value.trim();
    const qty = document.getElementById('s-qty')?.value.trim();
    const th = document.getElementById('s-th')?.value.trim();
    if (!branch || !product) {
      showAlert('Branch ID and product ID are required.', 'warning');
      return;
    }
    try {
      await apiPost('/api/stocks', {branch_id: branch, product_id: product, quantity: qty, threshold: th});
      showAlert('Stock updated successfully.', 'success');
      loadAlerts();
    } catch (err) {
      showAlert(err.msg || 'Could not update stock.', 'danger');
    }
  });
}

loadAlerts();
