document.addEventListener('DOMContentLoaded', () => {
  const summarizeBtn = document.getElementById('summarize-btn');
  // === Get the file input instead of the textarea ===
  const leaseFile = document.getElementById('lease-file');

  const loadingDiv = document.getElementById('loading');
  const resultsContainer = document.getElementById('results-container');
  const resultsDiv = document.getElementById('results');

  summarizeBtn.addEventListener('click', async () => {
    // === Get the file from the input ===
    const file = leaseFile.files[0];
    if (!file) {
      alert("Please select a file first.");
      return;
    }

    // --- Show loading, hide old results ---
    loadingDiv.classList.remove('hidden');
    resultsContainer.classList.add('hidden');
    resultsDiv.innerHTML = '';

    // === Create FormData to send the file ===
    const formData = new FormData();
    formData.append('file', file); // 'file' MUST match the 'file' argument in your FastAPI endpoint

    try {
      // === Call your local FastAPI server ===
      const response = await fetch('http://127.0.0.1:8000/summarize', {
        method: 'POST',
        // --- REMOVE the 'Content-Type' header. ---
        // The browser will automatically set the correct 'multipart/form-data' header
        // when you send FormData.
        body: formData, // --- Send the FormData object ---
      });

      // --- This part is all the same as before ---
      if (!response.ok) {
        // Try to parse the error message from the backend
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const report = await response.json();

      loadingDiv.classList.add('hidden');

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
      // We can now show the specific error from FastAPI (e.g., "Unsupported file type")
      resultsDiv.innerHTML = `<p style="color:red;">Error: ${error.message}. Is your local Python server running?</p>`;
      resultsContainer.classList.remove('hidden');
    }
  });
});