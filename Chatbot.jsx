import React, { useState, useEffect } from "react";

const Chatbot = () => {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hello! 👋 I am your Rama University Chatbot. How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [dots, setDots] = useState("");

  // Loader animation
  useEffect(() => {
    if (!loading) return;
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 500);
    return () => clearInterval(interval);
  }, [loading]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, newMessage]);
    setInput("");

    // Show loader
    setLoading(true);
    const botIndex = messages.length + 1;
    setMessages((prev) => [...prev, { sender: "bot", text: "⏳ Bot is typing" }]);

    try {
      const res = await fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      if (!res.body) throw new Error("No stream received");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let botReply = "";

      // Stream chunks
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        botReply += decoder.decode(value, { stream: true });

        // Update last message with partial reply
        setMessages((prev) => {
          const updated = [...prev];
          updated[botIndex] = { sender: "bot", text: botReply };
          return updated;
        });
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[botIndex] = { sender: "bot", text: "⚠️ Error connecting to server." };
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container" style={{ width: "400px", margin: "auto", fontFamily: "Arial, sans-serif" }}>
      <div
        className="chat-box"
        style={{ border: "1px solid #ccc", borderRadius: "10px", padding: "10px", height: "400px", overflowY: "auto" }}
      >
        {messages.map((msg, i) => (
          <div key={i} style={{ textAlign: msg.sender === "user" ? "right" : "left", margin: "5px 0" }}>
            <span
              style={{
                display: "inline-block",
                padding: "8px 12px",
                borderRadius: "10px",
                background: msg.sender === "user" ? "#4CAF50" : "#f1f0f0",
                color: msg.sender === "user" ? "white" : "black",
              }}
            >
              {msg.text === "⏳ Bot is typing" ? `${msg.text}${dots}` : msg.text}
            </span>
          </div>
        ))}
      </div>

      <div className="chat-input" style={{ marginTop: "10px", display: "flex" }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          style={{ flex: 1, padding: "10px", borderRadius: "5px", border: "1px solid #ccc" }}
          placeholder="Type your message..."
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button
          onClick={sendMessage}
          style={{
            marginLeft: "5px",
            padding: "10px 15px",
            border: "none",
            borderRadius: "5px",
            background: "#4CAF50",
            color: "white",
            cursor: "pointer",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default Chatbot;
