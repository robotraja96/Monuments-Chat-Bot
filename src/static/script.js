/* /static/script.js */

// Grab elements
const sendBtn = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');
const messagesDiv = document.getElementById('messages');
const newChatBtn = document.getElementById('new-chat');
const chatContainer = document.getElementById('chat-container');

// Get thread ID from data attribute - THIS IS THE FIX
const threadId = chatContainer.dataset.threadId;
let evtSource = null;
let sessionActive = true;

// Debug log to verify thread ID
console.log('Thread ID:', threadId);

// Check session status periodically
function checkSessionStatus() {
  fetch(`/session-status/${threadId}`)
    .then(response => response.json())
    .then(data => {
      if (!data.session_active) {
        disableChat("Your session has ended. Please start a new chat.");
      }
    })
    .catch(error => {
      console.error('Error checking session status:', error);
    });
}

function appendMessage(text, who) {
  const div = document.createElement('div');
  div.className = `message ${who}`;
  div.textContent = text;
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function disableChat(message) {
  sessionActive = false;
  sendBtn.disabled = true;
  userInput.disabled = true;
  userInput.placeholder = "Session ended - Click 'New Chat' to continue";
  
  if (message) {
    appendMessage(message, 'bot');
  }
  
  // Close any active EventSource
  if (evtSource) {
    evtSource.close();
    evtSource = null;
  }
}

function startStream(query) {
  if (!sessionActive) {
    appendMessage("Session has ended. Please start a new chat.", 'bot');
    return;
  }
  
  sendBtn.disabled = true;
  evtSource = new EventSource(`/chat?thread_id=${threadId}&query=${encodeURIComponent(query)}`);

  evtSource.onmessage = function(event) {
    // Check for session termination signal
    if (event.data === '__SESSION_TERMINATED__') {
      disableChat("✅ Email verification successful! Your session has ended. Click 'New Chat' to continue asking about monuments.");
      return;
    }
    
    appendMessage(event.data, 'bot');
  };
  
  evtSource.onopen = function() {
    console.log('Connection opened');
  };
  
  evtSource.onerror = function(event) {
    console.error('EventSource error:', event);
    sendBtn.disabled = false;
    
    if (evtSource) {
      evtSource.close();
      evtSource = null;
    }
    
    // Check if it's a session termination
    if (event.target.readyState === EventSource.CLOSED) {
      checkSessionStatus();
    }
  };
  
  // Re-enable send button after a delay (in case stream ends normally)
  setTimeout(() => {
    if (sessionActive) {
      sendBtn.disabled = false;
    }
  }, 1000);
}

function sendMessage() {
  const query = userInput.value.trim();
  if (!query || !sessionActive) return;
  
  appendMessage(query, 'user');
  userInput.value = '';
  startStream(query);
}

// Event listeners
sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && sessionActive) {
    sendMessage();
  }
});

newChatBtn.addEventListener('click', () => {
  // Clean up current session
  fetch(`/session/${threadId}`, { method: 'DELETE' })
    .then(() => {
      window.location.href = '/';
    })
    .catch(() => {
      // Even if cleanup fails, redirect to new chat
      window.location.href = '/';
    });
});

// Initialize
document.addEventListener('DOMContentLoaded', function() {
  appendMessage("👋 Welcome! I'm your Historical Monuments assistant. To get started, please provide your email address for verification.", 'bot');
  
  // Check session status every 30 seconds
  setInterval(checkSessionStatus, 30000);
});

// Handle page unload
window.addEventListener('beforeunload', function() {
  if (evtSource) {
    evtSource.close();
  }
});