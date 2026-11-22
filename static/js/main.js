/**
 * Employee Attrition Prediction & Analysis
 * Main Frontend JavaScript Utilities
 */

document.addEventListener("DOMContentLoaded", function () {
  // Initialize Bootstrap Tooltips
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Handle Form Submission Loading State
  const predictForm = document.getElementById("predict-form");
  if (predictForm) {
    predictForm.addEventListener("submit", function (e) {
      if (!predictForm.checkValidity()) {
        e.preventDefault();
        e.stopPropagation();
        predictForm.classList.add("was-validated");
        return;
      }
      const submitBtn = document.getElementById("submit-btn");
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
          <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          Running ML Pipeline...
        `;
      }
    });
  }

  // Clear Form Fields
  window.clearPredictForm = function () {
    const form = document.getElementById("predict-form");
    if (form) {
      form.reset();
      form.classList.remove("was-validated");
      const clientErr = document.getElementById("client-error");
      if (clientErr) {
        clientErr.classList.add("d-none");
      }
    }
  };
});
