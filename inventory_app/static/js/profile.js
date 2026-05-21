const btnChange = document.getElementById('change-password');
const alertContainer = document.getElementById('profile-alert');

function localAlert(msg, type='danger'){
  if (!alertContainer) return;
  alertContainer.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">${msg}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
}

function setProfileField(id, value) {
  const el = document.getElementById(id);
  if (el) el.innerText = value != null && value !== '' ? value : '-';
}

async function loadProfile() {
  try {
    const profile = await apiGet('/api/profile');
    setProfileField('profile-username', profile.username);
    setProfileField('profile-fullname', profile.full_name);
    setProfileField('profile-role', profile.role);
    setProfileField('profile-branch', profile.branch_id || '-');
    setProfileField('profile-sex', profile.sex);
    setProfileField('profile-age', profile.age != null ? profile.age : '-');
    setProfileField('profile-status', profile.locked ? 'Locked' : 'Active');
    setProfileField('profile-created', new Date(profile.created_at).toLocaleString());
    if (profile.force_password_reset) {
      localAlert('You are required to change your temporary password before using the system.', 'info');
    }
  } catch (err) {
    localAlert(err.msg || 'Unable to load profile information.', 'danger');
  }
}

async function handleChange(){
  const cur = document.getElementById('cur-password')?.value || '';
  const nw = document.getElementById('new-password')?.value || '';
  const cf = document.getElementById('confirm-password')?.value || '';
  if (!cur || !nw || !cf){ localAlert('All fields are required.', 'warning'); return; }
  if (nw !== cf){ localAlert('New password and confirmation do not match.', 'warning'); return; }
  try{
    await apiPost('/api/change-password', {old_password: cur, new_password: nw});
    localAlert('Password changed successfully.', 'success');
    document.getElementById('cur-password').value='';
    document.getElementById('new-password').value='';
    document.getElementById('confirm-password').value='';
  }catch(err){ localAlert(err.msg || 'Could not change password.', 'danger'); }
}

btnChange?.addEventListener('click', handleChange);
loadProfile();
