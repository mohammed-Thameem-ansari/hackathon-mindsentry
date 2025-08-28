# MindSentry Nova

MindSentry Nova is an AI-powered mental health companion designed to enhance emotional well-being. It was developed as part of the Project-X Hackathon 2025.

----

## Features

### Core Functionality
- **Text Sentiment Analysis** – Analyze the emotional tone of text inputs instantly.
- **Audio Sentiment Detection** – Transcribe and analyze spoken words for emotional insights.
- **Real-Time Group Chatroom** – Connect and communicate with others in real-time using WebSocket technology.
- **Therapy Assistant** – Access immersive therapy experiences with calming sounds and visuals.
- **Privacy-Focused Design** – All analysis is performed locally to ensure maximum privacy.

### Upcoming Features
- **Audio Room** – A group audio call feature with microphone toggling and visual indicators for active users. Participants can join via a meeting link and choose between chat or audio mode.

----

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: FastAPI (Python)
- **AI Models**: Sentiment Analysis (Hugging Face / Custom), Whisper for Speech-to-Text
- **WebSocket**: Real-time communication using FastAPI WebSocket
- **Voice Recording**: MediaRecorder API
- **User Interface**: Minimalist and responsive design with a focus on user experience

---

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repo-link>
   cd MindSentry-Nova
   ```

2. **Install Dependencies**
   - Navigate to the `backend` folder:
     ```bash
     cd backend
     pip install -r requirements.txt
     ```

3. **Set Up Environment Variables**
   - Create a `.env` file in the root directory and add the following:
     ```
     CEREBRAS_API_KEY='your-api-key-here'
     ```

4. **Run the Application**
   - Start the FastAPI server:
     ```bash
     uvicorn main:app --reload
     ```
   - Access the application at `http://127.0.0.1:8000`.

---

## Usage

### Text Sentiment Analysis
1. Go to the "Analyze" section on the homepage.
2. Enter your text in the input box and click "Analyze."
3. View the sentiment and confidence score.

### Audio Sentiment Detection
1. Record or upload an audio file in the "Analyze" section.
2. The system will transcribe and analyze the audio for sentiment.

### Real-Time Group Chatroom
1. Join a meeting room by entering a nickname.
2. Chat with others in real-time or interact with the AI chatbot if you're alone.

### Therapy Assistant
1. Explore the "Therapy" section for soothing sounds and calming videos.
2. Use the AI chatbot for guided relaxation (coming soon).

---

## Architecture

### Backend
- **FastAPI**: Manages API endpoints for sentiment analysis, transcription, and WebSocket communication.
- **Hugging Face Transformers**: Used for text sentiment analysis.
- **Whisper**: Used for audio transcription.

### Frontend
- **HTML/CSS/JavaScript**: Provides a responsive and user-friendly interface.
- **WebSocket**: Enables real-time chat functionality.

### Database
- **SQLAlchemy**: Handles user data, chat logs, and sentiment analysis results.

---

## File Structure

### Backend
- `main.py`: Defines API endpoints and WebSocket functionality.
- `sentiment.py`: Handles text sentiment analysis.
- `transcription.py`: Processes audio transcription using Whisper.
- `models.py`: Defines database models.

### Frontend
- `templates/`: Contains HTML templates for the user interface.
- `static/`: Contains CSS, JavaScript, and other static assets.

---

## Contribution Guidelines

1. **Fork the Repository**
   - Create a fork of the repository on GitHub.

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Commit Changes**
   - Use conventional commit messages:
     ```
     feat: Add new feature
     fix: Resolve bug in feature
     ```

4. **Submit a Pull Request**
   - Ensure your code passes all tests and linting checks before submitting.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Support

For any issues or feature requests, please open an issue on GitHub or contact the project maintainers.
