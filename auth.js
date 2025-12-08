// Authentication Logic

// Constants
const API_BASE_URL = '/api';

// DOM Elements
const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');
const errorMessage = document.getElementById('errorMessage');

// Helper Functions
function showError(message) {
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.classList.add('visible');

        // Shake animation for card
        const card = document.querySelector('.auth-card');
        card.style.animation = 'none';
        card.offsetHeight; /* trigger reflow */
        card.style.animation = 'shake 0.5s';
    }
}

function clearError() {
    if (errorMessage) {
        errorMessage.textContent = '';
        errorMessage.classList.remove('visible');
    }
}

function setLoading(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    if (button) {
        if (isLoading) {
            button.classList.add('loading');
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }
}

// Password Strength Checker
function updatePasswordStrength(password) {
    const strengthFill = document.getElementById('strengthFill');
    const strengthText = document.getElementById('strengthText');
    const strengthContainer = document.querySelector('.password-strength');

    if (!strengthContainer || !password) {
        if (strengthContainer) strengthContainer.style.display = 'none';
        return;
    }

    strengthContainer.style.display = 'block';

    let strength = 0;
    let status = '';
    let color = '';

    // Length check
    if (password.length >= 8) strength += 25;

    // Complexity checks
    if (/[A-Z]/.test(password)) strength += 25;
    if (/[0-9]/.test(password)) strength += 25;
    if (/[^A-Za-z0-9]/.test(password)) strength += 25;

    // Determine status and color
    if (strength <= 25) {
        status = 'Weak';
        color = '#ef4444'; // Red
    } else if (strength <= 50) {
        status = 'Fair';
        color = '#f59e0b'; // Orange
    } else if (strength <= 75) {
        status = 'Good';
        color = '#3b82f6'; // Blue
    } else {
        status = 'Strong';
        color = '#10b981'; // Green
    }

    strengthFill.style.width = strength + '%';
    strengthFill.style.backgroundColor = color;
    strengthText.textContent = status;
    strengthText.style.color = color;
}

// Login Handler
async function handleLogin(e) {
    e.preventDefault();
    clearError();
    setLoading('loginButton', true);

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'Login failed');
        }

        // Store token and user info
        localStorage.setItem('token', result.access_token);
        localStorage.setItem('username', result.username);

        if (result.recent_summaries) {
            localStorage.setItem('recent_summaries', JSON.stringify(result.recent_summaries));
        }

        // Redirect to chat
        window.location.href = '/';

    } catch (error) {
        showError(error.message);
    } finally {
        setLoading('loginButton', false);
    }
}

// Signup Handler
async function handleSignup(e) {
    e.preventDefault();
    clearError();

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    // Validation
    if (data.password !== data.confirmPassword) {
        showError("Passwords do not match");
        return;
    }

    if (data.password.length < 8) {
        showError("Password must be at least 8 characters");
        return;
    }

    if (!document.getElementById('terms').checked) {
        showError("Please accept the Terms & Conditions");
        return;
    }

    setLoading('signupButton', true);

    try {
        const response = await fetch(`${API_BASE_URL}/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: data.username,
                email: data.email,
                password: data.password
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'Signup failed');
        }

        // Auto login after signup
        localStorage.setItem('token', result.access_token);
        localStorage.setItem('username', result.username);

        // Redirect to chat
        window.location.href = '/';

    } catch (error) {
        showError(error.message);
    } finally {
        setLoading('signupButton', false);
    }
}

// Add shake animation style
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
`;
document.head.appendChild(style);
