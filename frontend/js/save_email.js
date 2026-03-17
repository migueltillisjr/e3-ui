// save html
async function saveHTML() {
  const htmlInput = document.getElementById('htmlInput');
  const htmlContent = htmlInput.value.trim();

  if (!htmlContent) {
    alert("Nothing to save.");
    return;
  }

  // 1) POST the new design
  loadingOverlay.style.display = 'flex';
  try {
    const params = new URLSearchParams(window.location.search);
    const file = params.get("file")
    const saveRes = await fetch(CLIENT_ROUTE_PREFIX + `/save_email_design/?file=${file}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ html: htmlContent })
    });
    if (!saveRes.ok) throw new Error('Save failed.');
    const data = await saveRes.json();
    alert('✅ Saved successfully!');
    console.log('Server response:', data);
  } catch (err) {
    alert('❌ Failed to save.');
    console.error('Save error:', err);
    return; // stop here on save failure
  }

  // 2) Load the saved HTML back into editor & preview
  try {
    const params = new URLSearchParams(window.location.search);
    const file = params.get("file") || "email_design1.html"; // fallback if no param

    const loadRes = await fetch(CLIENT_ROUTE_PREFIX + `/email_designs/?file=${file}&t=${Date.now()}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache"
      }
    });

    if (!loadRes.ok) throw new Error('Failed to load HTML content');
    const loadedHtml = await loadRes.text();

    // Populate the editor textarea
    htmlInput.value = loadedHtml;

    // Load into iframe preview via srcdoc to avoid caching
    const preview = document.getElementById('preview');
    preview.srcdoc = loadedHtml;
  } catch (error) {

    console.error('Load error:', error);
  }
  loadingOverlay.style.display = 'none';
}
