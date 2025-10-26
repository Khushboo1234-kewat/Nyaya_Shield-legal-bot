// Main chat functionality
async function sendQuery() {
  const queryInput = document.getElementById("queryInput");
  const responseBox = document.getElementById("responseBox");
  const query = queryInput.value.trim();
  
  if (!query) return;
  
  // Show loading state
  const originalText = responseBox.textContent;
  responseBox.textContent = "Processing your query...";
  
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message: query,
        domain: document.body.dataset.legalDomain || ''
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    responseBox.textContent = data.message || data.response || 'No response received';
  } catch (error) {
    console.error('Error:', error);
    responseBox.textContent = "An error occurred. Please try again later.";
  }
  
  // Re-enable input and focus
  queryInput.value = '';
  queryInput.focus();
}

// Add event listeners
document.addEventListener('DOMContentLoaded', function() {
  const queryInput = document.getElementById("queryInput");
  const sendButton = document.getElementById("sendButton");
  
  if (queryInput && sendButton) {
    // Handle Enter key
    queryInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        sendQuery();
      }
    });
    
    // Handle button click
    sendButton.addEventListener('click', sendQuery);
  }
});
