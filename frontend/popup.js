document.addEventListener('DOMContentLoaded', () => {
  const summarizeBtn = document.getElementById('summarize-btn');
  const leaseFile = document.getElementById('lease-file');
  const loadingDiv = document.getElementById('loading');
  const resultsContainer = document.getElementById('results-container');
  const resultsDiv = document.getElementById('results');

  // --- Helper function to create a report section ---
  // This keeps our code clean
  function createReportSection(title, data) {
    let html = `<h3 class="category">${title}</h3>`;
    for (const [key, value] of Object.entries(data)) {
      // Format the key from 'security_deposit' to 'Security Deposit'
      const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      html += `<h4>${formattedKey}</h4><p>${value}</p>`;
    }
    return html;
  }

  summarizeBtn.addEventListener('click', async () => {
    const file = leaseFile.files[0];
    if (!file) {
      alert("Please select a file first.");
      return;
    }

    loadingDiv.classList.remove('hidden');
    resultsContainer.classList.add('hidden');
    resultsDiv.innerHTML = '';

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://127.0.0.1:8000/summarize', {
        // Change this URL when you deploy!
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const report = await response.json();
      loadingDiv.classList.add('hidden');

      // -----------------------------------------------------------------
      // --- STEP 3: UPDATE THE RENDER LOGIC ---
      // -----------------------------------------------------------------

      // We will render the report in sections
      resultsDiv.innerHTML = createReportSection('Money', {
        security_deposit: report.security_deposit,
        deposit_conditions: report.deposit_conditions,
        non_refundable_fees: report.non_refundable_fees,
        late_fee_policy: report.late_fee_policy,
      });

      resultsDiv.innerHTML += createReportSection('Moving Out', {
        termination_notice: report.termination_notice,
        early_termination_penalty: report.early_termination_penalty,
        auto_renewal_clause: report.auto_renewal_clause,
      });

      resultsDiv.innerHTML += createReportSection('Living There', {
        pet_policy: report.pet_policy,
        guest_policy: report.guest_policy,
        subletting_policy: report.subletting_policy,
        maintenance_and_repairs: report.maintenance_and_repairs,
        utilities_included: report.utilities_included,
      });

      resultsContainer.classList.remove('hidden');

    } catch (error) {
      loadingDiv.classList.add('hidden');
      resultsDiv.innerHTML = `<p style="color:red;">Error: ${error.message}. Is your local Python server running?</p>`;
      resultsContainer.classList.remove('hidden');
    }
  });
});