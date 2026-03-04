console.log("SpeechRecognition:", window.SpeechRecognition || window.webkitSpeechRecognition);
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = "en-US";
recognition.continuous = false;
recognition.interimResults = false;

let isListening = false;

function setCalendarLink(link) {
    const linkBox = document.getElementById("linkBox");
    const input = document.getElementById("calendarLink");
    if (!linkBox || !input) return;

    if (link) {
        input.value = link;
        linkBox.style.display = "block";
    } else {
        input.value = "";
        linkBox.style.display = "none";
    }
}

function openCalendarLink() {
    const input = document.getElementById("calendarLink");
    const link = input?.value;
    if (link) window.open(link, "_blank");
}

async function copyCalendarLink() {
    const input = document.getElementById("calendarLink");
    const link = input?.value;
    if (!link) return;
    try {
        await navigator.clipboard.writeText(link);
    } catch {
        // Fallback for older browsers
        input.focus();
        input.select();
        document.execCommand("copy");
    }
}

function speak(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    speechSynthesis.speak(utterance);
}

function startListening() {
    if (isListening) {
        recognition.stop();
        isListening = false;
        return;
    }

    recognition.start();
    isListening = true;
    //speak("Hello Osama, can you hear me?");
}

recognition.onstart = function() {
    console.log("🎤 Listening...");
};

recognition.onend = function() {
    console.log("🛑 Stopped listening");
    isListening = false;
};

recognition.onerror = function(event) {
    console.error("Speech recognition error:", event.error);
    isListening = false;
};

recognition.onresult = async function(event) {
    const transcript = event.results[0][0].transcript;
    document.getElementById("output").innerText = "You said: " + transcript;

    const response = await fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            user_id: "user123",
            session_id: sessionStorage.getItem("session_id"),
            message: transcript
        })
    });

    const data = await response.json();
    setCalendarLink(data.calendar_link);
    document.getElementById("output").innerText = data.response;
    speak(data.response);
};

window.onload = async function () {
    // Get session_id from URL or sessionStorage
    const urlParams = new URLSearchParams(window.location.search);
    const sessionIdFromUrl = urlParams.get("session_id");
    let sessionId = sessionStorage.getItem("session_id");
    
    if (sessionIdFromUrl) {
        sessionId = sessionIdFromUrl;
        sessionStorage.setItem("session_id", sessionId);
    }
    
    // Check auth status
    if (sessionId) {
        const authResponse = await fetch(`/auth-status?session_id=${sessionId}`);
        const authData = await authResponse.json();
        if (authData.logged_in) {
            document.getElementById("loginBtn").style.display = "none";
            document.getElementById("status").innerText = "🟢 Authenticated";
            document.getElementById("status").style.color = "#10b981";
        }
    }
    
    // Only proceed with chat if we have a session_id
    if (sessionId) {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: "user123",
                session_id: sessionId,
                message: ""
            })
        });

        const data = await response.json();
        document.getElementById("output").innerText = data.response;
        setCalendarLink(data.calendar_link);
        speak(data.response);
    }
};