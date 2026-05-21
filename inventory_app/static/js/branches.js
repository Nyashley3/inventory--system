const branchCreateButton = document.getElementById('b-create');
const branchesList = document.getElementById('branches-list');

async function loadBranches() {
  try {
    const branches = await apiGet('/api/branches');
    if (!branchesList) return;
    branchesList.innerHTML = '';
    branches.forEach(branch => {
      const li = document.createElement('li');
      li.className = 'list-group-item';
      li.innerText = `${branch.id}: ${branch.name} — ${branch.address}`;
      branchesList.appendChild(li);
    });
  } catch (err) {
    showAlert(err.msg || 'Unable to load branches.', 'danger');
  }
}

if (branchCreateButton) {
  branchCreateButton.addEventListener('click', async () => {
    const name = document.getElementById('b-name')?.value.trim();
    const address = document.getElementById('b-address')?.value.trim();
    if (!name) {
      showAlert('Branch name cannot be empty.', 'warning');
      return;
    }
    try {
      await apiPost('/api/branches', {name, address});
      showAlert('Branch created successfully.', 'success');
      document.getElementById('b-name').value = '';
      document.getElementById('b-address').value = '';
      loadBranches();
    } catch (err) {
      showAlert(err.msg || 'Could not create branch.', 'danger');
    }
  });
}

loadBranches();
