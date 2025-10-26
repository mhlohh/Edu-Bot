// Consolidated client script: TTS, voice, chat UI, filters, helpers
"use strict";

/* ====== Text-to-Speech / Language detection ====== */
function detectLanguage(text) {
  if (!text) return "en-IN";
  if (/[അ-ഹ]/.test(text)) return "ml-IN";
  if (/[अ-ह]/.test(text)) return "hi-IN";
  return "en-IN";
}
function speak(text) {
  if (!text || !("speechSynthesis" in window)) return;
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = detectLanguage(text);
    u.rate = 1;
    u.pitch = 1;
    window.speechSynthesis.speak(u);
  } catch (e) { console.warn("TTS error:", e); }
}
function stopVoice() { if ("speechSynthesis" in window) window.speechSynthesis.cancel(); }

/* ====== Typing indicator ====== */
function showThinking() {
  const chatBox = document.getElementById("chat-box");
  if (!chatBox) return null;
  const existing = chatBox.querySelector(".bot-message.thinking");
  if (existing) return existing;
  const thinkingDiv = document.createElement("div");
  thinkingDiv.className = "bot-message thinking";
  thinkingDiv.id = "thinking";
  thinkingDiv.setAttribute("aria-live", "polite");
  thinkingDiv.innerHTML = "🤖 Thinking<span class='dots'></span>";
  chatBox.appendChild(thinkingDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
  return thinkingDiv;
}

/* ====== Safe HTML + Formatting Helpers ====== */
function escapeHtml(unsafe) {
  if (!unsafe && unsafe !== 0) return "";
  return String(unsafe).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;").replace(/'/g,"&#039;");
}

function formatBotResponse(text) {
  if (!text) return "<p>(no response)</p>";
  const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  if (lines.length === 0) return "<p>(no response)</p>";

  // bullets
  if (lines.every(l => /^[\u2022\u00B7\-\*\•]\s+/.test(l))) {
    return "<ul class='bot-list'>" + lines.map(l => "<li>" + escapeHtml(l.replace(/^[\u2022\u00B7\-\*\•]\s+/, "")) + "</li>").join("") + "</ul>";
  }

  // numbered
  if (lines.every(l => /^\d+[\.\)]\s+/.test(l))) {
    return "<ol class='bot-list'>" + lines.map(l => "<li>" + escapeHtml(l.replace(/^\d+[\.\)]\s+/, "")) + "</li>").join("") + "</ol>";
  }

  // card-like lines (• Name — details)
  if (lines.every(l => l.startsWith("•") || /—/.test(l))) {
    const items = lines.map(l => {
      l = l.replace(/^[\u2022\u00B7\-\*\•]\s*/, "");
      const parts = l.split(/—| - |•/).map(p => p.trim()).filter(Boolean);
      const title = escapeHtml(parts[0] || l);
      const rest = escapeHtml(parts.slice(1).join(" • "));
      return `<div class="bot-card"><div class="bot-card-title">${title}</div>${rest ? `<div class="bot-card-meta">${rest}</div>` : ""}</div>`;
    });
    return `<div class="bot-cards">${items.join("")}</div>`;
  }

  // fallback paragraphs
  return lines.map(l => `<p>${escapeHtml(l)}</p>`).join("");
}

/* ====== Render messages into chat box ====== */
function displayMessage(text, sender = "bot", opts = {}) {
  const chatBox = document.getElementById("chat-box");
  if (!chatBox) return;
  const wrapper = document.createElement("div");
  wrapper.className = `message-row ${sender === "bot" ? "from-bot" : "from-user"}`;

  const bubble = document.createElement("div");
  bubble.className = sender === "bot" ? "bot-message bubble" : "user-message bubble";

  if (sender === "bot") {
    bubble.innerHTML = opts.html ? text : formatBotResponse(text);
  } else {
    bubble.textContent = text;
  }

  const ts = document.createElement("div");
  ts.className = "msg-ts";
  ts.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  wrapper.appendChild(bubble);
  wrapper.appendChild(ts);
  chatBox.appendChild(wrapper);
  chatBox.scrollTop = chatBox.scrollHeight;
  return wrapper;
}

/* ====== Voice recognition ====== */
let recognition = null;
function startVoice() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { alert("Voice input not supported in this browser."); return; }
  if (!recognition) {
    recognition = new SR();
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (e) => {
      const t = e.results[0][0].transcript;
      const input = document.getElementById("user-input");
      if (input) input.value = t;
    };
    recognition.onerror = (e) => console.warn("Recognition error:", e);
    recognition.onend = () => console.log("Voice recognition ended");
  }
  recognition.lang = document.getElementById("lang")?.value === "hi" ? "hi-IN" : (document.getElementById("lang")?.value === "ml" ? "ml-IN" : "en-IN");
  try { recognition.start(); } catch (e) { console.warn("Could not start recognition:", e); }
}

/* ====== Filters helpers (used by the page UI) ====== */
const $ = id => document.getElementById(id);
const $list = () => document.querySelector(".college-list") || $("#collegeList");

function extractNumberFromDataAttr(el) {
  const v = el?.getAttribute("data-fee") || el?.querySelector(".min-fee")?.textContent || "";
  const digits = (v || "").toString().replace(/[^\d]/g, "");
  const n = parseInt(digits || "0", 10);
  return isNaN(n) ? 0 : n;
}

function currentFilters() {
  return {
    search: ($("search") && $("search").value || "").toLowerCase(),
    course: ($("course-filter") && $("course-filter").value || "").toLowerCase(),
    location: ($("location-filter") && $("location-filter").value || "").toLowerCase(),
    maxFee: parseInt(($("max-fee") && $("max-fee").value) || "0", 10) || 0,
    sort: ($("sort-by") && $("sort-by").value) || "rank"
  };
}

function applySort(items, sort) {
  const arr = Array.from(items);
  if (sort === "fee") arr.sort((a,b) => extractNumberFromDataAttr(a) - extractNumberFromDataAttr(b));
  else if (sort === "name") arr.sort((a,b) => (a.getAttribute("data-name")||"").localeCompare(b.getAttribute("data-name")||""));
  else arr.sort((a,b) => parseInt(a.getAttribute("data-rank")||"999999") - parseInt(b.getAttribute("data-rank")||"999999"));
  const container = $list();
  arr.forEach(el => container.appendChild(el));
}

function filterColleges() {
  const { search, course, location, maxFee, sort } = currentFilters();
  const container = $list();
  if (!container) return;
  const cards = container.querySelectorAll(".college-item");
  cards.forEach(card => {
    const name = (card.getAttribute("data-name")||"").toLowerCase();
    const courses = (card.getAttribute("data-courses")||"").toLowerCase();
    const loc = (card.getAttribute("data-location")||"").toLowerCase();
    const fee = extractNumberFromDataAttr(card);
    const show = (!search || name.includes(search)) &&
                 (!course || courses.includes(course)) &&
                 (!location || loc.includes(location)) &&
                 (!maxFee || fee <= maxFee);
    card.style.display = show ? "flex" : "none";
  });
  const visible = Array.from(cards).filter(c => c.style.display !== "none");
  applySort(visible, sort);
}

/* ====== Autofill filters from user message ====== */
function autoFillFilters(userMessage) {
  if (!userMessage) return;
  const lm = userMessage.toLowerCase();
  const locations = ["kerala","delhi","bangalore","tamil nadu","coimbatore","kochi","chennai","hyderabad","trivandrum","mumbai"];
  const foundLoc = locations.find(l => lm.includes(l));
  if (foundLoc && $("location-filter")) $("location-filter").value = foundLoc;

  const courses = ["b.tech","m.tech","ai","cse","ece","bca","bba","mba","phd"];
  const foundCourse = courses.find(c => lm.includes(c));
  if (foundCourse && $("course-filter")) $("course-filter").value = foundCourse;

  const feeMatch = userMessage.replace(/[,₹\s]/g,"").match(/(\d{3,9})/);
  if (feeMatch && $("max-fee")) $("max-fee").value = feeMatch[1];

  filterColleges();
}

/* ====== Main sendMessage ====== */
async function sendMessage() {
  const input = $("user-input");
  const message = (input && input.value || "").trim();
  if (!message) return;
  const lang = $("lang")?.value || "en";

  // user bubble
  displayMessage(message, "user");
  if (input) input.value = "";

  // thinking
  showThinking();

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, language: lang })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    document.getElementById("thinking")?.remove();

    // show bot reply with formatting
    displayMessage(data.response || "I couldn't find an answer.", "bot", { html: true });
    speak(data.response || "");
    autoFillFilters(message);
  } catch (e) {
    console.error("Chat error:", e);
    document.getElementById("thinking")?.remove();
    displayMessage("⚠️ Something went wrong. Try again.", "bot");
  }
}

/* ====== Quick ask helper ====== */
function quickAsk(text) {
  const input = $("user-input");
  if (input) input.value = text;
  sendMessage();
  autoFillFilters(text);
}

/* ====== Bootstrapping listeners ====== */
document.addEventListener("DOMContentLoaded", () => {
  ["search","course-filter","location-filter","max-fee","sort-by"].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    const ev = id === "sort-by" ? "change" : "input";
    el.addEventListener(ev, filterColleges);
  });

  const input = $("user-input");
  if (input) input.addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); sendMessage(); }
  });

  // initial render
  filterColleges();
});
