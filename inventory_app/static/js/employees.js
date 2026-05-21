const employeesTableBody = document.querySelector('#employees-table tbody');

async function loadEmployees() {
  try {
    const users = await apiGet('/api/users');
    if (!employeesTableBody) return;
    employeesTableBody.innerHTML = '';

    users.forEach(user => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${user.id}</td>
        <td>${user.username}</td>
        <td>${user.role}</td>
        <td>${user.branch_id || '-'} </td>
        <td>${user.locked ? '<span class="badge bg-danger">Locked</span>' : '<span class="badge bg-success">Active</span>'}</td>
        <td>${new Date(user.created_at).toLocaleString()}</td>
        <td>
          <button class="btn btn-sm btn-outline-${user.locked ? 'success' : 'warning'} user-lock" data-id="${user.id}" data-locked="${user.locked}">${user.locked ? 'Unlock' : 'Lock'}</button>
          <button class="btn btn-sm btn-outline-primary ms-1 user-reset" data-id="${user.id}" data-username="${user.username}">Reset Password</button>
        </td>
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

    document.querySelectorAll('.user-reset').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        const username = btn.dataset.username;
        const password = prompt(`Enter a new password for ${username}:`);
        if (!password) return;
        try {
          await apiPost(`/api/users/${id}/password`, {password});
          showAlert('Password reset successfully.', 'success');
        } catch (err) {
          showAlert(err.msg || 'Could not reset password.', 'danger');
        }
      });
    });
  } catch (err) {
    showAlert(err.msg || 'Unable to load employees.', 'danger');
  }
}

loadEmployees();
