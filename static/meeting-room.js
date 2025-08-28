/*
File: meeting-room.js
Purpose: Handles WebSocket communication for the meeting room.

Flow:
- Connects to the WebSocket endpoint (/ws/{room_id}) in main.py.
- Sends and receives messages in real-time.
*/

let socket;
let nickname;

function setNickname() {
    const nicknameInput = document.getElementById("nickname-input");
    nickname = nicknameInput.value.trim();

    if (!nickname) {
        alert("Please enter a nickname.");
        return;
    }

    document.getElementById("nickname-section").style.display = "none";
    document.getElementById("chat-section").style.display = "block";

    connectToRoom();
}

function connectToRoom() {
    const urlParams = new URLSearchParams(window.location.search);
    let roomId = urlParams.get("room_id") || "general"; // Default to "general" if no room ID is provided

    document.getElementById("room-info").innerText = `You are in room: ${roomId}`;
    socket = new WebSocket(`ws://127.0.0.1:8000/ws/${roomId}`);

    // Debugging log to confirm socket initialization
    console.log("Connecting to WebSocket...");

    socket.onopen = () => {
        console.log("WebSocket connection established.");
        socket.send(nickname);
        const messages = document.getElementById("messages");
        const messageElement = document.createElement("div");
        messageElement.className = "system-message";
        messageElement.style.textAlign = "center"; // Center-align the message
        messageElement.innerText = "Connected to the room.";
        messages.appendChild(messageElement); // Ensure the message is appended to the chatbox
        messages.scrollTop = messages.scrollHeight; // Scroll to the latest message
    };

    socket.onmessage = (event) => {
        console.log("Message received:", event.data); // Debugging log
        const data = JSON.parse(event.data);
        const messages = document.getElementById("messages");
        const messageElement = document.createElement("div");

        if (data.type === "message") {
            // Ignore messages sent by the current user
            if (data.nickname === nickname) return;

            // Append all received messages to the chatbox
            messageElement.className = data.isAI ? "message ai" : "message"; // Use "ai" class for AI messages
            const senderSpan = document.createElement("span");
            senderSpan.style.color = data.color;
            senderSpan.style.fontWeight = "bold";
            senderSpan.innerText = data.nickname;

            const messageSpan = document.createElement("span");
            messageSpan.innerText = `: ${data.message}`;

            messageElement.appendChild(senderSpan);
            messageElement.appendChild(messageSpan);
            messages.appendChild(messageElement);
            messages.scrollTop = messages.scrollHeight; // Scroll to the latest message
        } else if (data.type === "join" || data.type === "leave") {
            if (data.nickname === nickname && data.type === "join") return; // Prevent duplicate join message for the current user
            messageElement.className = "system-message";
            messageElement.style.textAlign = "center"; // Center-align the message
            messageElement.innerText = data.type === "join"
                ? `🟢 ${data.nickname} joined the room.`
                : `🔴 ${data.nickname} left the room.`;

            messages.appendChild(messageElement);
            messages.scrollTop = messages.scrollHeight;

            // Show prompt if only one user is present
            if (data.isAlone) {
                const chatbotPrompt = document.getElementById("chatbot-prompt");
                chatbotPrompt.style.display = "block"; // Show the chatbot prompt
            }
        } else if (data.type === "system" && data.showAiOption) {
            // Handle system message with AI chat option
            const chatbotPrompt = document.getElementById("chatbot-prompt");
            chatbotPrompt.style.display = "block";
        }
    };

    socket.onclose = () => {
        console.log("WebSocket connection closed.");
        alert("Disconnected from the room.");
        window.location.href = "/";
    };

    socket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
}

function sendMessage() {
    const messageInput = document.getElementById("message-input");
    const message = messageInput.value.trim();
    if (message && socket) {
        // Show the user's message in the chatbox
        const messages = document.getElementById("messages");
        const messageElement = document.createElement("div");
        messageElement.className = "message user"; // Ensure it's styled as a user message
        messageElement.innerText = message;
        messages.appendChild(messageElement);

        // Send the message to the server
        socket.send(message);
        messageInput.value = ""; // Clear the input field
        messages.scrollTop = messages.scrollHeight; // Scroll to the latest message
    }
}

function leaveRoom() {
    if (socket) {
        socket.close();
    }
}

function redirectToAiChat() {
    window.location.href = "/ai-chat";
}

function stayInRoom() {
    const aiStatus = document.getElementById("ai-status");
    aiStatus.style.display = "none";
}
function redirectToNewAudioRoom() {
    const username = prompt("Enter your name to join the audio room:");
    if (!username) {
        alert("Name is required to join the audio room.");
        return;
    }

    const socket = new WebSocket("ws://127.0.0.1:8000/ws/audio-room");

    socket.onopen = () => {
        console.log("Connected to the audio room WebSocket.");
        socket.send(JSON.stringify({ type: "join", username }));
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "join") {
            console.log(`${data.username} joined the audio room.`);
        } else if (data.type === "leave") {
            console.log(`${data.username} left the audio room.`);
        } else if (data.type === "system") {
            console.log(`System message: ${data.message}`);
        }
    };

    socket.onclose = () => {
        console.log("Disconnected from the audio room WebSocket.");
    };

    socket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
}
