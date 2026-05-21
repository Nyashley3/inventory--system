const employeesTableBody = document.querySelector('#employees-table tbody');
const createButton = document.getElementById('create-user');
const currentToken = localStorage.getItem('token');
const currentPayload = currentToken ? JSON.parse(atob(currentToken.split('.')[1])) : {};
const isAdmin = currentPayload.role === 'admin';

async function createUser() {
  const username = document.getElementById('new-username')?.value.trim();
  const fullName = document.getElementById('new-fullname')?.value.trim();
  const sex = document.getElementById('new-sex')?.value;
  const age = document.getElementById('new-age')?.value.trim();
  const role = document.getElementById('new-role')?.value;
  const branchId = document.getElementById('new-branch')?.value.trim();

  if (!username || !role) {
    showAlert('Username and role are required to create a user.', 'warning');
    return;
  }

  const payload = { username, role };
  if (fullName) payload.full_name = fullName;
  if (sex) payload.sex = sex;
  if (age) payload.age = age;
  if (branchId) {
    const parsed = Number(branchId);
    if (!Number.isInteger(parsed) || parsed <= 0) {
      showAlert('Branch ID must be a positive integer.', 'warning');
      return;
    }
    payload.branch_id = parsed;
  }

  try {
    const result = await apiPost('/api/signup', payload);
    let message = 'User created successfully.';
    if (result.temp_password) {
      message += ` Temporary password: ${result.temp_password}`;
    }
    showAlert(message, 'success');
    document.getElementById('new-username').value = '';
    document.getElementById('new-fullname').value = '';
    document.getElementById('new-sex').value = '';
    document.getElementById('new-age').value = '';
    document.getElementById('new-branch').value = '';
    loadEmployees();
  } catch (err) {
    showAlert(err.msg || 'Could not create user.', 'danger');
  }
}

async function loadEmployees() {
  try {
    const users = await apiGet('/api/users');
    if (!employeesTableBody) return;
    employeesTableBody.innerHTML = '';

    users.forEach(user => {
      const tr = document.createElement('tr');
      const actionButtons = [];
      actionButtons.push(`<button class="btn btn-sm btn-outline-${user.locked ? 'success' : 'warning'} user-lock" data-id="${user.id}" data-locked="${user.locked}">${user.locked ? 'Unlock' : 'Lock'}</button>`);
      actionButtons.push(`<button class="btn btn-sm btn-outline-info user-details" data-id="${user.id}" data-username="${user.username}">Details</button>`);
      actionButtons.push(`<button class="btn btn-sm btn-outline-primary ms-1 user-reset" data-id="${user.id}" data-username="${user.username}">Reset Password</button>`);
      if (isAdmin && user.role !== 'admin') {
        actionButtons.push(`<button class="btn btn-sm btn-outline-danger ms-1 user-delete" data-id="${user.id}" data-username="${user.username}">Delete</button>`);
      }

      tr.innerHTML = `
        <td>${user.id}</td>
        <td>${user.username}</td>
        <td>${user.full_name || '-'}</td>
        <td>${user.role}</td>
        <td>${user.branch_id || '-'} </td>
        <td>${user.sex || '-'} </td>
        <td>${user.age != null ? user.age : '-'} </td>
        <td>${user.locked ? '<span class="badge bg-danger">Locked</span>' : '<span class="badge bg-success">Active</span>'}</td>
        <td>${new Date(user.created_at).toLocaleString()}</td>
        <td>${actionButtons.join(' ')}</td>
      `;
      employeesTableBody.appendChild(tr);
    });

    document.querySelectorAll('.user-lock').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        const locked = btn.dataset.locked === 'true';
        try {
          await apiPost(`/api/users/${id}/lock`, {locked: !locked});
          showAlert(`User ${locked ? 'unlocked' : 'locked'} successfully.`, 'success');
          loadEmployees();
        } catch (err) {
          showAlert(err.msg || 'Could not update user lock status.', 'danger');
        }
      });
    });

    document.querySelectorAll('.user-details').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.id;
        const username = btn.dataset.username;
        const selected = users.find(u => String(u.id) === String(id));
        if (selected) setSelectedUser(selected);
      });
    });

    document.querySelectorAll('.user-reset').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        const username = btn.dataset.username;
        const password = prompt(`Enter a new password for ${username} (leave blank to auto-generate):`);
        if (password === null) return;
        const payload = {};
        if (password !== '') payload.password = password;
        try {
          const result = await apiPost(`/api/users/${id}/password`, payload);
          if (result.temp_password) {
            showAlert(`Password reset successfully. Temporary password: ${result.temp_password}`, 'success');
          } else {
            showAlert('Password reset successfully.', 'success');
          }
          loadEmployees();
        } catch (err) {
          showAlert(err.msg || 'Could not reset password.', 'danger');
        }
      });
    });

    document.querySelectorAll('.user-delete').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        const username = btn.dataset.username;
        if (!confirm(`Delete user ${username}? This cannot be undone.`)) return;
        try {
          await apiDelete(`/api/users/${id}`);
          showAlert('User deleted successfully.', 'success');
          clearSelectedUser();
          loadEmployees();
        } catch (err) {
          showAlert(err.msg || 'Could not delete user.', 'danger');
        }
      });
    });
  } catch (err) {
    showAlert(err.msg || 'Unable to load employees.', 'danger');
  }
}

function setSelectedUser(user){
  const detailFields = {
    'detail-username': user.username,
    'detail-fullname': user.full_name || '-',
    'detail-role': user.role,
    'detail-branch': user.branch_id || '-',
    'detail-sex': user.sex || '-',
    'detail-age': user.age != null ? user.age : '-',
    'detail-status': user.locked ? 'Locked' : 'Active',
    'detail-created': new Date(user.created_at).toLocaleString()
  };
  Object.entries(detailFields).forEach(([id, value]) => {
    const el = document.getElementById(id);
    if (el) el.innerText = value;
  });
  const card = document.getElementById('employee-detail-card');
  if (card) card.style.display = '';
}

function clearSelectedUser(){
  ['detail-username','detail-fullname','detail-role','detail-branch','detail-sex','detail-age','detail-status','detail-created'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerText = '-';
  });
  const card = document.getElementById('employee-detail-card');
  if (card) card.style.display = 'none';
}

const clearButton = document.getElementById('clear-selected-user');
clearButton?.addEventListener('click', clearSelectedUser);

createButton?.addEventListener('click', createUser);
loadEmployees();
