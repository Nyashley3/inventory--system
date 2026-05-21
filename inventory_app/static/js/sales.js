const salesProductsTable = document.querySelector('#sales-products-table tbody');
const salesBranchInput = document.getElementById('sale-branch');
const salesProductInput = document.getElementById('sale-product');
const salesQtyInput = document.getElementById('sale-qty');
const salesFilterBranch = document.getElementById('sale-filter-branch');
const salesResult = document.getElementById('sale-result');
const salesLoadButton = document.getElementById('btn-load-products');
const salesStartButton = document.getElementById('btn-start');
const salesStopButton = document.getElementById('btn-stop');
const recordSaleButton = document.getElementById('btn-sale');

async function loadSaleProducts() {
  try {
    const branch = salesFilterBranch?.value.trim();
    const url = branch ? '/api/products?branch_id=' + encodeURIComponent(branch) : '/api/products';
    const items = await apiGet(url);
    if (!salesProductsTable) return;
    salesProductsTable.innerHTML = '';

    items.forEach(p => {
      const stock = typeof p.stock !== 'undefined' ? p.stock : '-';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${p.id}</td>
        <td>${p.name}</td>
        <td>${p.price.toFixed(2)}</td>
        <td>${stock}</td>
        <td><button class='btn btn-sm btn-outline-primary select-product' data-id='${p.id}'>Select</button></td>
      `;
      salesProductsTable.appendChild(tr);
    });

    document.querySelectorAll('.select-product').forEach(btn => {
      btn.addEventListener('click', () => {
        if (salesProductInput) salesProductInput.value = btn.dataset.id;
        showAlert('Product ID ' + btn.dataset.id + ' selected. Enter quantity and record sale.', 'info', 4000);
      });
    });
  } catch (err) {
    showAlert(err.msg || 'Unable to load products for sale.', 'danger');
  }
}

if (salesLoadButton) {
  salesLoadButton.addEventListener('click', loadSaleProducts);
}

if (salesBranchInput) {
  salesBranchInput.addEventListener('change', () => {
    if (salesFilterBranch) salesFilterBranch.value = salesBranchInput.value.trim();
  });
}

if (recordSaleButton) {
  recordSaleButton.addEventListener('click', async () => {
    const branch = salesBranchInput?.value.trim();
    const pid = salesProductInput?.value.trim();
    const qty = salesQtyInput?.value.trim();
    if (!branch || !pid || !qty) {
      showAlert('Branch ID, product ID, and quantity are all required.', 'warning');
      return;
    }

    try {
      const response = await apiPost('/api/sales', {branch_id: branch, items:[{product_id: pid, quantity: qty}]});
      if (salesResult) salesResult.innerText = JSON.stringify(response, null, 2);
      showAlert('Sale recorded successfully.', 'success');
      loadSaleProducts();
    } catch (err) {
      showAlert(err.msg || 'Could not record sale.', 'danger');
    }
  });
}

loadSaleProducts();
