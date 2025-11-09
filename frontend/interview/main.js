const userVideo = document.getElementById("userVideo");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");

let stream;

startBtn.addEventListener("click", async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    userVideo.srcObject = stream;
    console.log("Camera started.");
  } catch (err) {
    console.error("Failed to access webcam:", err);
    alert("Please allow camera access to simulate the interview.");
  }
});

stopBtn.addEventListener("click", () => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    userVideo.srcObject = null;
    console.log("Camera stopped.");
  }
});
