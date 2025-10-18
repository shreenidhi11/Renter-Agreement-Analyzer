document.addEventListener('DOMContentLoaded', () => {
  const summarizeBtn = document.getElementById('summarize-btn');
  const leaseText = document.getElementById('lease-text');
  const loadingDiv = document.getElementById('loading');
  const resultsContainer = document.getElementById('results-container');
  const resultsDiv = document.getElementById('results');

  summarizeBtn.addEventListener('click', async () => {
    const text = leaseText.value;
    if (!text) {
      alert("Please paste your lease text first.");
      return;
    }

    // --- Show loading, hide old results ---
    loadingDiv.classList.remove('hidden');
    resultsContainer.classList.add('hidden');
    resultsDiv.innerHTML = '';

    try {
      // --- Call your local FastAPI server ---
      const response = await fetch('http://127.0.0.1:8000/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: text }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const report = await response.json();

      // --- Hide loading ---
      loadingDiv.classList.add('hidden');

      // --- Render the results ---
      resultsDiv.innerHTML = `
        <h3>Security Deposit</h3>
        <p>${report.security_deposit}</p>

        <h3>Pet Policy</h3>
        <p>${report.pet_policy}</p>

        <h3>Termination Notice</h3>
        <p>${report.termination_notice}</p>

        <h3>Guest Policy</h3>
        <p>${report.guest_policy}</p>

        <h3>Auto-Renewal</h3>
        <p>${report.auto_renewal}</p>

        <h3>Hidden Fees / Other</h3>
        <p>${report.hidden_fees}</p>
      `;
      resultsContainer.classList.remove('hidden');

    } catch (error) {
      loadingDiv.classList.add('hidden');
      resultsDiv.innerHTML = `<p style="color:red;">Error: ${error.message}. Is your local Python server running?</p>`;
      resultsContainer.classList.remove('hidden');
    }
  });
});