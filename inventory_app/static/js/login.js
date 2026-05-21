const alertContainer = document.getElementById('alert');
const alertEl = (msg, cls = 'danger') => {
  if (!alertContainer) return;
  alertContainer.innerHTML = `<div class="alert alert-${cls} alert-dismissible fade show" role="alert">${msg}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
};

const usernameInput = document.getElementById('login-username');
const passwordInput = document.getElementById('login-password');
const loginButton = document.getElementById('btn-login');

async function handleLogin(event) {
  if (event) event.preventDefault();
  if (!usernameInput || !passwordInput || !loginButton) return;

  const u = usernameInput.value.trim();
  const p = passwordInput.value;
  if (!u || !p) {
    alertEl('Please enter both username and password.', 'warning');
    return;
  }

  loginButton.disabled = true;
  loginButton.innerText = 'Signing in...';

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username: u, password: p})
    });

    let body;
    try {
      body = await res.json();
    } catch (_) {
      body = {msg: res.statusText || 'Unexpected response from server.'};
    }

    if (res.ok && body.access_token) {
      localStorage.setItem('token', body.access_token);
      location.href = '/dashboard';
      return;
    }

    const message = body.msg || `Login failed (${res.status}).`;
    alertEl(message, 'danger');
    console.error('Login failed', res.status, body);
  } catch (err) {
    alertEl('Unable to reach the server. Please make sure the app is running and try again.', 'danger');
    console.error('Login error', err);
  } finally {
    loginButton.disabled = false;
    loginButton.innerText = 'Login';
  }
}

if (loginButton) {
  loginButton.addEventListener('click', handleLogin);
}

[usernameInput, passwordInput].forEach(input => {
  if (!input) return;
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      handleLogin(event);
    }
  });
});
