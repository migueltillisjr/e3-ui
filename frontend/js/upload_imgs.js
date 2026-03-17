function toggleImgPanel(panelId) {
    const panel = document.getElementById(panelId);
    if (!panel) return;
    if (panel.classList.contains("opacity-0")) {
      panel.classList.remove("opacity-0", "pointer-events-none");
      panel.classList.add("opacity-100");
    } else {
      panel.classList.remove("opacity-100");
      panel.classList.add("opacity-0", "pointer-events-none");
    }
  }

  async function fetchGallery() {
    const res = await fetch(`https://${window.location.hostname}:${UI_PORT}` + CLIENT_ROUTE_PREFIX + "/list_images", {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      }
    });
    const images = await res.json();
    const gallery = document.getElementById("imageGallery");
    gallery.innerHTML = "";
  
    images.forEach((url) => {
      const wrapper = document.createElement("div");
      wrapper.className = "relative border rounded overflow-hidden group flex flex-col items-center"; // Use flex to center buttons
  
      // Image element
      const img = document.createElement("img");
      img.src = url;
      img.className = "w-full h-auto";
  
      // Button container
      const buttonContainer = document.createElement("div");
      buttonContainer.className = "w-full flex justify-center space-x-4 mt-2"; // Ensure buttons are spaced out and centered
  
      // Copy URL button
      const copyBtn = document.createElement("button");
      copyBtn.textContent = "📋 Copy URL";
      copyBtn.className = "bg-white bg-opacity-20 px-4 py-2 rounded hover:bg-opacity-40";
      copyBtn.onclick = () => {
        navigator.clipboard.writeText(url);
        copyBtn.textContent = "✅ Copied!";
        setTimeout(() => (copyBtn.textContent = "📋 Copy URL"), 1000);
      };
  
      // Delete button
      const deleteBtn = document.createElement("button");
      deleteBtn.textContent = "🗑️ Delete";
      deleteBtn.className = "text-red-300 hover:text-red-600";
      deleteBtn.onclick = async () => {
        try {
          const res = await fetch(CLIENT_ROUTE_PREFIX + "/delete_image", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url }),
          });
          const result = await res.json();
          if (res.ok) {
            await fetchGallery();
          } else {
            alert(`❌ ${result.error}`);
          }
        } catch (err) {
          alert(`❌ ${err.message}`);
        }
      };
  
      // Append buttons to the button container
      buttonContainer.appendChild(copyBtn);
      buttonContainer.appendChild(deleteBtn);
  
      // Append image and button container to wrapper
      wrapper.appendChild(img);
      wrapper.appendChild(buttonContainer);
  
      // Append the wrapper to the gallery
      gallery.appendChild(wrapper);
    });
  }
  
  document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("imageUploadForm");
    const status = document.getElementById("uploadStatus");
  
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(form);
  
      try {
        loadingOverlay.style.display = 'flex';
        const res = await fetch(CLIENT_ROUTE_PREFIX + "/upload_image", {
          method: "POST",
          body: formData,
        });
        const result = await res.json();
        if (res.ok) {
          status.textContent = `✅ ${result.message}`;
          status.classList.add("text-green-600");
          await fetchGallery();
        } else {
          throw new Error(result.error);
        }
        loadingOverlay.style.display = 'none';
      } catch (err) {
        loadingOverlay.style.display = 'none';
        status.textContent = `❌ ${err.message}`;
        status.classList.add("text-red-600");

      }
    });
  
    // Load gallery on first open
    document
      .getElementById("imageUploadPanel")
      .addEventListener("transitionend", () => {
        if (!document.getElementById("imageUploadPanel").classList.contains("opacity-0")) {
          fetchGallery();
        }
      });
  });
  