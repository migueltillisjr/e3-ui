  // Uses your existing CLIENT_ROUTE_PREFIX
  const form = document.getElementById('uploadContactsForm');
  const fileInput = document.getElementById('contactsFile');
  const msg = document.getElementById('uploadContactsMsg');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const f = fileInput.files[0];
    if (!f) { msg.textContent = "Please choose a .tsv or .csv file."; return; }

    msg.textContent = "Uploading…";
    const fd = new FormData();
    fd.append('file', f, f.name);
    loadingOverlay.style.display = 'flex';
    try {
      const res = await fetch(CLIENT_ROUTE_PREFIX + '/upload_contacts', {
        method: 'POST',
        body: fd
      });

      if (!res.ok) {
        const err = await res.text();
        msg.textContent = `❌ Upload failed: ${err}`;
        msg.className = "mt-2 text-xs text-red-600";
        return;
      }

      const data = await res.json();
      loadingOverlay.style.display = 'none';
      msg.textContent = `✅ Imported ${data.rows} contacts (saved: ${data.saved}).`;
      msg.className = "mt-2 text-xs text-green-700";
    } catch (e) {
      loadingOverlay.style.display = 'none';
      msg.textContent = `❌ Error: ${e.message}`;
      msg.className = "mt-2 text-xs text-red-600";
    }
  });