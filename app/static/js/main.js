// main.js - Pure SSE communication layer (no animations)

const orb = document.getElementById("orb");
const statusText = document.getElementById("agent-status");
const logBody = document.getElementById("log-body");
const connectionDot = document.getElementById("connection-dot");
const connectionLabel = document.getElementById("connection-label");

const pauseBtn = document.getElementById("pause-btn");
const clearBtn = document.getElementById("clear-btn");

let paused = false;
let eventSource = null;
let messageCount = 0;

// Simple logger - no animations, just DOM updates
function log(message, type = "info") {
  if (paused) return;

  // Auto-detect message type from content
  if (!type || type === "info") {
    if (message.toLowerCase().includes("error") || message.toLowerCase().includes("failed")) {
      type = "error";
    } else if (message.toLowerCase().includes("warning") || message.toLowerCase().includes("warn")) {
      type = "warn";
    } else if (message.toLowerCase().includes("success") || message.toLowerCase().includes("complete")) {
      type = "success";
    }
  }

  const line = document.createElement("div");
  line.className = `log-line ${type}`;
  line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  logBody.appendChild(line);
  logBody.scrollTop = logBody.scrollHeight;

  messageCount++;

  // Trigger orb activity via CSS class
  triggerOrbActivity();
}

// Update status text - pure content update
function updateStatusText(text) {
  statusText.textContent = text;
}

// Trigger orb activity via CSS class
function triggerOrbActivity() {
  orb.classList.add('active');
  // Remove class after animation completes
  setTimeout(() => {
    orb.classList.remove('active');
  }, 600);
}

// SSE connection handler
function connect() {
  connectionDot.className = "status-dot connecting";
  connectionLabel.textContent = "Connecting...";
  updateStatusText("INITIALIZING...");
  log("🔌 Connecting to SSE stream...", "info");

  // Create EventSource connection
  eventSource = new EventSource(window.location.href);

  eventSource.onopen = () => {
    connectionDot.className = "status-dot connected";
    connectionLabel.textContent = "Connected";
    updateStatusText("AGENT READY");
    log("✅ Connected to stream", "success");
    triggerOrbActivity();
  };

  eventSource.onmessage = (event) => {
    const message = event.data;
    log(message);
    updateStatusText(message.substring(0, 50) + (message.length > 50 ? "..." : ""));
    triggerOrbActivity();
  };

  eventSource.onerror = (error) => {
    console.error("SSE error:", error);
    connectionDot.className = "status-dot error";
    connectionLabel.textContent = "Connection Lost";
    updateStatusText("AGENT OFFLINE");
    log("❌ Connection error, reconnecting...", "error");

    if (eventSource) {
      eventSource.close();
    }

    // Reconnect after 5 seconds
    setTimeout(() => {
      log("🔄 Attempting to reconnect...", "warn");
      connect();
    }, 5000);
  };
}

// Controls - pure event handlers
pauseBtn.onclick = () => {
  paused = !paused;
  pauseBtn.textContent = paused ? "▶ Resume" : "⏸ Pause";
  log(paused ? "⏸ Stream paused" : "▶ Stream resumed", "info");
};

clearBtn.onclick = () => {
  logBody.innerHTML = "";
  messageCount = 0;
  log("🗑️ Log cleared", "info");
};

// Initialize connection on load
document.addEventListener('DOMContentLoaded', () => {
  log("🤖 Gaby AI initialized", "success");
  log("📊 Ready for data processing", "info");
  connect();
});
