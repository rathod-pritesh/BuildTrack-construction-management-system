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

    addMessage("You", message, "text-end");
    input.value = "";

    fetch("/chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    })
      .then(res => res.json())
      .then(data => {
        console.log("Server response:", data);
        addMessage("BuildBot", data.reply, "bg-light");
      })
      .catch(() => {
        addMessage("BuildBot", "Server error. Try again later.", "bg-light");
      });
  }

  function addMessage(sender, text, extraClass = "") {
    const div = document.createElement("div");
    div.className = `p-2 my-1 rounded ${extraClass}`;
    div.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
});
