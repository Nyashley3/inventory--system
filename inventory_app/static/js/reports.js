const reportLoadButton = document.getElementById('r-load');
const reportBody = document.getElementById('r-card');

function renderReport(data, branch) {
  const branchLabel = branch ? ` for branch ${branch}` : '';
  return `
    <h5 class="mb-3">Sales Report — ${data.range.charAt(0).toUpperCase() + data.range.slice(1)}${branchLabel}</h5>
    <p>Total transactions: <strong>${data.count}</strong></p>
    <p>Total sales value: <strong>${parseFloat(data.total).toFixed(2)}</strong></p>
    <p>Report period begins: <strong>${new Date(data.start).toLocaleString()}</strong></p>
  `;
}

if (reportLoadButton) {
  reportLoadButton.addEventListener('click', async () => {
    const range = document.getElementById('r-range')?.value;
    const branch = document.getElementById('r-branch')?.value.trim();
    const q = branch ? `?range=${encodeURIComponent(range)}&branch_id=${encodeURIComponent(branch)}` : `?range=${encodeURIComponent(range)}`;
    try {
      const result = await apiGet('/api/reports/sales' + q);
      if (reportBody) reportBody.innerHTML = renderReport(result, branch);
      showAlert('Report loaded successfully.', 'success');
    } catch (err) {
      showAlert(err.msg || 'Unable to load report.', 'danger');
    }
  });
}
