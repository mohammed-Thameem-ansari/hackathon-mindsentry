/*
File: scripts.js
Purpose: Provides frontend functionality for sentiment analysis, audio transcription, and WebSocket chat.

Flow:
1. Sentiment Analysis:
   - Text input is sent to the /analyze endpoint in main.py.
   - Displays the sentiment result.

2. Audio Transcription:
   - Records or uploads audio.
   - Sends the audio to the /transcribe endpoint in main.py.
   - Displays the transcription and sentiment result.

3. WebSocket Chat:
   - Connects to the WebSocket endpoint (/ws/{room_id}) in main.py.
   - Sends and receives messages in real-time.
*/

async function analyzeText() {
    const text = document.getElementById("text-input").value;
    const spinner = document.getElementById("spinner");
    const resultEl = document.getElementById("result");

    spinner.style.display = "block";
    resultEl.innerText = "";

    try {
        const response = await fetch("http://127.0.0.1:8000/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });

        if (!response.ok) {
            throw new Error("Failed to analyze text.");
        }

        const data = await response.json();
        resultEl.innerText = `Sentiment: ${data.sentiment.toUpperCase()} (Confidence: ${data.confidence})`;
    } catch (error) {
        resultEl.innerText = "Error: Unable to analyze text.";
        console.error(error);
    } finally {
        spinner.style.display = "none";
    }
}

let mediaRecorder;
let audioChunks = [];
let isRecording = false;

async function toggleRecording() {
    const recordBtn = document.getElementById("record-btn");
    const spinner = document.getElementById("spinner");
    const resultEl = document.getElementById("result");

    try {
        if (!isRecording) {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                spinner.style.display = "block";
                resultEl.innerText = "Transcribing your speech...";

                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append("file", audioBlob, "voice_input.webm");

                try {
                    const response = await fetch("http://127.0.0.1:8000/transcribe/", {
                        method: "POST",
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error("Failed to transcribe audio.");
                    }

                    const data = await response.json();
                    console.log("Backend response:", data); // Debugging log

                    // Ensure the transcription field exists
                    const transcript = data.transcription || "No transcription available.";
                    console.log("Transcript:", transcript); // Log the transcript for debugging

                    // Debugging logs for DOM elements
                    const textInputEl = document.getElementById("text-input");
                    const resultEl = document.getElementById("result");
                    const transcribe_text = document.getElementById("trans_text");
                    console.log("Text Input Element:", textInputEl);
                    console.log("Result Element:", resultEl);
                    
                    // Update the UI
                    if (textInputEl) {
                        textInputEl.value = transcript;
                    } else {
                        console.error("Text input element not found.");
                    }
                    
                    if (transcribe_text) {
                        transcribe_text.innerText = `You said: "${transcript}"`;
                    } else {
                        console.error("Result element not found.");
                    }
                    
                    console.log("Transcribe Text:", transcribe_text);
                    
                    // Handle sentiment if available
                    
                    if (data.sentiment) {
                        console.log("Sentiment:", data.sentiment);
                        resultEl.innerText += `\nSentiment: ${data.sentiment.sentiment.toUpperCase()} (Confidence: ${data.sentiment.confidence})`;
                    } else {
                        console.warn("Sentiment data not found in the response.");
                    }

                    analyzeText();
                } catch (error) {
                    resultEl.innerText = "Error: Unable to transcribe audio.";
                    console.error(error);
                } finally {
                    spinner.style.display = "none";
                }

                audioChunks = [];
            };

            audioChunks = [];
            mediaRecorder.start();
            recordBtn.innerText = "🛑 Stop Recording";
            isRecording = true;
        } else {
            mediaRecorder.stop();
            isRecording = false;
            recordBtn.innerText = "🎙 Start Recording";
        }
    } catch (error) {
        alert("Error accessing microphone. Please check permissions.");
        console.error(error);
    }
}

async function uploadAudio() {
    const fileInput = document.getElementById("audio-input");
    const spinner = document.getElementById("spinner");
    const resultEl = document.getElementById("result");

    if (fileInput.files.length === 0) {
        alert("Please select an audio file.");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    spinner.style.display = "block";
    resultEl.innerText = "Transcribing audio...";

    try {
        const response = await fetch("http://127.0.0.1:8000/transcribe/", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Failed to transcribe audio.");
        }

        const data = await response.json();
        console.log("Backend response:", data); // Debugging log
        // Ensure the transcription field exists
        const transcript = data.transcription || "No transcription available.";

        document.getElementById("text-input").value = transcript;
        resultEl.innerText = `You said: "${transcript}"`;

        analyzeText();
    } catch (error) {
        resultEl.innerText = "Error: Unable to transcribe audio.";
        console.error(error);
    } finally {
        spinner.style.display = "none";
    }
}
