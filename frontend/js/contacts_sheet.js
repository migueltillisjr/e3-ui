/**
 * Contacts Spreadsheet — fetches contacts JSON and renders an Excel-style table
 * with search, sort, inline editing, and delete functionality.
 */
document.addEventListener("DOMContentLoaded", () => {
  const panel        = document.getElementById("contactsPanel");
  const closeBtn     = document.getElementById("closeContactsPanel");
  const thead        = document.getElementById("contactsThead");
  const tbody        = document.getElementById("contactsTbody");
  const promptBar    = document.getElementById("contactsPromptBar");
  const promptText   = document.getElementById("contactsPromptText");
  const countEl      = document.getElementById("contactsCount");
  const tableWrap    = document.getElementById("contactsTableWrap");
  const loading      = document.getElementById("contactsLoading");
  const downloadLink = document.getElementById("contactsDownloadLink");
  const searchInput  = document.getElementById("contactsSearch");
  const emptyState   = document.getElementById("contactsEmptyState");

  const DISPLAY_COLS = [
    "first_name", "last_name", "email", "validated",
    "phone", "company", "job_title", "city", "state", "country"
  ];

  let loaded = false;
  let allRows = [];
  let filteredRows = [];
  let activeCols = [];
  let sortCol = null;
  let sortAsc = true;
  // Toggle panel
  document.getElementById("toggleContactsBtn").addEventListener("click", () => {
    const isHidden = panel.classList.contains("opacity-0");
    if (isHidden) {
      panel.classList.remove("opacity-0");
      panel.classList.add("opacity-100");
      fetchContacts();
    } else {
      panel.classList.remove("opacity-100");
      panel.classList.add("opacity-0");
    }
  });

  closeBtn.addEventListener("click", () => {
    panel.classList.remove("opacity-100");
    panel.classList.add("opacity-0");
  });

  downloadLink.href = CLIENT_ROUTE_PREFIX + "/download_contacts";

  // Search handler
  searchInput.addEventListener("input", () => {
    const q = searchInput.value.trim().toLowerCase();
    if (!q) {
      filteredRows = allRows;
    } else {
      filteredRows = allRows.filter(row =>
        activeCols.some(col => (row[col] || "").toLowerCase().includes(q))
      );
    }
    updateCount();
    renderBody(filteredRows, activeCols);
  });

  async function fetchContacts() {
    loading.style.display = "block";
    tableWrap.style.display = "none";
    promptBar.style.display = "none";
    emptyState.style.display = "none";

    try {
      const res = await fetch(CLIENT_ROUTE_PREFIX + "/contacts_json");
      if (!res.ok) {
        const err = await res.json();
        showEmpty(err.error || "No contacts found.");
        loading.style.display = "none";
        return;
      }

      const data = await res.json();
      loaded = true;

      if (!data.rows || data.rows.length === 0) {
        showEmpty("No contacts yet. Use AI or upload a file to get started.");
        loading.style.display = "none";
        return;
      }

      // Show prompt
      if (data.prompt) {
        promptText.textContent = data.prompt;
        promptBar.style.display = "block";
      }

      activeCols = DISPLAY_COLS.filter(c => data.columns.includes(c));
      allRows = data.rows;
      filteredRows = allRows;
      sortCol = null;
      sortAsc = true;
      searchInput.value = "";

      updateCount();
      renderHeader(activeCols);
      renderBody(filteredRows, activeCols);
    } catch (e) {
      showEmpty("Error loading contacts: " + e.message);
    } finally {
      loading.style.display = "none";
      tableWrap.style.display = "block";
    }
  }

  function showEmpty(msg) {
    emptyState.textContent = msg;
    emptyState.style.display = "block";
    tableWrap.style.display = "none";
    countEl.textContent = "";
  }

  function updateCount() {
    const total = allRows.length;
    const shown = filteredRows.length;
    countEl.textContent = shown === total
      ? `${total.toLocaleString()} contacts`
      : `${shown.toLocaleString()} of ${total.toLocaleString()} contacts`;
  }

  function renderHeader(cols) {
    thead.innerHTML = "";
    const tr = document.createElement("tr");

    // Row number header
    const thNum = document.createElement("th");
    thNum.textContent = "#";
    thNum.className = "sheet-th sheet-th-num";
    tr.appendChild(thNum);

    cols.forEach(col => {
      const th = document.createElement("th");
      th.className = "sheet-th sheet-th-sortable";
      th.dataset.col = col;

      const label = document.createElement("span");
      label.textContent = col.replace(/_/g, " ");
      th.appendChild(label);

      // Sort indicator
      const arrow = document.createElement("span");
      arrow.className = "sort-arrow";
      if (sortCol === col) {
        arrow.textContent = sortAsc ? " ▲" : " ▼";
      }
      th.appendChild(arrow);

      th.addEventListener("click", () => handleSort(col));
      tr.appendChild(th);
    });

    // Actions header
    const thAct = document.createElement("th");
    thAct.textContent = "";
    thAct.className = "sheet-th sheet-th-num";
    thAct.style.width = "50px";
    tr.appendChild(thAct);

    thead.appendChild(tr);
  }

  function handleSort(col) {
    if (sortCol === col) {
      sortAsc = !sortAsc;
    } else {
      sortCol = col;
      sortAsc = true;
    }
    filteredRows.sort((a, b) => {
      const va = (a[col] || "").toLowerCase();
      const vb = (b[col] || "").toLowerCase();
      if (va < vb) return sortAsc ? -1 : 1;
      if (va > vb) return sortAsc ? 1 : -1;
      return 0;
    });
    renderHeader(activeCols);
    renderBody(filteredRows, activeCols);
  }

  function renderBody(rows, cols) {
    tbody.innerHTML = "";
    const BATCH = 200;
    let idx = 0;

    function renderBatch() {
      const frag = document.createDocumentFragment();
      const end = Math.min(idx + BATCH, rows.length);
      for (; idx < end; idx++) {
        const row = rows[idx];
        const tr = document.createElement("tr");
        tr.className = idx % 2 === 0 ? "sheet-row-even" : "sheet-row-odd";

        // Row number
        const tdNum = document.createElement("td");
        tdNum.textContent = idx + 1;
        tdNum.className = "sheet-td sheet-td-num";
        tr.appendChild(tdNum);

        cols.forEach(col => {
          const td = document.createElement("td");
          td.className = "sheet-td";
          const val = row[col] || "";

          if (col === "validated") {
            td.innerHTML = val === "1"
              ? '<span class="badge-valid">✓</span>'
              : '<span class="badge-invalid">✗</span>';
          } else {
            td.textContent = val;
          }
          tr.appendChild(td);
        });

        // Delete button
        const tdAct = document.createElement("td");
        tdAct.className = "sheet-td sheet-td-num";
        const delBtn = document.createElement("button");
        delBtn.className = "sheet-delete-btn";
        delBtn.textContent = "✕";
        delBtn.title = "Remove contact";
        delBtn.addEventListener("click", () => deleteRow(row, tr));
        tdAct.appendChild(delBtn);
        tr.appendChild(tdAct);

        frag.appendChild(tr);
      }
      tbody.appendChild(frag);
      if (idx < rows.length) requestAnimationFrame(renderBatch);
    }
    renderBatch();
  }

  function deleteRow(row, tr) {
    const idx = allRows.indexOf(row);
    if (idx > -1) allRows.splice(idx, 1);
    const fIdx = filteredRows.indexOf(row);
    if (fIdx > -1) filteredRows.splice(fIdx, 1);
    tr.remove();
    updateCount();
    markDirty();
  }

  let dirty = false;
  function markDirty() {
    if (dirty) return;
    dirty = true;
    showSaveBar();
  }

  function showSaveBar() {
    let bar = document.getElementById("contactsSaveBar");
    if (bar) { bar.style.display = "flex"; return; }
    bar = document.createElement("div");
    bar.id = "contactsSaveBar";
    bar.className = "contacts-save-bar";
    bar.innerHTML = `
      <span style="font-size:12px; color:var(--warning);">Unsaved changes</span>
      <button id="contactsSaveBtn" class="panel-btn panel-btn--success" style="width:auto; padding:6px 16px; font-size:12px;">Save Changes</button>
    `;
    // Insert before the upload section
    const uploadSection = panel.querySelector('[style*="border-top"]');
    if (uploadSection) {
      panel.insertBefore(bar, uploadSection);
    } else {
      panel.appendChild(bar);
    }
    document.getElementById("contactsSaveBtn").addEventListener("click", saveContacts);
  }

  async function saveContacts() {
    const btn = document.getElementById("contactsSaveBtn");
    btn.textContent = "Saving…";
    btn.disabled = true;
    try {
      // Build TSV from allRows using all original columns
      const allColSet = new Set();
      allRows.forEach(r => Object.keys(r).forEach(k => allColSet.add(k)));
      const allColArr = Array.from(allColSet);

      let tsv = allColArr.join("\t") + "\n";
      allRows.forEach(row => {
        tsv += allColArr.map(c => (row[c] || "").replace(/\t/g, " ")).join("\t") + "\n";
      });

      const blob = new Blob([tsv], { type: "text/tab-separated-values" });
      const fd = new FormData();
      fd.append("file", blob, "contacts.tsv");

      const res = await fetch(CLIENT_ROUTE_PREFIX + "/upload_contacts", {
        method: "POST",
        body: fd
      });

      if (!res.ok) throw new Error(await res.text());

      dirty = false;
      const bar = document.getElementById("contactsSaveBar");
      if (bar) bar.style.display = "none";
      btn.textContent = "Save Changes";
      btn.disabled = false;
    } catch (e) {
      btn.textContent = "Save Changes";
      btn.disabled = false;
      alert("Save failed: " + e.message);
    }
  }

  // Allow re-fetch after upload
  window.refreshContactsSheet = () => { loaded = false; dirty = false; fetchContacts(); };
});
