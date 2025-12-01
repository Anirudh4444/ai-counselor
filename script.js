// Generate unique session ID
const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

// DOM elements
const welcomeMessage = document.getElementById('welcomeMessage');
const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const typingIndicator = document.getElementById('typingIndicator');
const charCount = document.getElementById('charCount');

// Auto-resize textarea
userInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';

    // Update character count
    charCount.textContent = this.value.length;

    // Enable/disable send button
    sendButton.disabled = this.value.trim().length === 0;
});

// Send message on Enter (Shift+Enter for new line)
userInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Start chat
function startChat() {
    welcomeMessage.style.display = 'none';
    addMessage('counselor', "Hello! I'm here to listen and support you. What's on your mind today?");
    userInput.focus();
}

// Add message to chat
function addMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'counselor' ? '💙' : '👤';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom smoothly
    setTimeout(() => {
        messagesContainer.parentElement.scrollTo({
            top: messagesContainer.parentElement.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
}

// Show/hide typing indicator
function setTyping(isTyping) {
    if (isTyping) {
        typingIndicator.classList.add('active');
        setTimeout(() => {
            messagesContainer.parentElement.scrollTo({
                top: messagesContainer.parentElement.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);
    } else {
        typingIndicator.classList.remove('active');
    }
}

// Send message to backend
async function sendMessage() {
    const message = userInput.value.trim();

    if (!message) return;

    // Add user message
    addMessage('user', message);

    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';
    charCount.textContent = '0';
    sendButton.disabled = true;

    // Show typing indicator
    setTyping(true);

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();

        // Hide typing indicator
        setTyping(false);

        // Add counselor response
        addMessage('counselor', data.response);

    } catch (error) {
        setTyping(false);
        addMessage('counselor', error);
        console.error('Error:', error);
    }

    userInput.focus();
}

// Reset conversation
async function resetConversation() {
    if (!confirm('Are you sure you want to start a new conversation? This will clear the current chat history.')) {
        return;
    }

    try {
        await fetch('/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });
    } catch (error) {
        console.error('Error resetting conversation:', error);
    }

    // Clear messages
    messagesContainer.innerHTML = '';

    // Show welcome message
    welcomeMessage.style.display = 'block';

    // Reset input
    userInput.value = '';
    userInput.style.height = 'auto';
    charCount.textContent = '0';
    sendButton.disabled = true;
}

// Focus input on load
window.addEventListener('load', () => {
    userInput.focus();
});
