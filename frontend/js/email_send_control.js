
document.addEventListener("DOMContentLoaded", () => {


  async function runCampaign(settings) {
    const loadingOverlay_runCampaign = document.getElementById('loadingOverlay');
    loadingOverlay_runCampaign.style.display = 'flex';
    try {
      const sendRes = await fetch(CLIENT_ROUTE_PREFIX + "/send_campaign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });
  
      if (!sendRes.ok) {
        const errorText = await sendRes.text(); // Optional: parse more detailed error
        alert(`❌ Failed to send email: ${errorText || sendRes.statusText}`);
        return;
      }
  
      alert("✅ Campaign sent successfully!");
      loadingOverlay_runCampaign.style.display = 'none';
    } catch (e) {
      alert(`❌ Unexpected error: ${e.message}`);
      loadingOverlay_runCampaign.style.display = 'none';
    }
  }
  
  // Hook up save handler
window.sendEmail = function () {
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
    alert("❌ One or more required email setup fields are empty.");
    return;
  }

  const settings = {
    design_name: designNameEl.value,
    html_email_design: `https://e3-designs.s3.amazonaws.com/${designNameEl.value}`,
    subject: subjectEl.value,
    preview: previewEl.value,
    from_data: fromEl.value,
    tracking: trackingEl.value,
    send_date: dateEl.value,
  };

  // Display confirmation popup
  const summaryHTML = `
    <p><strong>Design:</strong> ${settings.design_name}</p>
    <p><strong>Subject:</strong> ${settings.subject}</p>
    <p><strong>Preview Text:</strong> ${settings.preview}</p>
    <p><strong>From:</strong> ${settings.from_data}</p>
    <p><strong>Tracking:</strong> ${settings.tracking}</p>
    <p><strong>Send Date:</strong> ${settings.send_date}</p>
  `;
  document.getElementById("emailSummary").innerHTML = summaryHTML;
  document.getElementById("emailConfirmPopup").style.display = "flex";

  // Attach confirmation click handler
  document.getElementById("confirmSendBtn").onclick = function () {
    document.getElementById("emailConfirmPopup").style.display = "none";
    runCampaign(settings);
  };
};

});

    // Replace with actual email-sending logic
    // fetch(CLIENT_ROUTE_PREFIX + "/send_email", {
    //   method: "POST",
    //   headers: { "Content-Type": "application/json" },
    //   body: JSON.stringify(settings),
    // }).then((response) => {
    //   alert(response.ok ? "📨 Email is being sent with all required fields!" : "❌ Failed to send email.");
    // });

