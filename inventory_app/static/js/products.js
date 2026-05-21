const createProductButton = document.getElementById('p-create');
const productAdminActions = document.getElementById('product-admin-actions');
let PRODUCTS_ROLE = 'manager';

async function loadProducts() {
  try {
    const products = await apiGet('/api/products');
    const tbody = document.querySelector('#products-table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    products.forEach(p => {
      const tr = document.createElement('tr');
      const actions = PRODUCTS_ROLE === 'cashier'
        ? ''
        : `<button class='btn btn-sm btn-danger product-delete' data-id='${p.id}'>Delete</button>`;
      tr.innerHTML = `<td>${p.id}</td><td>${p.name}</td><td>${p.barcode}</td><td>${p.price.toFixed(2)}</td><td>${p.currency || 'USD'}</td><td>${actions}</td>`;
      tbody.appendChild(tr);
    });

    if (PRODUCTS_ROLE !== 'cashier') {
      document.querySelectorAll('.product-delete').forEach(button => {
        button.addEventListener('click', async () => {
          try {
            await apiDelete('/api/products/' + button.dataset.id);
            showAlert('Product deleted successfully.', 'success');
            loadProducts();
          } catch (err) {
            showAlert(err.msg || 'Could not delete product.', 'danger');
          }
        });
      });
    }
  } catch (err) {
    showAlert(err.msg || 'Unable to load products.', 'danger');
  }
}

if (createProductButton) {
  createProductButton.addEventListener('click', async () => {
    const name = document.getElementById('p-name')?.value.trim();
    const barcode = document.getElementById('p-barcode')?.value.trim();
    const price = parseFloat(document.getElementById('p-price')?.value || '0');
    const currency = document.getElementById('p-currency')?.value;

    if (!name) {
      showAlert('Product name cannot be empty.', 'warning');
      return;
    }
    if (!barcode) {
      showAlert('Barcode is required to save a product.', 'warning');
      return;
    }

    try {
      const result = await apiPost('/api/products', {name, barcode, price, currency});
      showAlert(`Product "${result.name}" created successfully.`, 'success');
      document.getElementById('p-name').value = '';
      document.getElementById('p-barcode').value = '';
      document.getElementById('p-price').value = '';
      document.getElementById('p-currency').value = 'USD';
      loadProducts();
    } catch (err) {
      showAlert(err.msg || 'Could not create product. Please check the inputs.', 'danger');
    }
  });
}

(async function initProductsPage() {
  try {
    const token = localStorage.getItem('token');
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1] || '{}'));
      PRODUCTS_ROLE = payload.role || PRODUCTS_ROLE;
      if (PRODUCTS_ROLE === 'cashier') {
        productAdminActions?.classList.add('d-none');
        document.getElementById('products-alert').innerHTML = '<div class="alert alert-info">Cashiers can view product details here, but only managers and supervisors can create or delete products.</div>';
      }
    }
  } catch (e) {
    console.warn('Unable to determine user role for products page', e);
  }
  loadProducts();
})();
