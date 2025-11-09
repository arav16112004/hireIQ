"use client";
import { useEffect, useState, useRef, useCallback } from "react";
import Script from "next/script";

export interface IntegrityMonitor {
  score: number;
  lookingUpTime: number;
  lookingDownTime: number;
  gazeX: number | null;
  gazeY: number | null;
  isReady: boolean;
  isMonitoring: boolean;
  showPredictionPoints: boolean;
  setShowPredictionPoints: (show: boolean) => void;
  startMonitoring: () => void;
  stopMonitoring: () => void;
  resetCalibration: () => void;
}

export function useIntegrityMonitor(): IntegrityMonitor {
  const [score, setScore] = useState(0);
  const [gazeX, setGazeX] = useState<number | null>(null);
  const [gazeY, setGazeY] = useState<number | null>(null);
  const [lookingUpTime, setLookingUpTime] = useState(0);
  const [lookingDownTime, setLookingDownTime] = useState(0);
  const [isReady, setIsReady] = useState(false);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [showPredictionPoints, setShowPredictionPoints] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);

  const webgazerRef = useRef<any>(null);
  const gazeDataRef = useRef({ x: null, y: null, hasLogged: false, hasLoggedError: false });
  const trackingDataRef = useRef({
    offCenterTicks: 0,
    totalTicks: 0,
    lookingUpStartTime: null as number | null,
    lookingDownStartTime: null as number | null,
    lookingUpDuration: 0,
    lookingDownDuration: 0,
    lastGazeX: null as number | null,
    lastGazeY: null as number | null,
    hasLoggedCalculation: false,
    hasLoggedScoreBreakdown: false,
    hasLoggedNoGaze: false,
  });
  const scoreIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const webgazerReadyRef = useRef(false);

  // Wait for WebGazer script to load
  useEffect(() => {
    const checkWebGazer = async () => {
      let attempts = 0;
      while (attempts < 100) {
        if (typeof window !== "undefined" && window.webgazer) {
          setScriptLoaded(true);
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, 100));
        attempts++;
      }
      // Try npm import as fallback
      try {
        const webgazerModule = await import("webgazer");
        window.webgazer = webgazerModule.default || webgazerModule;
        setScriptLoaded(true);
      } catch (err) {
        console.error("Failed to load WebGazer:", err);
      }
    };
    checkWebGazer();
  }, []);

  // Initialize WebGazer
  useEffect(() => {
    if (!scriptLoaded) return;

    let webgazer: any = null;
    let lastGazeUpdate = 0;
    const GAZE_UPDATE_THROTTLE = 100;

    async function initWebGazer() {
      try {
        // Check if already calibrated
        const isCalibrated = localStorage.getItem("webgazer_calibrated") === "true";

        // Wait for WebGazer
        let attempts = 0;
        while (!window.webgazer && attempts < 50) {
          await new Promise((resolve) => setTimeout(resolve, 100));
          attempts++;
        }

        if (!window.webgazer) {
          console.error("WebGazer not available");
          return;
        }

        webgazer = window.webgazer;

        // Set regression
        if (typeof webgazer.setRegression === "function") {
          webgazer.setRegression("ridge");
        }

        // Initialize
        webgazer
          .setGazeListener((data: any, elapsedTime: number) => {
            let x = null;
            let y = null;

            // WebGazer can provide data in different formats
            // Try multiple ways to extract x and y
            if (data) {
              // Format 1: {x: number, y: number}
              if (typeof data.x === 'number' && typeof data.y === 'number') {
                x = data.x;
                y = data.y;
              }
              // Format 2: {clientX: number, clientY: number}
              else if (typeof data.clientX === 'number' && typeof data.clientY === 'number') {
                x = data.clientX;
                y = data.clientY;
              }
              // Format 3: Array [x, y]
              else if (Array.isArray(data) && data.length >= 2 && typeof data[0] === 'number' && typeof data[1] === 'number') {
                x = data[0];
                y = data[1];
              }
              // Format 4: Object with different property names
              else if (data.screenX !== undefined && data.screenY !== undefined) {
                x = data.screenX;
                y = data.screenY;
              }
              // Format 5: Check if data itself is the coordinates
              else if (typeof data === 'object' && Object.keys(data).length === 2) {
                const keys = Object.keys(data);
                const maybeX = data[keys[0]];
                const maybeY = data[keys[1]];
                if (typeof maybeX === 'number' && typeof maybeY === 'number') {
                  x = maybeX;
                  y = maybeY;
                }
              }
            }

            // Update gaze data ref immediately (this is critical for score calculation)
            if (x !== null && y !== null && !isNaN(x) && !isNaN(y) && isFinite(x) && isFinite(y)) {
              const hadLogged = gazeDataRef.current.hasLogged;
              const hadLoggedError = gazeDataRef.current.hasLoggedError;
              
              // Always update the ref (score calculation reads from this)
              gazeDataRef.current = { x, y, hasLogged: hadLogged, hasLoggedError: hadLoggedError };

              // Throttle state updates to prevent UI flickering
              const now = Date.now();
              if (now - lastGazeUpdate > GAZE_UPDATE_THROTTLE) {
                setGazeX(x);
                setGazeY(y);
                lastGazeUpdate = now;
              }

              if (!hadLogged) {
                console.log("✅ First gaze data received:", { x, y, elapsedTime });
                console.log("✅ Raw data format:", data);
                gazeDataRef.current.hasLogged = true;
              }
            } else {
              // Log invalid gaze data format (throttled)
              if (!gazeDataRef.current.hasLoggedError) {
                console.log("⚠️ Invalid or missing gaze data:", {
                  data,
                  dataType: typeof data,
                  isArray: Array.isArray(data),
                  keys: data ? Object.keys(data) : null
                });
                console.log("💡 WebGazer might not be calibrated yet or camera not working");
                gazeDataRef.current.hasLoggedError = true;
                // Reset error flag after 5 seconds to log again if still failing
                setTimeout(() => {
                  gazeDataRef.current.hasLoggedError = false;
                }, 5000);
              }
            }
          })
          .saveDataAcrossSessions(true);
        
        // Check if user is calibrated and resume WebGazer if so
        if (isCalibrated) {
          console.log("✅ User is calibrated, resuming WebGazer with saved data...");
          // Resume WebGazer to load saved calibration data
          if (typeof webgazer.resume === "function") {
            try {
              webgazer.resume();
              console.log("✅ WebGazer resumed with calibration data");
            } catch (resumeError) {
              console.warn("⚠️ Error resuming WebGazer:", resumeError);
            }
          }
        }
        
        webgazerRef.current = webgazer;
        
        // Begin WebGazer
        try {
          webgazer.begin();
          console.log("✅ WebGazer.begin() called");
        } catch (beginError) {
          console.error("❌ Error calling webgazer.begin():", beginError);
        }

        webgazerReadyRef.current = true;
        console.log("✅ WebGazer instance stored in ref and ready");

        // Show video preview (hidden by default)
        if (typeof webgazer.showVideoPreview === "function") {
          webgazer.showVideoPreview(false); // Hide video by default
          console.log("✅ Video preview disabled");
        }

        // Set prediction points based on initial toggle state (default to false to avoid stuck dot)
        const initialShowPoints = showPredictionPoints;
        if (typeof webgazer.showPredictionPoints === "function") {
          webgazer.showPredictionPoints(initialShowPoints);
          console.log(`✅ Prediction points ${initialShowPoints ? 'enabled' : 'disabled'} initially`);
        } else if (typeof webgazer.setPredictionPoints === "function") {
          webgazer.setPredictionPoints(initialShowPoints);
          console.log(`✅ Prediction points ${initialShowPoints ? 'enabled' : 'disabled'} initially (via setPredictionPoints)`);
        } else {
          console.warn("⚠️ showPredictionPoints method not found on WebGazer");
        }

        // Wait for video
        await new Promise((resolve) => {
          let videoAttempts = 0;
          const checkVideo = setInterval(() => {
            videoAttempts++;
            const video = document.querySelector("video");
            if (video && video.readyState >= 2) {
              clearInterval(checkVideo);
              resolve(true);
            } else if (videoAttempts >= 50) {
              clearInterval(checkVideo);
              resolve(false);
            }
          }, 100);
        });

        setIsReady(true);
      } catch (error) {
        console.error("Error initializing WebGazer:", error);
      }
    }

    initWebGazer();

    return () => {
      if (scoreIntervalRef.current) {
        clearInterval(scoreIntervalRef.current);
      }
      // Don't end WebGazer on cleanup - only end when component unmounts
      // This prevents interrupting monitoring when prediction points toggle
    };
  }, [scriptLoaded]); // Removed showPredictionPoints dependency - only initialize once

  // Update prediction points when toggle changes
  useEffect(() => {
    // Use a small delay to ensure WebGazer is fully initialized
    const timeoutId = setTimeout(() => {
      if (webgazerRef.current && webgazerReadyRef.current) {
        try {
          const webgazer = webgazerRef.current;
          if (typeof webgazer.showPredictionPoints === "function") {
            webgazer.showPredictionPoints(showPredictionPoints);
            console.log(`✅ Prediction points ${showPredictionPoints ? 'enabled' : 'disabled'}`);
          } else {
            // Try alternative method names
            if (typeof webgazer.setPredictionPoints === "function") {
              webgazer.setPredictionPoints(showPredictionPoints);
              console.log(`✅ Prediction points ${showPredictionPoints ? 'enabled' : 'disabled'} (via setPredictionPoints)`);
            } else {
              console.warn("⚠️ showPredictionPoints method not available on WebGazer");
              console.log("Available methods:", Object.keys(webgazer).filter(k => k.toLowerCase().includes('prediction') || k.toLowerCase().includes('point')).slice(0, 10));
            }
          }
        } catch (error) {
          console.error("Error toggling prediction points:", error);
        }
      } else {
        console.log("⚠️ WebGazer not ready yet, prediction points toggle will be applied when ready");
      }
    }, 100);

    return () => clearTimeout(timeoutId);
  }, [showPredictionPoints]);

  const startMonitoring = useCallback(() => {
    if (!webgazerReadyRef.current) {
      console.log("WebGazer not ready yet");
      return;
    }
    
    if (isMonitoring) {
      console.log("Already monitoring");
      return;
    }

    if (scoreIntervalRef.current) {
      clearInterval(scoreIntervalRef.current);
    }

    setIsMonitoring(true);
    console.log("🚀 Starting integrity monitoring...");
    console.log("🔍 Initial gaze data:", gazeDataRef.current);
    console.log("🔍 WebGazer ref:", !!webgazerRef.current);
    console.log("🔍 Window.webgazer:", typeof window !== 'undefined' && !!window.webgazer);

    // Reset tracking data when starting monitoring
    trackingDataRef.current = {
      offCenterTicks: 0,
      totalTicks: 0,
      lookingUpStartTime: null,
      lookingDownStartTime: null,
      lookingUpDuration: 0,
      lookingDownDuration: 0,
      lastGazeX: null,
      lastGazeY: null,
      hasLoggedCalculation: false,
      hasLoggedScoreBreakdown: false,
      hasLoggedNoGaze: false,
    };

    scoreIntervalRef.current = setInterval(() => {
      const data = trackingDataRef.current;
      const gaze = gazeDataRef.current;
      const screenCenterX = window.innerWidth / 2;
      const screenCenterY = window.innerHeight / 2;
      const screenHeight = window.innerHeight;
      const screenWidth = window.innerWidth;

      const currentGazeX = gaze.x;
      const currentGazeY = gaze.y;

      // Debug: Log first calculation and periodic updates
      if (!data.hasLoggedCalculation) {
        console.log("🔍 Score calculation interval started. Gaze data:", { x: currentGazeX, y: currentGazeY });
        console.log("🔍 Screen dimensions:", { width: screenWidth, height: screenHeight, centerX: screenCenterX, centerY: screenCenterY });
        console.log("🔍 WebGazer instance:", !!webgazerRef.current);
        console.log("🔍 Window.webgazer:", typeof window !== 'undefined' && !!window.webgazer);
        if (window.webgazer) {
          console.log("🔍 WebGazer methods:", Object.keys(window.webgazer).slice(0, 10));
        }
        data.hasLoggedCalculation = true;
      }

      // Check if we have valid gaze data
      if (currentGazeX !== null && currentGazeY !== null && !isNaN(currentGazeX) && !isNaN(currentGazeY) && isFinite(currentGazeX) && isFinite(currentGazeY)) {
        const xDeviation = Math.abs(currentGazeX - screenCenterX) / screenWidth;
        const yDeviation = Math.abs(currentGazeY - screenCenterY) / screenHeight;
        const totalDeviation = Math.sqrt(xDeviation * xDeviation + yDeviation * yDeviation);

        // Track looking up (top 20% of screen - including notch area)
        const topThreshold = screenHeight * 0.2;
        if (currentGazeY < topThreshold) {
          if (data.lookingUpStartTime === null) {
            data.lookingUpStartTime = Date.now();
          }
          data.lookingUpDuration = (Date.now() - data.lookingUpStartTime) / 1000;
        } else {
          if (data.lookingUpStartTime !== null) {
            data.lookingUpStartTime = null;
          }
          data.lookingUpDuration = 0;
        }

        // Track looking down
        const bottomThreshold = screenHeight * 0.7;
        if (currentGazeY > bottomThreshold) {
          if (data.lookingDownStartTime === null) {
            data.lookingDownStartTime = Date.now();
          }
          data.lookingDownDuration = (Date.now() - data.lookingDownStartTime) / 1000;
        } else {
          if (data.lookingDownStartTime !== null) {
            data.lookingDownStartTime = null;
          }
          data.lookingDownDuration = 0;
        }

        setLookingUpTime(Math.round(data.lookingUpDuration * 10) / 10);
        setLookingDownTime(Math.round(data.lookingDownDuration * 10) / 10);

        // Movement penalty
        let movementPenalty = 0;
        if (data.lastGazeX !== null && data.lastGazeY !== null) {
          const dx = Math.abs(currentGazeX - data.lastGazeX) / screenWidth;
          const dy = Math.abs(currentGazeY - data.lastGazeY) / screenHeight;
          const movement = Math.sqrt(dx * dx + dy * dy);
          movementPenalty = Math.min(30, movement * 200);
        }
        data.lastGazeX = currentGazeX;
        data.lastGazeY = currentGazeY;

        // Track off-center glances
        if (totalDeviation > 0.15) {
          data.offCenterTicks++;
        }
        data.totalTicks++;

        if (data.totalTicks > 100) {
          data.offCenterTicks = Math.floor(data.offCenterTicks * 0.9);
          data.totalTicks = Math.floor(data.totalTicks * 0.9);
        }

        const glanceRatio = data.offCenterTicks / Math.max(1, data.totalTicks);

        // Calculate score
        let immediateScore = 0;
        if (totalDeviation > 0.4) {
          immediateScore = 80 + Math.min(20, (totalDeviation - 0.4) * 50);
        } else if (totalDeviation > 0.25) {
          immediateScore = 50 + ((totalDeviation - 0.25) / 0.15) * 30;
        } else if (totalDeviation > 0.15) {
          immediateScore = 20 + ((totalDeviation - 0.15) / 0.1) * 30;
        } else if (totalDeviation > 0.05) {
          immediateScore = 2 + ((totalDeviation - 0.05) / 0.1) * 18;
        }
        if (totalDeviation > 0.01) {
          immediateScore = Math.max(immediateScore, 1);
        }

        // Time-based penalties
        let lookingUpPenalty = 0;
        if (data.lookingUpDuration > 4.0) {
          lookingUpPenalty = Math.min(100, 50 + ((data.lookingUpDuration - 4.0) / 4) * 50);
        } else if (data.lookingUpDuration > 2) {
          lookingUpPenalty = 20 + ((data.lookingUpDuration - 2) / 2) * 30;
        } else if (data.lookingUpDuration > 1) {
          lookingUpPenalty = 5 + ((data.lookingUpDuration - 1) / 1) * 15;
        }

        let lookingDownPenalty = 0;
        if (data.lookingDownDuration > 3) {
          lookingDownPenalty = Math.min(80, 40 + ((data.lookingDownDuration - 3) / 3) * 40);
        } else if (data.lookingDownDuration > 1.5) {
          lookingDownPenalty = 15 + ((data.lookingDownDuration - 1.5) / 1.5) * 25;
        } else if (data.lookingDownDuration > 0.5) {
          lookingDownPenalty = 3 + ((data.lookingDownDuration - 0.5) / 1) * 12;
        }

        const maxTimePenalty = Math.max(lookingUpPenalty, lookingDownPenalty);
        const immediateComponent = immediateScore * 0.5;
        const movementComponent = movementPenalty * 0.2;
        const historicalComponent = glanceRatio * 100 * 0.1;
        const timePenaltyComponent = maxTimePenalty * 0.2;

        const cheatScore = Math.round(
          Math.min(100, immediateComponent + movementComponent + historicalComponent + timePenaltyComponent)
        );

        // Debug: Log score breakdown (only first time)
        if (!data.hasLoggedScoreBreakdown && cheatScore > 0) {
          console.log("📊 Score breakdown:", {
            immediate: immediateComponent.toFixed(2),
            movement: movementComponent.toFixed(2),
            historical: historicalComponent.toFixed(2),
            timePenalty: timePenaltyComponent.toFixed(2),
            total: cheatScore,
            deviation: totalDeviation.toFixed(3),
            gazeX: currentGazeX.toFixed(0),
            gazeY: currentGazeY.toFixed(0)
          });
          data.hasLoggedScoreBreakdown = true;
        }

        setScore(cheatScore);
      } else {
        // Debug: Log when no gaze data (only first few times)
        if (!data.hasLoggedNoGaze) {
          console.log("⚠️ No gaze data available for score calculation. Gaze:", { x: currentGazeX, y: currentGazeY });
          console.log("💡 Make sure you've calibrated and are looking at the screen.");
          data.hasLoggedNoGaze = true;
          // Reset after 10 seconds to log again if still no data
          setTimeout(() => {
            data.hasLoggedNoGaze = false;
          }, 10000);
        }
        // Set score to 0 if no gaze data
        setScore(0);
      }
    }, 100);
  }, [isMonitoring]);

  const stopMonitoring = useCallback(() => {
    if (scoreIntervalRef.current) {
      clearInterval(scoreIntervalRef.current);
      scoreIntervalRef.current = null;
    }
    setIsMonitoring(false);
  }, []);

  const resetCalibration = useCallback(() => {
    localStorage.removeItem("webgazer_calibrated");
    if (webgazerRef.current && typeof webgazerRef.current.clearData === "function") {
      webgazerRef.current.clearData();
    }
    trackingDataRef.current = {
      offCenterTicks: 0,
      totalTicks: 0,
      lookingUpStartTime: null,
      lookingDownStartTime: null,
      lookingUpDuration: 0,
      lookingDownDuration: 0,
      lastGazeX: null,
      lastGazeY: null,
      hasLoggedCalculation: false,
      hasLoggedScoreBreakdown: false,
      hasLoggedNoGaze: false,
    };
    setScore(0);
    setGazeX(null);
    setGazeY(null);
    setLookingUpTime(0);
    setLookingDownTime(0);
  }, []);

  return {
    score,
    lookingUpTime,
    lookingDownTime,
    gazeX,
    gazeY,
    isReady,
    isMonitoring,
    showPredictionPoints,
    setShowPredictionPoints,
    startMonitoring,
    stopMonitoring,
    resetCalibration,
  };
}

// Extend Window interface for TypeScript
declare global {
  interface Window {
    webgazer: any;
  }
}

