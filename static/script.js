const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
const voiceAnswerBtn = document.getElementById("voiceAnswerBtn");
const themeBtn = document.getElementById("themeBtn");

const chatMessages = document.getElementById("chatMessages");
const aiStage = document.querySelector(".ai-stage");
const aiState = document.getElementById("aiState");
const aiGreeting = document.getElementById("aiGreeting");
const aiSubtitle = document.getElementById("aiSubtitle");
const voiceStatus = document.getElementById("voiceStatus");


// =====================================
// SETTINGS
// =====================================

let voiceAnswerEnabled =
    localStorage.getItem("voiceAnswer") !== "false";

let darkMode =
    localStorage.getItem("darkMode") !== "false";


// =====================================
// THEME
// =====================================

function applyTheme() {

    if (darkMode) {

        document.body.classList.remove("light");
        themeBtn.textContent = "🌙";

    } else {

        document.body.classList.add("light");
        themeBtn.textContent = "☀️";
    }
}

themeBtn.addEventListener("click", () => {

    darkMode = !darkMode;

    localStorage.setItem(
        "darkMode",
        darkMode
    );

    applyTheme();
});

applyTheme();


// =====================================
// VOICE ANSWER BUTTON
// =====================================

function updateVoiceButton() {

    if (voiceAnswerEnabled) {

        voiceAnswerBtn.classList.add("active");
        voiceAnswerBtn.textContent = "🔊";

    } else {

        voiceAnswerBtn.classList.remove("active");
        voiceAnswerBtn.textContent = "🔇";
    }
}

voiceAnswerBtn.addEventListener("click", () => {

    voiceAnswerEnabled = !voiceAnswerEnabled;

    localStorage.setItem(
        "voiceAnswer",
        voiceAnswerEnabled
    );

    updateVoiceButton();

    if (!voiceAnswerEnabled) {
        speechSynthesis.cancel();
    }
});

updateVoiceButton();


// =====================================
// AI STATE
// =====================================

function setAIState(state) {

    aiStage.classList.remove(
        "listening",
        "thinking",
        "speaking"
    );

    if (state === "listening") {

        aiStage.classList.add("listening");

        aiState.innerHTML =
            '<span class="state-dot"></span> LISTENING';

        aiGreeting.textContent =
            "I'm listening...";

        aiSubtitle.textContent =
            "Speak your college question.";

    }

    else if (state === "thinking") {

        aiStage.classList.add("thinking");

        aiState.innerHTML =
            '<span class="state-dot"></span> THINKING';

        aiGreeting.textContent =
            "Checking college information...";

        aiSubtitle.textContent =
            "Finding the best available answer.";

    }

    else if (state === "speaking") {

        aiStage.classList.add("speaking");

        aiState.innerHTML =
            '<span class="state-dot"></span> SPEAKING';

        aiGreeting.textContent =
            "Here is your answer.";

        aiSubtitle.textContent =
            "P.R. Pote AI Assistant";

    }

    else {

        aiState.innerHTML =
            '<span class="state-dot"></span> READY TO HELP';

        aiGreeting.textContent =
            "Hello! I'm your College AI Assistant.";

        aiSubtitle.textContent =
            "Ask me anything about P.R. Pote Patil College.";
    }
}


// =====================================
// ADD MESSAGE
// =====================================

function addMessage(text, type) {

    const message = document.createElement("div");

    message.className =
        "message " +
        (type === "user" ? "user" : "bot-message");

    if (type === "user") {

        message.innerHTML = `
            <div class="bubble">
                <div class="bubble-title">YOU</div>
                ${escapeHTML(text)}
            </div>
        `;

    } else {

        message.innerHTML = `
            <div class="avatar">✦</div>

            <div class="bubble">
                <div class="bubble-title">
                    P.R. Pote AI
                </div>

                ${escapeHTML(text)}
            </div>
        `;
    }

    chatMessages.appendChild(message);

    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}


// =====================================
// SAFE HTML
// =====================================

function escapeHTML(text) {

    const div =
        document.createElement("div");

    div.textContent = text;

    return div.innerHTML
        .replace(/\n/g, "<br>");
}


// =====================================
// SEND QUESTION
// =====================================

async function sendQuestion(question = null) {

    const text =
        question || input.value.trim();

    if (!text) return;

    input.value = "";

    addMessage(text, "user");

    setAIState("thinking");

    sendBtn.disabled = true;

    try {

        const response = await fetch(
            "/api/ask",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    question: text
                })
            }
        );

        const data =
            await response.json();

        const answer =
            data.answer ||
            "I couldn't find an answer.";

        addMessage(answer, "bot");

        if (voiceAnswerEnabled) {
            speakAnswer(answer);
        } else {
            setAIState("ready");
        }

    }

    catch (error) {

        console.error(error);

        const answer =
            "Sorry, I couldn't connect to the college assistant.";

        addMessage(answer, "bot");

        setAIState("ready");
    }

    finally {

        sendBtn.disabled = false;
        input.focus();
    }
}


// =====================================
// SEND BUTTON
// =====================================

sendBtn.addEventListener(
    "click",
    () => sendQuestion()
);


// =====================================
// ENTER KEY
// =====================================

input.addEventListener(
    "keydown",
    (event) => {

        if (event.key === "Enter") {

            event.preventDefault();

            sendQuestion();
        }
    }
);


// =====================================
// QUICK BUTTONS
// =====================================

document
    .querySelectorAll(
        "[data-question]"
    )
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const question =
                    button.dataset.question;

                sendQuestion(question);
            }
        );
    });


// =====================================
// TEXT TO SPEECH
// =====================================

function speakAnswer(text) {

    if (!("speechSynthesis" in window)) {

        setAIState("ready");
        return;
    }

    speechSynthesis.cancel();

    const cleanText =
        text.replace(
            /https?:\/\/\S+/g,
            ""
        );

    const utterance =
        new SpeechSynthesisUtterance(
            cleanText
        );

    utterance.rate = 0.95;
    utterance.pitch = 1;

    utterance.onstart = () => {
        setAIState("speaking");
    };

    utterance.onend = () => {
        setAIState("ready");
    };

    utterance.onerror = () => {
        setAIState("ready");
    };

    speechSynthesis.speak(
        utterance
    );
}


// =====================================
// MICROPHONE / SPEECH TO TEXT
// =====================================

const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;

let recognition = null;
let listening = false;

if (SpeechRecognition) {

    recognition =
        new SpeechRecognition();

    recognition.lang = "en-IN";

    recognition.continuous = false;

    recognition.interimResults = true;


    recognition.onstart = () => {

        listening = true;

        micBtn.classList.add(
            "listening"
        );

        voiceStatus.textContent =
            "🔴 Listening... Speak now.";

        setAIState("listening");
    };


    recognition.onresult = (event) => {

        let transcript = "";

        for (
            let i = event.resultIndex;
            i < event.results.length;
            i++
        ) {

            transcript +=
                event.results[i][0].transcript;
        }

        input.value = transcript;

        if (
            event.results[
                event.results.length - 1
            ].isFinal
        ) {

            sendQuestion(transcript);
        }
    };


    recognition.onerror = (event) => {

        console.log(
            "Speech error:",
            event.error
        );

        stopListening();

        voiceStatus.textContent =
            "Voice input stopped.";
    };


    recognition.onend = () => {

        stopListening();
    };

} else {

    micBtn.disabled = true;

    voiceStatus.textContent =
        "Speech recognition is not supported in this browser.";
}


// =====================================
// MIC BUTTON
// =====================================

micBtn.addEventListener(
    "click",
    () => {

        if (!recognition) {

            alert(
                "Speech recognition is not supported. Please use Google Chrome."
            );

            return;
        }

        if (listening) {

            recognition.stop();

        } else {

            try {

                recognition.start();

            } catch (error) {

                console.log(error);
            }
        }
    }
);


function stopListening() {

    listening = false;

    micBtn.classList.remove(
        "listening"
    );

    voiceStatus.textContent =
        "Voice input is OFF";

    setAIState("ready");
}


// =====================================
// INITIAL
// =====================================

setAIState("ready");

input.focus();
