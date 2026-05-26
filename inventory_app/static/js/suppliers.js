const suppliersTableBody = document.querySelector('#suppliers-table tbody');
const ordersTableBody = document.querySelector('#orders-table tbody');
const createSupplierButton = document.getElementById('create-supplier');
const addOrderItemButton = document.getElementById('add-order-item');
const createOrderButton = document.getElementById('create-order');
const orderItemsContainer = document.getElementById('order-items');

function createOrderItemRow(item = {}) {
  const index = orderItemsContainer.children.length;
  const wrapper = document.createElement('div');
  wrapper.className = 'row g-2 align-items-end mb-2 order-item-row';
  wrapper.innerHTML = `
    <div class="col-4"><input class="form-control order-product" placeholder="Product ID" value="${item.product_id || ''}"></div>
    <div class="col-3"><input class="form-control order-qty" placeholder="Quantity" type="number" min="1" value="${item.quantity || 1}"></div>
    <div class="col-3"><input class="form-control order-price" placeholder="Unit Price" type="number" step="0.01" min="0" value="${item.price || 0.00}"></div>
    <div class="col-2"><button type="button" class="btn btn-outline-danger btn-sm remove-order-item">Remove</button></div>
  `;
  orderItemsContainer.appendChild(wrapper);
  wrapper.querySelector('.remove-order-item')?.addEventListener('click', () => {
    wrapper.remove();
  });
}

async function loadSuppliers() {
  try {
    const suppliers = await apiGet('/api/suppliers');
    if (!suppliersTableBody) return;
    suppliersTableBody.innerHTML = '';
    suppliers.forEach(s => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${s.name}</td>
        <td>${s.contact_name || '-'}</td>
        <td>${s.phone || '-'}</td>
        <td>${s.email || '-'}</td>
        <td><button class="btn btn-sm btn-outline-danger delete-supplier" data-id="${s.id}">Delete</button></td>
      `;
      suppliersTableBody.appendChild(row);
    });
    suppliersTableBody.querySelectorAll('.delete-supplier').forEach(button => {
      button.addEventListener('click', async () => {
        try {
          await apiDelete('/api/suppliers/' + button.dataset.id);
          showAlert('Supplier deleted successfully.', 'success');
          loadSuppliers();
          loadPurchaseOrders();
        } catch (err) {
          showAlert(err.msg || 'Unable to delete supplier.', 'danger');
        }
      });
    });
  } catch (err) {
    showAlert(err.msg || 'Unable to load suppliers.', 'danger');
  }
}

async function loadPurchaseOrders() {
  try {
    const orders = await apiGet('/api/purchase-orders');
    if (!ordersTableBody) return;
    ordersTableBody.innerHTML = '';
    orders.forEach(o => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${o.id}</td>
        <td>${o.supplier_name}</td>
        <td>${o.branch_id}</td>
        <td>${o.status}</td>
        <td>${o.expected_date || '-'}</td>
        <td>${o.status === 'pending' ? `<button class="btn btn-sm btn-success receive-order" data-id="${o.id}">Receive</button>` : '<span class="text-muted">No action</span>'}</td>
      `;
      ordersTableBody.appendChild(row);
    });
    ordersTableBody.querySelectorAll('.receive-order').forEach(button => {
      button.addEventListener('click', async () => {
        try {
          await apiPost(`/api/purchase-orders/${button.dataset.id}/receive`, {});
          showAlert('Purchase order marked as delivered and inventory updated.', 'success');
          loadPurchaseOrders();
        } catch (err) {
          showAlert(err.msg || 'Unable to receive order.', 'danger');
        }
      });
    });
  } catch (err) {
    showAlert(err.msg || 'Unable to load purchase orders.', 'danger');
  }
}

if (createSupplierButton) {
  createSupplierButton.addEventListener('click', async () => {
    const name = document.getElementById('supplier-name')?.value.trim();
    const contact = document.getElementById('supplier-contact')?.value.trim();
    const phone = document.getElementById('supplier-phone')?.value.trim();
    const email = document.getElementById('supplier-email')?.value.trim();
    const address = document.getElementById('supplier-address')?.value.trim();
    if (!name) {
      showAlert('Supplier name is required.', 'warning');
      return;
    }
    try {
      await apiPost('/api/suppliers', {name, contact_name: contact, phone, email, address});
      showAlert('Supplier created successfully.', 'success');
      document.getElementById('supplier-name').value = '';
      document.getElementById('supplier-contact').value = '';
      document.getElementById('supplier-phone').value = '';
      document.getElementById('supplier-email').value = '';
      document.getElementById('supplier-address').value = '';
      loadSuppliers();
    } catch (err) {
      showAlert(err.msg || 'Could not create supplier.', 'danger');
    }
  });
}

if (addOrderItemButton) {
  addOrderItemButton.addEventListener('click', () => createOrderItemRow());
}

if (createOrderButton) {
  createOrderButton.addEventListener('click', async () => {
    const supplierId = document.getElementById('order-supplier')?.value.trim();
    const branchId = document.getElementById('order-branch')?.value.trim();
    const expectedDate = document.getElementById('order-expected')?.value.trim();
    const itemRows = Array.from(document.querySelectorAll('.order-item-row'));
    const items = itemRows.map(row => ({
      product_id: row.querySelector('.order-product')?.value.trim(),
      quantity: row.querySelector('.order-qty')?.value.trim(),
      price: row.querySelector('.order-price')?.value.trim(),
    })).filter(item => item.product_id && item.quantity && item.price);

    if (!supplierId || !branchId || !items.length) {
      showAlert('Supplier ID, branch ID, and at least one order item are required.', 'warning');
      return;
    }
    try {
      await apiPost('/api/purchase-orders', {supplier_id: supplierId, branch_id: branchId, expected_date: expectedDate, items});
      showAlert('Purchase order created successfully.', 'success');
      document.getElementById('order-supplier').value = '';
      document.getElementById('order-branch').value = '';
      document.getElementById('order-expected').value = '';
      orderItemsContainer.innerHTML = '';
      createOrderItemRow();
      loadPurchaseOrders();
    } catch (err) {
      showAlert(err.msg || 'Could not create purchase order.', 'danger');
    }
  });
}

createOrderItemRow();
loadSuppliers();
loadPurchaseOrders();
