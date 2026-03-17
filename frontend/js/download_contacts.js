document.addEventListener("DOMContentLoaded", () => {
    const downloadLink = document.querySelector('a[href="' + CLIENT_ROUTE_PREFIX + '/download_contacts"]');

    downloadLink.addEventListener("click", async function (e) {
      e.preventDefault(); // prevent immediate navigation

      try {

        const response = await fetch(CLIENT_ROUTE_PREFIX + "/download_contacts", {
          method: "GET",
          headers: {
            "Content-Type": "application/json"
          }
        });

        if (!response.ok) {
          throw new Error("Failed to fetch contacts.");
        }

        const text = await response.text();

        // If the file is empty or contains just a header, show alert
        if (!text.trim() || text.trim().split("\n").length <= 1) {
          alert("⚠️ No contacts found to download.");
          return;
        }

        // Otherwise, create a download link and trigger it
        const blob = new Blob([text], { type: "text/tab-separated-values" });
        const url = URL.createObjectURL(blob);
        const tempLink = document.createElement("a");
        tempLink.href = url;
        tempLink.download = "contacts.tsv";
        document.body.appendChild(tempLink);
        tempLink.click();
        document.body.removeChild(tempLink);
        URL.revokeObjectURL(url);
      } catch (err) {
        alert("⚠️ Error downloading contacts, perhaps query for contacts: " + err.message);
      }
    });
  });