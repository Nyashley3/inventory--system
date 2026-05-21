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

document.getElementById('nav-logout')?.addEventListener('click', async ()=>{
  const token = localStorage.getItem('token');
  if (token) {
    await fetch('/api/logout', {method:'POST', headers: {'Authorization': 'Bearer '+token}}).catch(()=>{});
  }
  localStorage.removeItem('token');
  location.href='/';
});

(async ()=>{
  try {
    const token = localStorage.getItem('token');
    if (!token) return;
    const payload = JSON.parse(atob(token.split('.')[1]));
    const role = payload.role || '';
    document.getElementById('nav-user').innerText = (payload.sub || '') + (role ? ` • ${role}` : '');
    document.querySelectorAll('[data-roles]').forEach(li => {
      const roles = li.dataset.roles.split(',');
      if (!roles.includes(role)) li.style.display = 'none';
    });
  } catch (e) {
    console.warn('Unable to decode token', e);
  }
})();
