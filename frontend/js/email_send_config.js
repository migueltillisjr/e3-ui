document.addEventListener("DOMContentLoaded", () => {
    // Toggle visibility
    document.getElementById("toggleEmailPanelBtn").addEventListener("click", () => {
      const panel = document.getElementById("emailPanel");
      const isVisible = panel.classList.contains("opacity-100");
      panel.classList.toggle("opacity-0", isVisible);
      panel.classList.toggle("pointer-events-none", isVisible);
      panel.classList.toggle("opacity-100", !isVisible);
    });
  
    // Hook up save handler
    window.saveEmailSettings = function () {
      const designNameEl = document.getElementById("designName");
      const subjectEl = document.getElementById("emailSubject");
      const previewEl = document.getElementById("emailPreview");
      const fromEl = document.getElementById("emailFrom");
      const trackingEl = document.getElementById("emailTracking");
      const dateEl = document.getElementById("sendDate");
  

      if (
        !subjectEl || !previewEl || !fromEl || !trackingEl || !dateEl || !designNameEl ||
        !subjectEl.value.trim() ||
        !previewEl.value.trim() ||
        !fromEl.value.trim() ||
        !trackingEl.value.trim() ||
        !dateEl.value.trim() ||
        !designNameEl.value.trim()
      ) {
        alert("❌ One or more required input fields are empty.");
        return;
      }
      
      const params = new URLSearchParams(window.location.search);
      const file = params.get("file"); // fallback if no param
      const settings = {
        design_name: file,
        //html_email_design: `https://${S3_BUCKET_NAME}.s3.amazonaws.com/${file}_${dateEl.value}_id${uniqueId}`, // define this or hardcode for now

        html_email_design: `https://${S3_BUCKET_NAME}.s3.amazonaws.com/${file}`, // define this or hardcode for now
        subject: subjectEl.value,
        preview: previewEl.value,
        from_data: fromEl.value,
        tracking: trackingEl.value,
        send_date: dateEl.value,
      };

      console.log(settings);

      fetch(CLIENT_ROUTE_PREFIX + `/save_email_config/?file=${file}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      }).then((response) => {
        alert(response.ok ? "✅ Email settings saved." : "❌ Failed to save settings.");
      });
    };
  });
  