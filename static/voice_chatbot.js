const startButton = document.getElementById("start-recording");
const stopButton = document.getElementById("stop-recording");
const chatLog = document.getElementById("chat-log");
const responseDiv = document.getElementById("response");

let recognition;
let isRecording = false;

// Initialize Speech Recognition
if ("SpeechRecognition" in window || "webkitSpeechRecognition" in window) {
    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.lang = "en-US";

    // Increase timeout duration
    recognition.speechRecognitionTimeout = 10000; // 10 seconds

    recognition.onstart = () => {
        isRecording = true;
        responseDiv.textContent = "Listening...";
        startButton.disabled = true;
        stopButton.disabled = false;
        document.getElementById("waveform").style.display = "block";
    };

    recognition.onresult = async (event) => {
        const userMessage = event.results[event.results.length - 1][0].transcript.trim();
        if (userMessage) {
            addMessageToLog(userMessage, "user");
            responseDiv.textContent = "Processing...";
            await sendToChatbot(userMessage);
        }
    };

    recognition.onerror = (event) => {
        console.error("Speech Recognition Error:", event.error);
        if (event.error === "no-speech") {
            responseDiv.textContent = "No speech detected. Please try again.";
            // Automatically restart recognition
            try {
                recognition.stop();
                setTimeout(() => {
                    if (isRecording) {
                        recognition.start();
                    }
                }, 100);
            } catch (error) {
                console.error("Error restarting recognition:", error);
            }
        } else {
            responseDiv.textContent = `Error: ${event.error}. Please try again.`;
            isRecording = false;
            startButton.disabled = false;
            stopButton.disabled = true;
        }
    };

    recognition.onend = () => {
        console.log("Recognition ended");
        // Only stop if the stop button was clicked
        if (isRecording) {
            try {
                recognition.start();
            } catch (error) {
                console.error("Error restarting recognition:", error);
                isRecording = false;
                startButton.disabled = false;
                stopButton.disabled = true;
                responseDiv.textContent = "Recognition stopped. Click Start to begin again.";
            }
        } else {
            responseDiv.textContent = "Stopped listening.";
            startButton.disabled = false;
            stopButton.disabled = true;
            document.getElementById("waveform").style.display = "none";
        }
    };
} else {
    responseDiv.textContent = "Speech Recognition is not supported in this browser.";
    startButton.disabled = true;
    stopButton.disabled = true;
}

// Start Recording
startButton.addEventListener("click", () => {
    if (!isRecording) {
        try {
            recognition.start();
        } catch (error) {
            responseDiv.textContent = "Error starting recognition.";
        }
    }
});

// Stop Recording
stopButton.addEventListener("click", () => {
    if (isRecording) {
        isRecording = false; // Set this first so onend doesn't restart
        try {
            recognition.stop();
        } catch (error) {
            console.error("Error stopping recognition:", error);
        }
    }
});

// Add message to chat log
function addMessageToLog(message, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}`;
    messageDiv.textContent = message;
    chatLog.appendChild(messageDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}

// Send message to chatbot API
async function sendToChatbot(message) {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/voice-chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: message })
        });

        if (!response.ok) {
            throw new Error("Failed to connect to the chatbot API.");
        }

        const data = await response.json();
        addMessageToLog(data.response, "ai");
        responseDiv.textContent = "Ready for next input.";
    } catch (error) {
        console.error("Error:", error);
        addMessageToLog("Error: Unable to connect to the server.", "ai");
        responseDiv.textContent = "Error occurred.";
    }
}