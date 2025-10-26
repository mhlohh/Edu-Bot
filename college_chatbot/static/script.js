// 🌐 Toggle Chat Popup
function toggleChat() {
  const popup = document.getElementById("chat-popup");
  popup.classList.toggle("show");
}

// 🧠 Text-to-Speech (Bot Voice Reply)
function speak(text) {
  if (!window.speechSynthesis) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-IN";
  u.rate = 1;
  u.pitch = 1;
  speechSynthesis.speak(u);
}

// 📤 Send Message to Backend + Typing Animation
async function sendMessage() {
  const input = document.getElementById("user-input");
  const message = input.value.trim();
  const chatBox = document.getElementById("chat-box");

  if (message === "") return;

  // 🧑‍💻 Add user message
  const userMessage = document.createElement("div");
  userMessage.classList.add("user-message");
  userMessage.innerText = message;
  chatBox.appendChild(userMessage);
  input.value = "";
  chatBox.scrollTop = chatBox.scrollHeight;

  // 🤖 Typing Indicator
  const typingIndicator = document.createElement("div");
  typingIndicator.classList.add("bot-message");
  typingIndicator.setAttribute("id", "typing");
  typingIndicator.innerHTML = "<span class='dots'>🤖 Typing</span>";
  chatBox.appendChild(typingIndicator);
  chatBox.scrollTop = chatBox.scrollHeight;

  // 📡 Call Flask Backend
  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message })
    });

    const data = await response.json();

    // 🧹 Remove typing indicator
    document.getElementById("typing").remove();

    // 💬 Show bot response
    const botMessage = document.createElement("div");
    botMessage.classList.add("bot-message");
    botMessage.innerText = data.response;
    chatBox.appendChild(botMessage);

    // 🧠 Try to parse filters from user query
    autoFillFilters(message);

    // 🔊 Speak bot response
    speak(data.response);

  } catch (error) {
    console.error("Error:", error);
    document.getElementById("typing").remove();
    const errorMsg = document.createElement("div");
    errorMsg.classList.add("bot-message");
    errorMsg.innerText = "⚠️ Something went wrong. Try again.";
    chatBox.appendChild(errorMsg);
  }
}

// 🧠 Auto-Fill Filters from AI Query
function autoFillFilters(userMessage) {
  // 🔎 Detect location
  const locations = ["Kerala", "Delhi", "Bangalore", "Tamil Nadu", "Coimbatore", "Kochi", "Chennai"];
  const foundLocation = locations.find(loc => userMessage.toLowerCase().includes(loc.toLowerCase()));
  if (foundLocation) {
    document.getElementById("location-filter").value = foundLocation;
  }

  // 📚 Detect course
  const courses = ["B.Tech", "BSc", "BA", "MBA", "BCom", "M.Tech", "PhD", "MBBS"];
  const foundCourse = courses.find(c => userMessage.toLowerCase().includes(c.toLowerCase()));
  if (foundCourse) {
    document.getElementById("course-filter").value = foundCourse;
  }

  // 💸 Detect budget (₹)
  const feeMatch = userMessage.match(/(\d{2,7})/);
  if (feeMatch) {
    document.getElementById("max-fee").value = feeMatch[1];
  }

  // ✅ Trigger the filter function
  filterColleges();
}

// 🎙️ Voice Input (Speech-to-Text)
function startVoice() {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  recognition.lang = "en-IN";
  recognition.start();
  recognition.onresult = function (event) {
    const transcript = event.results[0][0].transcript;
    document.getElementById("user-input").value = transcript;
  };
}

// 🧠 Quick Replies
function quickAsk(text) {
  document.getElementById("user-input").value = text;
  sendMessage();
  autoFillFilters(text);
}

// 🌟 Scroll Animation Trigger
document.addEventListener("scroll", () => {
  const elements = document.querySelectorAll(".fade-in, .slide-in-left, .slide-in-right");
  const triggerBottom = window.innerHeight * 0.85;

  elements.forEach((el) => {
    const boxTop = el.getBoundingClientRect().top;
    if (boxTop < triggerBottom) {
      el.classList.add("show");
    }
  });
});

// 📩 Enter Key Submit
document.getElementById("user-input").addEventListener("keypress", function (e) {
  if (e.key === "Enter") {
    sendMessage();
  }
});

// 📊 Filter Event Listeners
document.getElementById("search").addEventListener("input", filterColleges);
document.getElementById("course-filter").addEventListener("change", filterColleges);
document.getElementById("location-filter").addEventListener("change", filterColleges);
document.getElementById("max-fee").addEventListener("input", filterColleges);

// 🏛️ Filter Function
function filterColleges() {
  let search = document.getElementById("search").value.toLowerCase();
  let course = document.getElementById("course-filter").value;
  let location = document.getElementById("location-filter").value;
  let maxFee = parseInt(document.getElementById("max-fee").value);

  document.querySelectorAll(".college-card").forEach(card => {
    let name = card.querySelector("h3").textContent.toLowerCase();
    let text = card.textContent.toLowerCase();
    let feeText = card.querySelector("p:nth-child(4)")?.textContent || "0";
    let fee = parseInt(feeText.replace(/\D/g, "") || "0");

    let matches = (!search || name.includes(search)) &&
                  (!course || text.includes(course.toLowerCase())) &&
                  (!location || text.includes(location.toLowerCase())) &&
                  (!maxFee || fee <= maxFee);

    card.style.display = matches ? "block" : "none";
  });
}

// 📜 Modal logic
function showDetails(collegeId) {
  fetch(`/college/${collegeId}`)
    .then(res => res.json())
    .then(data => {
      const modalBody = document.getElementById("modal-body");
      modalBody.innerHTML = `
        <h2>${data.name}</h2>
        <p>📍 ${data.city}, ${data.state}</p>
        <p>📚 Courses: ${data.courses.join(", ")}</p>
        <p>💸 Fees: ₹${data.fees}/year</p>
        <a href="${data.website}" target="_blank">🌐 Visit Website</a>
      `;
      document.getElementById("collegeModal").classList.remove("hidden");
    });
}

function closeModal() {
  document.getElementById("collegeModal").classList.add("hidden");
}
function toggleChat() {
  const popup = document.getElementById("chat-popup");

  // 👇 Stop speech recognition if running
  if (recognition) {
    try {
      recognition.stop();
      console.log("🛑 Voice stopped because chat was closed.");
    } catch (e) {
      console.warn("Recognition stop error:", e);
    }
  }

  popup.classList.toggle("show");
}

}
let recognition; // global speech recognition object
function startVoice() {
  if (!('webkitSpeechRecognition' in window)) {
    alert("Your browser does not support voice input.");
    return;
  }

  if (!recognition) {
    recognition = new webkitSpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = function (event) {
      const transcript = event.results[0][0].transcript;
      document.getElementById("user-input").value = transcript;
      sendMessage();
    };

    recognition.onerror = function (e) {
      console.error("Speech error:", e);
    };

    recognition.onend = function () {
      console.log("🎤 Voice recognition stopped");
    };
  }

  recognition.start();
  console.log("🎤 Listening...");
}
function toggleChat() {
  const popup = document.getElementById("chat-popup");

  if (recognition) {
    try { recognition.stop(); } catch (e) {}
  }

  popup.classList.toggle("show");
}
