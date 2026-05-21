// pages.js - shared helper functions for authenticated pages
function showAlert(message, type='danger', timeout=7000) {
  const container = document.getElementById('page-alert');
  if (!container) return;
  container.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">${message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
  if (timeout) setTimeout(()=>{ if (container.firstElementChild?.classList.contains('show')) container.innerHTML = ''; }, timeout);
}

async function parseResponse(res) {
  let payload;
  try { payload = await res.json(); } catch (_) { payload = {msg: res.statusText}; }
  if (!res.ok) throw payload;
  return payload;
}

async function apiGet(path) {
  const token = localStorage.getItem('token');
  const res = await fetch(path, {headers: token ? {'Authorization': 'Bearer '+token} : {}});
  if (res.status === 401) { localStorage.removeItem('token'); location.href = '/'; throw {msg: 'Unauthorized'}; }
  return parseResponse(res);
}

async function apiPost(path, body) {
  const token = localStorage.getItem('token');
  const res = await fetch(path, {method: 'POST', headers: {'Content-Type':'application/json', 'Authorization': 'Bearer '+token}, body: JSON.stringify(body)});
  if (res.status === 401) { localStorage.removeItem('token'); location.href = '/'; throw {msg: 'Unauthorized'}; }
  return parseResponse(res);
}

async function apiDelete(path) {
  const token = localStorage.getItem('token');
  const res = await fetch(path, {method:'DELETE', headers: {'Authorization': 'Bearer '+token}});
  if (res.status === 401) { localStorage.removeItem('token'); location.href = '/'; throw {msg: 'Unauthorized'}; }
  return parseResponse(res);
}

// unified logout handler for both navbar and dropdown
function doLogout(){
  const token = localStorage.getItem('token');
  if (token) {
    fetch('/api/logout', {method:'POST', headers: {'Authorization': 'Bearer '+token}}).catch(()=>{});
  }
  localStorage.removeItem('token');
  location.href='/';
}

document.getElementById('nav-logout')?.addEventListener('click', doLogout);
document.getElementById('nav-logout-link')?.addEventListener('click', (e)=>{ e.preventDefault(); doLogout(); });

(async ()=>{
  try {
    const token = localStorage.getItem('token');
    if (!token) return;
    const payload = JSON.parse(atob(token.split('.')[1]));
    const role = payload.role || '';
    const navUser = document.getElementById('nav-user');
    if (navUser) navUser.innerText = (payload.sub || '') + (role ? ` • ${role}` : '');

    // role-based menu visibility
    document.querySelectorAll('[data-roles]').forEach(li => {
      const roles = li.dataset.roles.split(',');
      if (role === 'admin') {
        // admin sees items unless explicitly hidden for admin
        if (li.dataset.hideForAdmin === 'true') li.style.display = 'none'; else li.style.display = '';
      } else {
        if (!roles.includes(role)) li.style.display = 'none'; else li.style.display = '';
      }
    });

    // hide items explicitly marked as hidden for admin
    document.querySelectorAll('[data-hide-for-admin]').forEach(el => {
      if (role === 'admin') el.style.display = 'none'; else el.style.display = '';
    });

  } catch (e) {
    console.warn('Unable to decode token', e);
  }
})();
