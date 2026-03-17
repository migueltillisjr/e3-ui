function updatePreview() {
  preview.srcdoc = htmlInput.value;
}

async function handleRequestStatus(response) {
  try {
    // Show browser-native alert
    if (response.includes('<@AiResponse:SUCCESS')) {
      response = response.replace('<@AiResponse:SUCCESS@>', '');
      alert("✅ Success:\n" + response);
    } else {
      response = response.replace('<@AiResponse:ERROR@>', '');
      alert("❌ Error:\n" + response);
    }
  } catch (err) {
    alert("⚠️ Unexpected error:\n" + err);
  }
}

htmlInput.addEventListener('input', updatePreview);

    // AI
        document.addEventListener('DOMContentLoaded', () => {
            const htmlInput = document.getElementById('htmlInput');
            const contextMenu = document.getElementById('contextMenu');
            const aiPromptBtn = document.getElementById('aiPromptBtn');
            const llmModal = document.getElementById('llmModal');
            const llmInput = document.getElementById('llmInput');
            const sendPromptBtn = document.getElementById('sendPromptBtn');
        
            let selectedHTML = '';
            let selectionStart = 0;
            let selectionEnd = 0;
        
            llmInput.addEventListener('keydown', (e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault(); // prevent newline
                sendPromptBtn.click();
              }
            });
                        
            // Show context menu on right-click
            htmlInput.addEventListener('contextmenu', (e) => {
              e.preventDefault();
        
              selectionStart = htmlInput.selectionStart;
              selectionEnd = htmlInput.selectionEnd;
              selectedHTML = htmlInput.value.substring(selectionStart, selectionEnd).trim();
        
            //   if (!selectedHTML) return;
        
              contextMenu.style.top = `${e.pageY}px`;
              contextMenu.style.left = `${e.pageX}px`;
              contextMenu.style.display = 'block';
            });
        
            // Hide context menu
            document.addEventListener('click', () => {
              contextMenu.style.display = 'none';
            });
        
            // Show LLM modal
            aiPromptBtn.addEventListener('click', () => {
              llmInput.value = '';
              llmModal.style.display = 'block';
              contextMenu.style.display = 'none';
            });
        
            sendPromptBtn.addEventListener('click', async () => {
          const userPrompt = llmInput.value.trim();
        //   if (!userPrompt || !selectedHTML) return;
        
          if (!userPrompt) return;
        
          const combined = `User Prompt:\n${userPrompt}\n\nContext:\n${selectedHTML}`;
        
          const loadingOverlay = document.getElementById('loadingOverlay');
          loadingOverlay.style.display = 'flex';
         // Run Ai Agent and get response
          try {
                await new Promise(resolve => setTimeout(resolve, 2000));
                const response = await fetch(CLIENT_ROUTE_PREFIX + '/ai_agent', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ message: combined })
                });
                const data = await response.json();
                data.response = data.response.replace(/```html/g, '').replace(/```/g, '');
                if (data.response.includes('<@AiResponse:')) {
                  handleRequestStatus(data.response);
                };                
                console.log("AI Response:", data.response);
                console.log("Data:", data);
            // Simulate 2-second delay (mocking LLM response time)
            // await new Promise(resolve => setTimeout(resolve, 2000));
            // var mockResponse = "";
            // console.log(selectedHTML.length);
        
            // If text is selected.
            // if (selectedHTML.length != 0) {
            //     mockResponse = `<!-- AI-Suggested Update -->\n${selectedHTML.toUpperCase()}`;
            // }
        
            // // If text is not select, which equals an action
            // if (selectedHTML.length == 0) {
            //     mockResponse = `<!-- AI Action -->\n${selectedHTML.toUpperCase()}`;
            // }
        
            // Insert the AI response into the HTML input
            // Only if not a non view related response
            if (!data.response.includes('<@AiResponse:')) {
            const before = htmlInput.value.substring(0, selectionStart);
            const after = htmlInput.value.substring(selectionEnd);
            htmlInput.value = "";
            htmlInput.value = before + data.response + after;
            updatePreview();
            refreshIframe();

              if (data.response) {
                htmlInput.setSelectionRange(
                  selectionStart,
                  selectionStart + data.response.length
                );
            }}
            
          } catch (err) {
            console.error('Error submitting or inserting:', err);
          }
        
          loadingOverlay.style.display = 'none';
          llmModal.style.display = 'none';
        });
        
          });

          const closeLlmModal = document.getElementById('closeLlmModal');
          if (closeLlmModal) {
            closeLlmModal.addEventListener('click', () => {
              llmModal.style.display = 'none';
            });
          }
          


