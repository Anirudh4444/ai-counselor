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
const deleteHistoryBtn = document.getElementById('deleteHistoryBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupEventListeners();
    // loadSessionContext(); // Hidden as per user request

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
    if (deleteHistoryBtn) {
        deleteHistoryBtn.addEventListener('click', handleDeleteHistory);
    }

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

// Show thinking animation
function showThinkingAnimation() {
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'message counselor thinking-message';
    thinkingDiv.id = 'thinkingAnimation';
    thinkingDiv.innerHTML = `
        <div class="thinking-content">
            <span class="thinking-text">Thinking</span>
            <span class="thinking-dots">
                <span class="dot-anim">.</span>
                <span class="dot-anim">.</span>
                <span class="dot-anim">.</span>
            </span>
        </div>
    `;
    messagesContainer.appendChild(thinkingDiv);
    scrollToBottom();
    return thinkingDiv;
}

// Remove thinking animation
function removeThinkingAnimation() {
    const thinkingEl = document.getElementById('thinkingAnimation');
    if (thinkingEl) {
        thinkingEl.remove();
    }
}

// Message Handling with Streaming
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

    // Show thinking animation
    isTyping = true;
    const thinkingEl = showThinkingAnimation();

    try {
        // Use streaming endpoint
        const response = await fetch(`${API_BASE_URL}/chat/stream`, {
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

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        // Create message element for streaming response
        let aiMessageDiv = null;
        let wordBuffer = '';
        let displayedText = '';
        let wordQueue = [];
        let isDisplaying = false;

        // Function to display words one at a time
        async function displayNextWord() {
            if (wordQueue.length === 0) {
                isDisplaying = false;
                return;
            }

            isDisplaying = true;
            const word = wordQueue.shift();
            displayedText += word;

            if (aiMessageDiv) {
                // Process markdown-like formatting
                const formattedContent = displayedText
                    .replace(/\n/g, '<br>')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>');
                aiMessageDiv.innerHTML = formattedContent;
                scrollToBottom();
            }

            // Delay between words (adjust for speed - reduced for snappier feel)
            await new Promise(resolve => setTimeout(resolve, 30));
            displayNextWord();
        }

        // Function to add words to queue
        function queueWords(text) {
            // Split by spaces but keep the spaces
            const words = text.split(/(\s+)/);
            words.forEach(word => {
                if (word) {
                    wordQueue.push(word);
                }
            });

            // Start displaying if not already
            if (!isDisplaying) {
                displayNextWord();
            }
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        switch (data.type) {
                            case 'session':
                                currentSessionId = data.session_id;
                                break;

                            case 'thinking':
                                // Update thinking animation if needed
                                break;

                            case 'start':
                                // Remove thinking, prepare for response
                                removeThinkingAnimation();
                                aiMessageDiv = document.createElement('div');
                                aiMessageDiv.className = 'message counselor streaming';
                                messagesContainer.appendChild(aiMessageDiv);
                                break;

                            case 'chunk':
                                if (aiMessageDiv && data.content) {
                                    // Queue words for display
                                    queueWords(data.content);
                                }
                                break;

                            case 'done':
                                // Wait for all words to be displayed
                                while (wordQueue.length > 0 || isDisplaying) {
                                    await new Promise(resolve => setTimeout(resolve, 50));
                                }
                                if (aiMessageDiv) {
                                    aiMessageDiv.classList.remove('streaming');
                                }
                                // Check for session end triggers
                                if (content.toLowerCase().match(/\b(bye|goodbye|see you|end session)\b/)) {
                                    setTimeout(() => confirmEndSession(), 2000);
                                }
                                break;

                            case 'error':
                                removeThinkingAnimation();
                                addMessage("I'm having trouble connecting right now. Please try again.", 'counselor');
                                console.error('Stream error:', data.content);
                                break;
                        }
                    } catch (parseError) {
                        // Ignore parse errors for incomplete JSON
                    }
                }
            }
        }

    } catch (error) {
        console.error('Error:', error);
        removeThinkingAnimation();
        addMessage("I'm having trouble connecting right now. Please check your connection and try again.", 'counselor');
    } finally {
        isTyping = false;
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

async function handleLogout() {
    if (confirm('Are you sure you want to sign out?')) {
        // Auto-save session before logout
        if (currentSessionId) {
            try {
                await fetch(`${API_BASE_URL}/session/end`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${currentUser.token}`
                    },
                    body: JSON.stringify({ session_id: currentSessionId })
                });
            } catch (error) {
                console.error('Error saving session on logout:', error);
            }
        }

        localStorage.removeItem('token');
        localStorage.removeItem('username');
        localStorage.removeItem('recent_summaries');
        window.location.href = '/login';
    }
}

async function handleDeleteHistory() {
    if (confirm('Are you sure you want to delete ALL chat history? This cannot be undone.')) {
        try {
            const response = await fetch(`${API_BASE_URL}/user/delete-history`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${currentUser.token}`
                }
            });

            if (response.ok) {
                alert('Chat history deleted successfully.');
                // Clear local storage and reload to start fresh
                localStorage.removeItem('recent_summaries');
                window.location.reload();
            } else {
                const data = await response.json();
                alert(`Error: ${data.detail || 'Failed to delete history'}`);
            }
        } catch (error) {
            console.error('Error deleting history:', error);
            alert('An error occurred while deleting history.');
        }
    }
}

// Utilities
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function scrollToBottom() { messagesContainer.scrollTop = messagesContainer.scrollHeight; }
