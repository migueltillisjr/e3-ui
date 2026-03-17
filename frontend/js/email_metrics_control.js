document.addEventListener("DOMContentLoaded", () => {
  const metricsBtn = document.getElementById("toggleMetricsBtn");
  const metricsPanel = document.getElementById("metricsPanel");
  const metricsImage = document.getElementById("metricsImage");
  const spinner = document.getElementById("spinner");

  if (metricsBtn && metricsPanel && metricsImage && spinner) {
    metricsBtn.addEventListener("click", () => {
      // Show spinner
      spinner.style.display = "block";
      metricsImage.style.display = "none";

      // Load image
      metricsImage.src = CLIENT_ROUTE_PREFIX + "/view_metrics?cache_bust=" + Date.now(); // cache-bust

      // Once image is loaded, hide spinner
      metricsImage.onload = () => {
        spinner.style.display = "none";
        metricsImage.style.display = "block";
      };

      // Show panel
      metricsPanel.classList.remove("opacity-0", "pointer-events-none");
      metricsPanel.classList.add("opacity-100");
    });
  }

  window.closeMetrics = () => {
    if (metricsPanel) {
      metricsPanel.classList.add("opacity-0", "pointer-events-none");
      metricsPanel.classList.remove("opacity-100");
    }
  };
});
