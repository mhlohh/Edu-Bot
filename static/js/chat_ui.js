/* Chat Popup Styles */
.chat-popup {
  background: rgba(255, 255, 255, 0.8); /* Glass effect */
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.chat-popup.show {
  transform: translateY(0);
  opacity: 1;
}

.chat-popup.hidden {
  transform: translateY(100%);
  opacity: 0;
}

.chat-box {
  max-height: 400px;
  overflow-y: auto;
  padding: 10px;
}

.bot-message, .user-message {
  border-radius: 15px;
  padding: 10px 15px;
  margin: 5px 0;
  max-width: 80%;
}

.bot-message {
  background-color: #e0f7fa; /* Light blue for bot messages */
  align-self: flex-start;
}

.user-message {
  background-color: #c8e6c9; /* Light green for user messages */
  align-self: flex-end;
}

/* Button Hover Effects */
.btn:hover, .chip:hover {
  background-color: rgba(140, 21, 21, 0.1);
  cursor: pointer;
}