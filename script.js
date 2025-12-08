// Chat Application Logic

// Constants
const API_BASE_URL = '/api';

// State
let currentUser = null;
let currentSessionId = null;
let isTyping = false;

// DOM Elements
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const messagesContainer = document.getElementById('messagesContainer');
const typingIndicator = document.getElementById('typingIndicator');
const userProfile = document.getElementById('userProfile');
const userDropdown = document.getElementById('userDropdown');
const logoutBtn = document.getElementById('logoutBtn');
const endSessionBtn = document.getElementById('endSessionBtn');
const sessionModal = document.getElementById('sessionModal');
const closeModalBtn = document.querySelector('.close-modal');
const closeSessionBtn = document.getElementById('closeSessionBtn');
const summaryContent = document.getElementById('summaryContent');
const welcomeMessage = document.getElementById('welcomeMessage');
const sessionContext = document.getElementById('sessionContext');
const contextContent = document.getElementById('contextContent');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupEventListeners();
    loadSessionContext();

    // Generate new session ID if not exists
    if (!currentSessionId) {
        currentSessionId = generateUUID();
    }
});

// Authentication Check
function checkAuth() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');

    if (!token || !username) {
        window.location.href = '/login';
        return;
    }

    currentUser = { username, token };
    updateUserProfile(username);
}

function updateUserProfile(username) {
    document.getElementById('displayUsername').textContent = username;
    document.getElementById('userInitial').textContent = username.charAt(0).toUpperCase();
    document.getElementById('welcomeName').textContent = username;
}

// Event Listeners
function setupEventListeners() {
    // Message Input
    messageInput.addEventListener('input', autoResizeTextarea);
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendButton.addEventListener('click', sendMessage);

    // User Dropdown
    userProfile.addEventListener('click', (e) => {
        e.stopPropagation();
        userDropdown.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
        if (!userProfile.contains(e.target)) {
            userDropdown.classList.remove('show');
        }
    });

    // Session Management
    logoutBtn.addEventListener('click', handleLogout);
    endSessionBtn.addEventListener('click', confirmEndSession);

    // Modal
    closeModalBtn.addEventListener('click', () => sessionModal.classList.remove('show'));
    closeSessionBtn.addEventListener('click', () => {
        sessionModal.classList.remove('show');
        window.location.reload(); // Start fresh session
    });
}

// Session Context
function loadSessionContext() {
    const recentSummaries = localStorage.getItem('recent_summaries');
    if (recentSummaries) {
        try {
            const summaries = JSON.parse(recentSummaries);
            if (summaries && summaries.length > 0) {
                const lastSummary = summaries[0].summary;
                contextContent.textContent = lastSummary;
                sessionContext.style.display = 'block';
                welcomeMessage.style.display = 'none'; // Hide welcome if context exists
            }
        } catch (e) {
            console.error('Error parsing summaries:', e);
        }
    }
}

// Message Handling
async function sendMessage() {
    const content = messageInput.value.trim();
    if (!content || isTyping) return;

    // Add user message
    addMessage(content, 'user');
    messageInput.value = '';
    autoResizeTextarea();

    // Hide welcome/context
    welcomeMessage.style.display = 'none';
    sessionContext.style.display = 'none';

    // Show typing indicator
    showTyping(true);

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({
                message: content,
                session_id: currentSessionId
            })
        });

        if (response.status === 401) {
            handleLogout();
            return;
        }

        const data = await response.json();

        // Add AI response
        addMessage(data.prompt, 'counselor');

        // Check for session end triggers
        if (content.toLowerCase().match(/\b(bye|goodbye|see you|end session)\b/)) {
            setTimeout(() => confirmEndSession(), 2000);
        }

    } catch (error) {
        console.error('Error:', error);
        addMessage("I'm having trouble connecting right now. Please check your connection and try again.", 'counselor');
    } finally {
        showTyping(false);
    }
}

function addMessage(content, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    // Process markdown-like formatting (simple version)
    const formattedContent = content
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');

    messageDiv.innerHTML = formattedContent;

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

function showTyping(show) {
    isTyping = show;
    if (show) {
        typingIndicator.classList.add('active');
        messagesContainer.appendChild(typingIndicator);
        scrollToBottom();
    } else {
        typingIndicator.classList.remove('active');
        typingIndicator.remove();
    }
}

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = messageInput.scrollHeight + 'px';
}

// Session Management
async function confirmEndSession() {
    if (confirm("Are you sure you want to end this session? I'll create a summary for next time.")) {
        await endSession();
    }
}

async function endSession() {
    try {
        const response = await fetch(`${API_BASE_URL}/session/end`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({
                session_id: currentSessionId
            })
        });

        const data = await response.json();

        // Show summary modal
        summaryContent.textContent = data.summary;
        sessionModal.classList.add('show');

        // Clear current session ID
        currentSessionId = null;

    } catch (error) {
        console.error('Error ending session:', error);
    }
}

function handleLogout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('recent_summaries');
    window.location.href = '/login';
}

// Utilities
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}
