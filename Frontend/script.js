// ---------- Theme toggle (dark/light) ----------
const themeToggle = document.getElementById("themeToggle");
const htmlEl = document.documentElement;

const savedTheme = localStorage.getItem("voltassist-theme") || "dark";
htmlEl.setAttribute("data-theme", savedTheme);

themeToggle.addEventListener("click", () => {
  const current = htmlEl.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  htmlEl.setAttribute("data-theme", next);
  localStorage.setItem("voltassist-theme", next);
});

// ---------- Chat elements ----------
const chatBox = document.getElementById("chatBox");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const emptyState = document.getElementById("emptyState");

const STREAM_URL = "http://127.0.0.1:8000/ask/stream";

let conversationHistory = [];

// ---------- Helpers ----------
function hideEmptyState() {
  if (emptyState) emptyState.remove();
}

function appendMessage(text, sender) {
  if (sender === "user") userHasScrolledUp = false; 
   const msg = document.createElement("div");
  msg.className = `message ${sender}`;
  const p = document.createElement("p");
  p.textContent = text;
  msg.appendChild(p);
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight; 
}

function setLoading(isLoading) {
  sendBtn.disabled = isLoading;
  userInput.disabled = isLoading;
}


let userHasScrolledUp = false;

function isNearBottom() {
  const threshold = 80;
  return chatBox.scrollHeight - chatBox.scrollTop - chatBox.clientHeight < threshold;
}

chatBox.addEventListener("scroll", () => {
  userHasScrolledUp = !isNearBottom();
}, { passive: true });

function smartScroll() {
  if (!userHasScrolledUp) {
    chatBox.scrollTop = chatBox.scrollHeight;
  }
}

// ---------- Send message + streaming ----------
async function sendMessage() {
  const question = userInput.value.trim();
  if (!question) return;

  hideEmptyState();
  appendMessage(question, "user");
  userInput.value = "";
  setLoading(true);

  const typingMsg = document.createElement("div");
  typingMsg.className = "message bot typing-msg";
  typingMsg.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
  chatBox.appendChild(typingMsg);
  smartScroll();

  let botMsgEl = null;
  let botP = null;
  let displayedText = "";
  let pendingText = "";
  let streamDone = false;

  const typeInterval = setInterval(() => {
    if (pendingText.length > 0) {
      if (!botMsgEl) {
        typingMsg.remove(); 
        botMsgEl = document.createElement("div");
        botMsgEl.className = "message bot";
        botP = document.createElement("p");
        botMsgEl.appendChild(botP);
        chatBox.appendChild(botMsgEl);
      }
      const take = pendingText.slice(0, 2); 
      pendingText = pendingText.slice(2);
      displayedText += take;
      botP.textContent = displayedText;
      smartScroll();
    } else if (streamDone) {
      clearInterval(typeInterval);
      conversationHistory.push({ role: "user", content: question });
      conversationHistory.push({ role: "assistant", content: displayedText });
      if (conversationHistory.length > 12) {
        conversationHistory = conversationHistory.slice(-12);
      }
      setLoading(false);
      userInput.focus();
    }
  }, 18); 

  try {
    const response = await fetch(STREAM_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: question, history: conversationHistory })
    });

    if (!response.ok || !response.body) {
      throw new Error(`Server responded with ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      pendingText += decoder.decode(value, { stream: true });
    }
    streamDone = true;

  } catch (error) {
    console.error("VoltAssist error:", error);
    clearInterval(typeInterval);
    typingMsg.remove();
    if (!botMsgEl) {
      botMsgEl = document.createElement("div");
      botMsgEl.className = "message bot";
      botP = document.createElement("p");
      botMsgEl.appendChild(botP);
      chatBox.appendChild(botMsgEl);
    }
    botP.textContent = "Sorry, I couldn't reach the server right now. Please make sure the backend is running and try again.";
    setLoading(false);
    userInput.focus();
  }
}

sendBtn.addEventListener("click", sendMessage);

userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    sendMessage();
  }
});

// ---------- Mobile: intro screen <-> chat screen ----------
const startChatBtn = document.getElementById("startChatBtn");
const backBtn = document.getElementById("backBtn");

if (startChatBtn) {
  startChatBtn.addEventListener("click", () => {
    document.body.classList.add("mobile-chat-active");
  });
}

if (backBtn) {
  backBtn.addEventListener("click", () => {
    document.body.classList.remove("mobile-chat-active");
  });
}