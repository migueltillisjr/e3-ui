function updatePreview() {
  preview.srcdoc = htmlInput.value;
}


// ✅ Use reusable function instead:
htmlInput.addEventListener('input', updatePreview);


document.addEventListener("DOMContentLoaded", async () => {
  try {
    const params = new URLSearchParams(window.location.search);
    const file = params.get("file") || "on_initial_login_is_no_file"; // fallback if no param

    const response = await fetch(`https://${window.location.hostname}:${UI_PORT}${SERVER_ROUTE_PREFIX}/email_designs/?file=${file}&t=${Date.now()}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache"
      }
    });


    if (file != "on_initial_login_is_no_file") {
      if (!response.ok) throw new Error("Failed to load HTML content");
      const html = await response.text();
      console.log("html::");
      console.log(html);
      const sanitizedHtml = html.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "");
            // Populate the editor textarea
      const htmlInput = document.getElementById("htmlInput");
      htmlInput.value = sanitizedHtml;

      // Load into iframe preview
      const preview = document.getElementById("preview");
      preview.srcdoc = html;
    }

  } catch (error) {
    console.error("Error loading HTML:", error);
  }
});


document.getElementById("htmlInput").addEventListener("input", (e) => {
  document.getElementById("preview").srcdoc = e.target.value;
});