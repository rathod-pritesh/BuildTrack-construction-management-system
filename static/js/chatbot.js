document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");
  const chatBox = document.getElementById("chatMessages");

  if (!input || !sendBtn || !chatBox) return;

  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keypress", e => {
    if (e.key === "Enter") sendMessage();
  });

  function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    addMessage("You", message, "user");
    input.value = "";

    fetch("/chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    })
      .then(res => res.json())
      .then(data => {
        console.log("Server response:", data);
        addMessage("BuildBot", data.reply, "bot");
      })
      .catch(() => {
        addMessage("BuildBot", "Server error. Try again later.", "bot");
      });
  }

  function addMessage(sender, text, type) {
    const div = document.createElement("div");
    // Apply premium styling classes defined in styles.css
    div.className = `chat-bubble ${type}`;
    div.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatBox.appendChild(div);
    
    // Smooth scrolling to latest message
    chatBox.scrollTo({
      top: chatBox.scrollHeight,
      behavior: 'smooth'
    });
  }
});
