const userGrid = document.getElementById("user-grid");
const toggleMicButton = document.getElementById("toggle-mic");
const debugLog = document.getElementById("debug-log");
const chatbotPrompt = document.getElementById("chatbot-prompt");
const chatWithBotButton = document.getElementById("chat-with-bot");
const stayHereButton = document.getElementById("stay-here");

let localStream = null;
let peers = {};
let isMicOn = false;
let signalingSocket = null;
let username = prompt("Enter your name to join the audio room:");

// Connect to signaling server
function connectToSignalingServer() {
    signalingSocket = new WebSocket("ws://127.0.0.1:8000/ws/audio-room");

    signalingSocket.onopen = () => {
        log("Connected to the room.");
        signalingSocket.send(JSON.stringify({ type: "join", username }));
    };

    signalingSocket.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "join") {
            addUserToGrid(data.username);
        } else if (data.type === "leave") {
            removeUserFromGrid(data.username);
        } else if (data.type === "offer") {
            await handleOffer(data.offer, data.sender);
        } else if (data.type === "answer") {
            await handleAnswer(data.answer, data.sender);
        } else if (data.type === "ice-candidate") {
            await handleIceCandidate(data.candidate, data.sender);
        } else if (data.type === "system" && data.showAiOption) {
            chatbotPrompt.classList.remove("hidden");
        }
    };

    signalingSocket.onclose = () => log("Disconnected from the room.");
}

// Add user to the grid
function addUserToGrid(username) {
    if (document.getElementById(`user-${username}`)) return; // Avoid duplicates

    const userDiv = document.createElement("div");
    userDiv.id = `user-${username}`;
    userDiv.className = "flex flex-col items-center";
    userDiv.innerHTML = `
        <div class="avatar">${username[0].toUpperCase()}</div>
        <p class="mt-2">${username}</p>
    `;
    userGrid.appendChild(userDiv);
}

// Remove user from the grid
function removeUserFromGrid(username) {
    const userDiv = document.getElementById(`user-${username}`);
    if (userDiv) userDiv.remove();
}

// Toggle microphone
toggleMicButton.addEventListener("click", async () => {
    if (!localStream) {
        localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        broadcastStream();
    }

    isMicOn = !isMicOn;
    localStream.getAudioTracks()[0].enabled = isMicOn;
    toggleMicButton.textContent = isMicOn ? "Microphone On" : "Microphone Off";
});

// Handle chatbot prompt actions
chatWithBotButton.addEventListener("click", () => {
    window.location.href = "/ai-chat";
});

stayHereButton.addEventListener("click", () => {
    chatbotPrompt.classList.add("hidden");
});

// Broadcast local stream to peers
function broadcastStream() {
    Object.values(peers).forEach(peer => {
        localStream.getTracks().forEach(track => peer.addTrack(track, localStream));
    });
}

// Handle WebRTC offer
async function handleOffer(offer, sender) {
    const peerConnection = createPeerConnection(sender);
    await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);
    signalingSocket.send(JSON.stringify({ type: "answer", answer, sender: username, receiver: sender }));
}

// Handle WebRTC answer
async function handleAnswer(answer, sender) {
    const peerConnection = peers[sender];
    if (peerConnection) {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
    }
}

// Handle ICE candidate
async function handleIceCandidate(candidate, sender) {
    const peerConnection = peers[sender];
    if (peerConnection) {
        await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
    }
}

// Create a new peer connection
function createPeerConnection(peerId) {
    const peerConnection = new RTCPeerConnection();
    peers[peerId] = peerConnection;

    peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            signalingSocket.send(JSON.stringify({ type: "ice-candidate", candidate: event.candidate, sender: username, receiver: peerId }));
        }
    };

    peerConnection.ontrack = (event) => {
        const remoteAudio = new Audio();
        remoteAudio.srcObject = event.streams[0];
        remoteAudio.play();
    };

    return peerConnection;
}

// Log messages for debugging
function log(message) {
    debugLog.innerHTML += `<p>${message}</p>`;
}

// Connect to signaling server on page load
connectToSignalingServer();
