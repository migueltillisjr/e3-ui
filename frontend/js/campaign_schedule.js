function getSettings() {
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
    return null;
  }

  return {
    design_name: designNameEl.value,
    html_email_design: `https://e3-designs.s3.amazonaws.com/${designNameEl.value}`,
    subject: subjectEl.value,
    preview: previewEl.value,
    from_data: fromEl.value,
    tracking: trackingEl.value,
    send_date: dateEl.value,
  };
}

async function scheduleCampaign() {
  const settings = getSettings();
  if (!settings) return;

  const res = await fetch(CLIENT_ROUTE_PREFIX + "/schedule_campaign", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
  console.log("schedule settings: ");
  console.log(settings);
  await loadScheduledcampaigns();
}



function toggleSchedulePanel() {
  const pane = document.getElementById("schedulePanel");
  const isHidden = pane.classList.contains("opacity-0");

  if (isHidden) {
    pane.classList.remove("opacity-0", "pointer-events-none");
    pane.classList.add("opacity-100");
  } else {
    pane.classList.add("opacity-0", "pointer-events-none");
    pane.classList.remove("opacity-100");
  }
}

function closeSchedulePanel() {
  const pane = document.getElementById("schedulePanel");
  pane.classList.remove("opacity-100");
  pane.classList.add("opacity-0", "pointer-events-none");
}

async function loadScheduledcampaigns() {
  try {

    const res = await fetch(CLIENT_ROUTE_PREFIX + "/scheduled_campaigns", {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      }
    });
    
    const data = await res.json();
    console.log("Scheduled campaigns Response:", data);

    // Fallback handling in case data is not an array
    const campaigns = Array.isArray(data) ? data : data.campaigns || [];

    const list = document.getElementById("scheduledList");
    list.innerHTML = campaigns.map(campaign => `
      <div class="border p-2 my-2 rounded">
        <strong>${campaign.subject}</strong> to ${campaign.recipient} at ${campaign.send_at}
        <button onclick="deletecampaign('${campaign.id}')" class="ml-2 text-red-600">🗑️ Delete</button>
      </div>
    `).join('');
  } catch (error) {
    console.error("Failed to load scheduled campaigns:", error);
  }
}

async function deletecampaign(id) {

  await fetch(`/delete_campaign/${id}`, {
    method: "GET",
    method: "DELETE",
    headers: {
      "Content-Type": "application/json"
    }
  });

  await loadScheduledcampaigns();
}

// window.onload = loadScheduledcampaigns;