const checkoutSearch = document.getElementById('checkout-search');
const checkoutBranch = document.getElementById('checkout-branch');
const searchAlert = document.getElementById('search-alert');
const checkoutResult = document.getElementById('search-result');
const productDetails = document.getElementById('product-details');
const quantityInput = document.getElementById('add-quantity');
const cartTableBody = document.querySelector('#cart-table tbody');
const emptyCartMessage = document.getElementById('empty-cart-msg');
const subtotalText = document.getElementById('total-subtotal');
const totalAmountText = document.getElementById('total-amount');
const cartCountText = document.getElementById('stat-cart-count');
const cartSubtotalText = document.getElementById('stat-subtotal');

let CHECKOUT_CART = [];
let CURRENT_PRODUCT = null;

function showSearchAlert(message, type = 'danger') {
  if (!searchAlert) return;
  searchAlert.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
}

function updateCartDisplay() {
  if (!cartTableBody) return;
  cartTableBody.innerHTML = '';

  let subtotal = 0;
  CHECKOUT_CART.forEach((item, idx) => {
    const lineTotal = item.price * item.quantity;
    subtotal += lineTotal;

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${item.name}</strong></td>
      <td>$${item.price.toFixed(2)}</td>
      <td><input type="number" min="1" value="${item.quantity}" class="form-control form-control-sm cart-qty-input" data-index="${idx}"></td>
      <td>$${lineTotal.toFixed(2)}</td>
      <td><button class="btn btn-sm btn-danger remove-from-cart" data-index="${idx}">Remove</button></td>
    `;

    tr.querySelector('.cart-qty-input')?.addEventListener('change', event => {
      updateItemQuantity(idx, event.target.value);
    });
    tr.querySelector('.remove-from-cart')?.addEventListener('click', () => {
      removeFromCart(idx);
    });
    cartTableBody.appendChild(tr);
  });

  if (emptyCartMessage) {
    emptyCartMessage.style.display = CHECKOUT_CART.length === 0 ? 'block' : 'none';
  }
  if (subtotalText) subtotalText.innerText = '$' + subtotal.toFixed(2);
  if (totalAmountText) totalAmountText.innerText = '$' + subtotal.toFixed(2);
  if (cartCountText) cartCountText.innerText = CHECKOUT_CART.length.toString();
  if (cartSubtotalText) cartSubtotalText.innerText = '$' + subtotal.toFixed(2);
}

function updateItemQuantity(idx, newQty) {
  const qty = parseInt(newQty || 0, 10);
  if (qty < 1) {
    removeFromCart(idx);
    return;
  }
  CHECKOUT_CART[idx].quantity = qty;
  updateCartDisplay();
}

function removeFromCart(idx) {
  CHECKOUT_CART.splice(idx, 1);
  updateCartDisplay();
}

function clearCart() {
  if (!confirm('Clear entire cart?')) return;
  CHECKOUT_CART = [];
  updateCartDisplay();
  showAlert('Cart cleared.', 'info', 2000);
}

async function searchProduct() {
  if (!checkoutSearch) return;
  const search = checkoutSearch.value.trim();
  if (!search) {
    showSearchAlert('Please enter a barcode or product ID.', 'warning');
    return;
  }

  try {
    let product = null;
    if (/^\d+$/.test(search)) {
      const allProducts = await apiGet('/api/products');
      product = allProducts.find(p => p.id === parseInt(search, 10));
    }
    if (!product) {
      product = await apiGet('/api/products?barcode=' + encodeURIComponent(search));
    }

    if (!product || !product.id) {
      showSearchAlert('Product not found.', 'danger');
      checkoutResult?.classList.add('d-none');
      return;
    }

    CURRENT_PRODUCT = product;
    productDetails.innerHTML = `
      <strong>${product.name}</strong> (ID: ${product.id})<br>
      Barcode: ${product.barcode}<br>
      Price: ${product.currency || 'USD'} ${product.price.toFixed(2)}
    `;
    checkoutResult?.classList.remove('d-none');
    showSearchAlert('', '');
    if (quantityInput) quantityInput.value = '1';
  } catch (err) {
    showSearchAlert(err.msg || 'Search failed.', 'danger');
    checkoutResult?.classList.add('d-none');
  }
}

function addToCart() {
  if (!CURRENT_PRODUCT) return;
  const qty = parseInt(quantityInput?.value || '1', 10);
  if (qty < 1) {
    showSearchAlert('Quantity must be at least 1.', 'warning');
    return;
  }

  const existing = CHECKOUT_CART.find(item => item.product_id === CURRENT_PRODUCT.id);
  if (existing) {
    existing.quantity += qty;
  } else {
    CHECKOUT_CART.push({
      product_id: CURRENT_PRODUCT.id,
      name: CURRENT_PRODUCT.name,
      price: CURRENT_PRODUCT.price,
      quantity: qty
    });
  }

  showAlert(`Added ${qty}x ${CURRENT_PRODUCT.name} to cart.`, 'success', 3000);
  if (checkoutSearch) checkoutSearch.value = '';
  checkoutResult?.classList.add('d-none');
  CURRENT_PRODUCT = null;
  updateCartDisplay();
}

async function completeSale() {
  const branch = checkoutBranch?.value.trim();
  if (!branch) {
    showAlert('Please enter a branch ID.', 'warning');
    return;
  }
  if (CHECKOUT_CART.length === 0) {
    showAlert('Cart is empty.', 'warning');
    return;
  }

  try {
    const items = CHECKOUT_CART.map(item => ({product_id: item.product_id, quantity: item.quantity}));
    const result = await apiPost('/api/sales', {branch_id: branch, items});
    document.getElementById('sale-result')?.innerText = JSON.stringify(result, null, 2);
    showAlert('Sale completed successfully.', 'success');
    CHECKOUT_CART = [];
    updateCartDisplay();
  } catch (err) {
    showAlert(err.msg || 'Could not complete sale. Please check the branch and cart.', 'danger');
  }
}

if (document.getElementById('btn-search-product')) {
  document.getElementById('btn-search-product').addEventListener('click', searchProduct);
}
if (document.getElementById('btn-add-to-cart')) {
  document.getElementById('btn-add-to-cart').addEventListener('click', addToCart);
}
if (document.getElementById('btn-clear-cart')) {
  document.getElementById('btn-clear-cart').addEventListener('click', clearCart);
}
if (document.getElementById('btn-complete-sale')) {
  document.getElementById('btn-complete-sale').addEventListener('click', completeSale);
}
if (checkoutSearch) {
  checkoutSearch.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      event.preventDefault();
      searchProduct();
    }
  });
}
