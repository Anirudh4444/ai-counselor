# AI Counselor - Mental Health Support Assistant 💙

An empathetic AI counselor powered by Google's Gemini API, designed to provide compassionate mental health support for depression and anxiety.

## Features

- 🧠 **Chain-of-Thought Reasoning**: Deep understanding of user emotions
- 💬 **Few-Shot Learning**: Trained with empathetic response examples
- 🎨 **Beautiful UI**: Modern glassmorphism design with smooth animations
- 📱 **Responsive**: Works on desktop, tablet, and mobile
- 🔒 **Privacy-Focused**: Session-based conversations
- ⚡ **Real-time**: Instant responses with typing indicators

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML, CSS, JavaScript
- **AI**: Google Gemini 2.5 Flash
- **Deployment**: Render.com (free tier)

## Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/ai-counselor.git
cd ai-counselor
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set environment variable**
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

5. **Run the server**
```bash
./start_server.sh
# Or manually: python app.py
```

6. **Open in browser**
```
http://localhost:8000
```

## Deployment

See [deployment_guide.md](deployment_guide.md) for detailed instructions on deploying to Render.com for free.

## Important Note

⚠️ This is an AI assistant for support, not a replacement for professional mental health care. If you're in crisis, please contact a crisis helpline immediately.

## License

MIT License - feel free to use and modify!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
