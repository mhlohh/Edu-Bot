/* Chat Popup Styles */
.chat-popup {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  transition: transform 0.3s ease, opacity 0.3s ease;
  opacity: 0;
  transform: translateY(20px);
}

.chat-popup.show {
  opacity: 1;
  transform: translateY(0);
}

/* Input Area */
.input-area {
  display: flex;
  align-items: center;
  border-top: 1px solid #ccc;
  padding: 10px;
}

.input-area input {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 5px;
  margin-right: 10px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.input-area button {
  background-color: #8C1515;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 10px 15px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.input-area button:hover {
  background-color: #a61e1e;
}

/* Quick Replies */
.quick-menu {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 10px 0;
}

.quick-menu .chip {
  background-color: #f0f0f0;
  border-radius: 20px;
  padding: 10px 15px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.quick-menu .chip:hover {
  background-color: #e0e0e0;
}