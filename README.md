# AI Counselor Web Application

A compassionate AI counselor web application powered by Google's Gemini AI, designed to provide mental health support for depression and anxiety.

## Features

- 🤖 AI-powered counseling using Gemini 2.5 Flash
- 💬 Real-time chat interface
- 🎨 Modern, responsive UI
- 🔒 Secure API key management
- 📝 Conversation history tracking

## Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd <your-repo-name>
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:

```
GOOGLE_API_KEY=your-actual-google-api-key-here
PORT=8000
```

**Get your API key:** Visit [Google AI Studio](https://aistudio.google.com/apikey)

### 5. Run the Server

```bash
# Option 1: Using the startup script
bash start_server.sh

# Option 2: Manual start
source venv/bin/activate
python app.py
```

The server will start at `http://localhost:8000`

## Deployment

### Deploying to Render

1. Push your code to GitHub (make sure `.env` is in `.gitignore`)
2. Connect your GitHub repo to Render
3. Render will use `render.yaml` for configuration
4. **Important:** Set environment variables in Render dashboard:
   - Go to your service → Environment
   - Add `GOOGLE_API_KEY` with your actual API key

### Deploying to Heroku

```bash
heroku create your-app-name
heroku config:set GOOGLE_API_KEY=your-actual-api-key-here
git push heroku main
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Your Google Gemini API key | Yes |
| `PORT` | Server port (default: 8000) | No |

## API Endpoints

- `GET /` - Main web interface
- `POST /chat` - Send a message to the AI counselor
- `POST /reset` - Reset conversation history
- `GET /docs` - API documentation (FastAPI auto-generated)

## Security Notes

⚠️ **Never commit your `.env` file or API keys to GitHub**

- API keys are stored in environment variables
- `.env` file is gitignored
- Use `.env.example` as a template for other developers
- On production servers, set environment variables through the hosting platform's dashboard

## Project Structure

```
.
├── app.py              # FastAPI backend server
├── index.html          # Frontend HTML
├── styles.css          # Styling
├── script.js           # Frontend JavaScript
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore rules
├── render.yaml         # Render deployment config
├── Procfile            # Heroku deployment config
└── README.md           # This file
```

## Troubleshooting

### Error: "GOOGLE_API_KEY environment variable is not set"
- Make sure you created a `.env` file with your API key
- Verify the `.env` file is in the project root directory
- Check that `python-dotenv` is installed

### Error: "403 PERMISSION_DENIED - API key was reported as leaked"
- Your API key was exposed publicly and disabled by Google
- Get a new API key from [Google AI Studio](https://aistudio.google.com/apikey)
- Update your `.env` file with the new key
- Never commit API keys to GitHub

### Port Already in Use
```bash
# Find and kill the process using port 8000
lsof -ti :8000 | xargs kill -9
```

## License

MIT License - feel free to use this project for your own purposes.
