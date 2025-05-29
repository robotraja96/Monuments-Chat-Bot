/* ---------------------------------------- */
/* /static/script.js */
// Grab elements
const sendBtn = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');
const messagesDiv = document.getElementById('messages');
const newChatBtn = document.getElementById('new-chat');

// Thread ID from template context
const threadId = "{{ thread_id }}";
let evtSource = null;

function appendMessage(text, who) {
  const div = document.createElement('div');
  div.className = `message ${who}`;
  div.textContent = text;
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function startStream(query) {
  sendBtn.disabled = true;
  evtSource = new EventSource(`/chat?thread_id=${threadId}&query=${encodeURIComponent(query)}`);

  evtSource.onmessage = function(event) {
    appendMessage(event.data, 'bot');
    // if verification succeeded, the server can send a special token or close stream
  };
  evtSource.onerror = function() {
    sendBtn.disabled = false;
    if (evtSource) { evtSource.close(); evtSource = null; }
  };
}

sendBtn.addEventListener('click', () => {
  const query = userInput.value.trim();
  if (!query) return;
  appendMessage(query, 'user');
  userInput.value = '';
  startStream(query);
});

userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendBtn.click();
});

newChatBtn.addEventListener('click', () => {
  window.location.href = '/';
});