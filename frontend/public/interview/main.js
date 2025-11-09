const userVideo = document.getElementById("userVideo");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const endCallBtn = document.getElementById("endCallBtn");

let stream;
let sessionId = null;

// Get session ID from URL or localStorage
const urlParams = new URLSearchParams(window.location.search);
sessionId = urlParams.get('sessionId') || localStorage.getItem('interviewSessionId');

// Store session ID if we got it from URL
if (urlParams.get('sessionId')) {
  localStorage.setItem('interviewSessionId', sessionId);
}

// Get API base URL - try to get from window or use default
const API_URL = window.API_URL || 'http://localhost:8000';

// Get auth token
function getAuthToken() {
  return localStorage.getItem('token');
}

startBtn.addEventListener("click", async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    userVideo.srcObject = stream;
    console.log("Camera started.");
  } catch (err) {
    console.error("Failed to access webcam:", err);
    alert("Please allow camera access to continue the interview.");
  }
});

stopBtn.addEventListener("click", () => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    userVideo.srcObject = null;
    console.log("Camera stopped.");
  }
});

endCallBtn.addEventListener("click", async () => {
  if (confirm("Are you sure you want to end the interview call?")) {
    try {
      // Stop camera
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
        userVideo.srcObject = null;
        stream = null;
      }

      // End interview session if we have a session ID
      if (sessionId) {
        try {
          const token = getAuthToken();
          const response = await fetch(`${API_URL}/interviews/end`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ session_id: sessionId })
          });

          if (response.ok) {
            console.log("Interview session ended successfully");
          } else {
            console.error("Failed to end interview session:", await response.text());
          }
        } catch (error) {
          console.error("Error ending interview session:", error);
        }
      }

      // Clear session ID from localStorage
      localStorage.removeItem('interviewSessionId');

      // Redirect to dashboard
      window.location.href = '/candidate/dashboard';
    } catch (error) {
      console.error("Error ending call:", error);
      // Still redirect even if API call fails
      window.location.href = '/candidate/dashboard';
    }
  }
});
