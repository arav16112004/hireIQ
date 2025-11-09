"use client";
import React, { useEffect, useState, useRef, useCallback } from "react";
import Script from "next/script";
import { useRouter, useSearchParams } from "next/navigation";

export default function IntegrityPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectUrl = searchParams.get('redirect');
  
  const [calibrationStatus, setCalibrationStatus] = useState("loading"); // loading, not_started, calibrating, calibrated, monitoring
  const [currentCalibrationPoint, setCurrentCalibrationPoint] = useState(0);
  const [score, setScore] = useState(0);
  const [status, setStatus] = useState("Initializing WebGazer...");
  const [gazeX, setGazeX] = useState(null);
  const [gazeY, setGazeY] = useState(null);
  const [scoreAnimation, setScoreAnimation] = useState(false);
  const [lookingUpTime, setLookingUpTime] = useState(0);
  const [lookingDownTime, setLookingDownTime] = useState(0);
  const [webgazerReady, setWebgazerReady] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [showPredictionPoints, setShowPredictionPoints] = useState(false);
  
  const videoRef = useRef(null);
  const webgazerRef = useRef(null);
  const calibrationPointsRef = useRef([
    { x: "50%", y: "5%" },   // Top center (notch area)
    { x: "10%", y: "10%" },  // Top left
    { x: "90%", y: "10%" },  // Top right
    { x: "50%", y: "50%" },  // Center
    { x: "10%", y: "90%" },  // Bottom left
    { x: "90%", y: "90%" },  // Bottom right
  ]);

  // Tracking variables
  const trackingDataRef = useRef({
    offCenterTicks: 0,
    totalTicks: 0,
    lookingUpStartTime: null,
    lookingDownStartTime: null,
    lookingUpDuration: 0,
    lookingDownDuration: 0,
    lastGazeX: null,
    lastGazeY: null,
    gazeHistory: [],
    hasLoggedCalculation: false,
    hasLoggedScoreBreakdown: false,
    hasLoggedNoGaze: false,
  });

  // Store gaze data in ref so interval can access latest values
  const gazeDataRef = useRef({ x: null, y: null, hasLogged: false, hasLoggedError: false });

  // Store webgazer instance in ref so handlers can access it
  const webgazerInstanceRef = useRef(null);
  const webgazerReadyRef = useRef(false);

  useEffect(() => {
    let webgazer = null;
    let gazeInterval = null;
    let scoreInterval = null;

    async function waitForWebGazer() {
      console.log("Waiting for WebGazer to be available...");
      // Wait for WebGazer to be available (from script tag or npm package)
      let attempts = 0;
      const maxAttempts = 100; // 10 seconds
      
      while (attempts < maxAttempts) {
        // Check for window.webgazer (from CDN script)
        if (typeof window !== "undefined" && window.webgazer) {
          console.log("✅ WebGazer found on window.webgazer");
          return window.webgazer;
        }
        
        // Check for webgazer in various possible locations
        if (typeof window !== "undefined" && window.WebGazer) {
          console.log("✅ WebGazer found on window.WebGazer");
          return window.WebGazer;
        }
        
        await new Promise((resolve) => setTimeout(resolve, 100));
        attempts++;
        
        if (attempts % 10 === 0) {
          console.log(`Still waiting for WebGazer... (${attempts}/100)`);
        }
      }
      
      console.log("⚠️ WebGazer not found on window, trying npm import...");
      
      // Try dynamic import as fallback
      try {
        const webgazerModule = await import("webgazer");
        const wg = webgazerModule.default || webgazerModule;
        console.log("✅ WebGazer loaded from npm package");
        return wg;
      } catch (err) {
        console.error("❌ Failed to load WebGazer from npm:", err);
        throw new Error("WebGazer not available. Please check your internet connection and refresh the page.");
      }
    }

    async function initWebGazer() {
      try {
        setCalibrationStatus("loading");
        setStatus("Loading WebGazer library...");

        // Wait for WebGazer to be available
        webgazer = await waitForWebGazer();
        
        if (!webgazer) {
          throw new Error("WebGazer instance is null");
        }
        
        console.log("WebGazer instance:", webgazer);
        console.log("WebGazer methods:", Object.keys(webgazer));
        
        // Store instance immediately
        webgazerRef.current = webgazer;
        webgazerInstanceRef.current = webgazer;
        
        setStatus("Initializing camera...");

        // Initialize WebGazer
        let lastGazeUpdate = 0;
        const GAZE_UPDATE_THROTTLE = 100; // Update UI every 100ms max
        
        // Check if WebGazer has the required methods
        if (typeof webgazer.setGazeListener !== 'function') {
          console.error("WebGazer.setGazeListener is not a function");
          throw new Error("WebGazer API mismatch. Please refresh the page.");
        }
        
        if (typeof webgazer.begin !== 'function') {
          console.error("WebGazer.begin is not a function");
          throw new Error("WebGazer API mismatch. Please refresh the page.");
        }
        
        // Set regression type first (ridge is recommended for better accuracy)
        if (typeof webgazer.setRegression === 'function') {
          webgazer.setRegression('ridge');
          console.log("✅ Regression type set to 'ridge'");
        }
        
        webgazer
          .setGazeListener((data, elapsedTime) => {
            // WebGazer provides data in different formats, handle both
            let x = null;
            let y = null;
            
          if (data) {
              // Try different possible data formats
              if (data.x !== undefined && data.y !== undefined) {
                x = data.x;
                y = data.y;
              } else if (data.clientX !== undefined && data.clientY !== undefined) {
                x = data.clientX;
                y = data.clientY;
              } else if (Array.isArray(data) && data.length >= 2) {
                x = data[0];
                y = data[1];
              }
            }
            
            if (x !== null && y !== null && !isNaN(x) && !isNaN(y)) {
              // Always update ref immediately (for score calculation)
              const hadLogged = gazeDataRef.current.hasLogged;
              const hadLoggedError = gazeDataRef.current.hasLoggedError;
              gazeDataRef.current = { x, y, hasLogged: hadLogged, hasLoggedError: hadLoggedError };
              
              // Throttle state updates to prevent UI flickering
              const now = Date.now();
              if (now - lastGazeUpdate > GAZE_UPDATE_THROTTLE) {
                setGazeX(x);
                setGazeY(y);
                lastGazeUpdate = now;
              }
              
              // Debug: log first successful reading
              if (!hadLogged) {
                console.log('✅ Gaze data received:', x, y);
                gazeDataRef.current.hasLogged = true;
              }
            } else {
              // Log when data is invalid (only first time)
              if (!gazeDataRef.current.hasLoggedError) {
                console.log('⚠️ Invalid gaze data format:', data);
                gazeDataRef.current.hasLoggedError = true;
              }
            }
          })
          .saveDataAcrossSessions(true);
        
        // Begin WebGazer
        try {
          webgazer.begin();
          console.log("✅ WebGazer.begin() called successfully");
        } catch (beginError) {
          console.error("Error calling webgazer.begin():", beginError);
          throw new Error("Failed to start WebGazer. Please allow camera access and refresh.");
        }

        // Show video feed (if methods exist)
        if (typeof webgazer.showVideoPreview === 'function') {
          webgazer.showVideoPreview(true);
        }
        // Hide prediction points by default to avoid stuck dot
        if (typeof webgazer.showPredictionPoints === 'function') {
          webgazer.showPredictionPoints(false);
          console.log("✅ Prediction points disabled");
        }
        // Also try to hide any existing prediction points
        if (typeof webgazer.setPredictionPoints === 'function') {
          webgazer.setPredictionPoints(false);
        }
        
        // Force hide any prediction points that might have been created
        // Wait a bit for WebGazer to initialize, then clean up
        setTimeout(() => {
          // Hide via API
          if (typeof webgazer.showPredictionPoints === 'function') {
            webgazer.showPredictionPoints(false);
          }
          // Also remove any DOM elements WebGazer might have created
          const allDivs = document.querySelectorAll('div');
          allDivs.forEach((el) => {
            if (el.hasAttribute('data-calibration-dot')) return;
            const style = window.getComputedStyle(el);
            if (style.position === 'fixed' || style.position === 'absolute') {
              const zIndex = parseInt(style.zIndex || '0');
              if (zIndex > 9999) {
                const width = parseFloat(style.width) || 0;
                const height = parseFloat(style.height) || 0;
                // Small fixed/absolute element with very high z-index = likely WebGazer prediction point
                if (width < 50 && height < 50) {
                  el.style.display = 'none';
                }
              }
            }
          });
        }, 500);
        
        // Enable calibration mode if the method exists
        if (typeof webgazer.setCalibrationMode === 'function') {
          webgazer.setCalibrationMode(true);
          console.log("✅ Calibration mode enabled");
        }
        
        console.log("✅ WebGazer initialized, waiting for video...");

        // Wait for video to be ready (with timeout)
        await new Promise((resolve, reject) => {
          let attempts = 0;
          const maxAttempts = 50; // 5 seconds max
          const checkVideo = setInterval(() => {
            attempts++;
            const video = document.querySelector("video");
            if (video && video.readyState >= 2) {
              clearInterval(checkVideo);
              videoRef.current = video;
              resolve();
            } else if (attempts >= maxAttempts) {
              clearInterval(checkVideo);
              reject(new Error("Camera not ready"));
            }
          }, 100);
        });

        // Verify WebGazer instance is still available
        if (!webgazerInstanceRef.current) {
          throw new Error("WebGazer instance lost during initialization");
        }
        
        // WebGazer uses mouse clicks for calibration automatically
        // We'll programmatically trigger clicks at calibration points
        console.log("✅ WebGazer fully initialized and ready");
        console.log("Instance available:", !!webgazerInstanceRef.current);
        console.log("Available methods:", Object.keys(webgazerInstanceRef.current));
        
        // Check if already calibrated
        const isCalibrated = localStorage.getItem("webgazer_calibrated") === "true";
        
        // Mark WebGazer as ready FIRST (before status changes)
        webgazerReadyRef.current = true;
        setWebgazerReady(true);
        
        // Use setTimeout to batch state updates and prevent flickering
        setTimeout(() => {
          if (isCalibrated) {
            // If already calibrated and there's a redirect URL, redirect back immediately
            if (redirectUrl) {
              const decodedRedirect = decodeURIComponent(redirectUrl);
              console.log("✅ User is already calibrated. Redirecting back to:", decodedRedirect);
              setCalibrationStatus("calibrated");
              setStatus("Already calibrated! Redirecting to assessment...");
              setTimeout(() => {
                router.push(decodedRedirect);
              }, 1000);
            } else {
              // No redirect URL, start monitoring on this page
              setCalibrationStatus("calibrated");
              setStatus("Starting monitoring...");
              setTimeout(() => {
                startMonitoring();
              }, 500);
            }
          } else {
            setCalibrationStatus("not_started");
            setStatus("Ready to calibrate. Click the button below to start.");
          }
        }, 100);
      } catch (error) {
        console.error("Error initializing WebGazer:", error);
        setCalibrationStatus("not_started");
        setStatus(`Error: ${error.message}. Please refresh the page and allow camera access.`);
        setWebgazerReady(false);
        webgazerReadyRef.current = false;
      }
    }

    // Store handlers in window for JSX access (use ref to check ready state)
    window.__startCalibration = () => {
      if (!webgazerReadyRef.current) {
        setStatus("Please wait, WebGazer is still initializing...");
        return;
      }
      const wg = webgazerInstanceRef.current;
      if (!wg) {
        setStatus("Error: WebGazer not initialized. Please refresh the page.");
        return;
      }
      
      console.log("🎯 Starting calibration...");
      
      // Enable calibration/data collection mode if available
      if (typeof wg.setCalibrationMode === 'function') {
        wg.setCalibrationMode(true);
        console.log("✅ Calibration mode enabled");
      }
      if (typeof wg.resume === 'function') {
        wg.resume();
        console.log("✅ WebGazer resumed for calibration");
      }
      
      setCalibrationStatus("calibrating");
      setCurrentCalibrationPoint(0);
      const points = calibrationPointsRef.current;
      setStatus(`Look at the red dot and click on it (1/${points.length})`);
    };

    window.__handleCalibrationClick = (pointIndex) => {
      const points = calibrationPointsRef.current;
      
      if (!points || pointIndex < 0 || pointIndex >= points.length) {
        console.error("Invalid calibration point index:", pointIndex);
        return;
      }
      
      const point = points[pointIndex];
      
      // Get the actual screen coordinates
      const xPercent = parseFloat(point.x) / 100;
      const yPercent = parseFloat(point.y) / 100;
      const screenX = window.innerWidth * xPercent;
      const screenY = window.innerHeight * yPercent;

      // Record calibration point using WebGazer's recordScreenPosition
      const wg = webgazerInstanceRef.current;
      
      if (!wg) {
        console.error("❌ WebGazer instance is null");
        setStatus("Error: WebGazer instance not available. Please refresh the page.");
        return;
      }
      
      // WebGazer uses recordScreenPosition for calibration
      // When user clicks the dot while looking at it, we record that screen position
      try {
        if (typeof wg.recordScreenPosition === 'function') {
          // Record the screen position - WebGazer uses this to learn eye-to-screen mapping
          wg.recordScreenPosition(screenX, screenY, 'click');
          const points = calibrationPointsRef.current;
          console.log(`✅ Calibration point ${pointIndex + 1}/${points.length} recorded at (${Math.round(screenX)}, ${Math.round(screenY)})`);
        } else {
          // Fallback: try alternative methods
          console.warn("⚠️ recordScreenPosition not found, trying alternatives...");
          console.log("Available methods:", Object.keys(wg).slice(0, 20)); // Log first 20 methods
          
          // Try mouse event approach as fallback
          const event = new MouseEvent('click', {
            bubbles: true,
            cancelable: true,
            clientX: screenX,
            clientY: screenY,
            view: window
          });
          document.dispatchEvent(event);
          console.log(`⚠️ Using fallback: dispatched click event at (${Math.round(screenX)}, ${Math.round(screenY)})`);
        }
      } catch (err) {
        console.error("Error recording calibration point:", err);
        setStatus("Error adding calibration point. Please try again.");
        return;
      }

      // Move to next point
      if (pointIndex < points.length - 1) {
        const nextIndex = pointIndex + 1;
        setCurrentCalibrationPoint(nextIndex);
        setStatus(`Look at the red dot and click on it (${nextIndex + 1}/${points.length})`);
      } else {
        // Calibration complete
        console.log("✅ Calibration complete!");
        setCalibrationStatus("calibrated");
        setStatus("Calibration complete! Processing...");
        localStorage.setItem("webgazer_calibrated", "true");
        
        // Wait a moment for calibration to process
        // WebGazer needs time to train the regression model with the calibration data
        setTimeout(() => {
          setCalibrationStatus("monitoring");
          setStatus("Monitoring your gaze...");
          
          // Give WebGazer a moment to process calibration data
          setTimeout(() => {
            // If there's a redirect URL, redirect back immediately after calibration
            // Don't start monitoring on the calibration page if we're redirecting
            if (redirectUrl) {
              const decodedRedirect = decodeURIComponent(redirectUrl);
              console.log("🔄 Calibration complete! Redirecting back to:", decodedRedirect);
              setStatus("Calibration complete! Redirecting to assessment...");
              setTimeout(() => {
                router.push(decodedRedirect);
              }, 1500);
            } else {
              // Only start monitoring if we're staying on this page
              startMonitoring();
            }
          }, 500);
        }, 2000);
      }
    };

    window.__resetCalibration = () => {
      localStorage.removeItem("webgazer_calibrated");
      const wg = webgazerInstanceRef.current;
      if (wg) {
        wg.clearData();
      }
      setCalibrationStatus("not_started");
      setCurrentCalibrationPoint(0);
      setScore(0);
      setGazeX(null);
      setGazeY(null);
      setLookingUpTime(0);
      setLookingDownTime(0);
      trackingDataRef.current = {
        offCenterTicks: 0,
        totalTicks: 0,
        lookingUpStartTime: null,
        lookingDownStartTime: null,
        lookingUpDuration: 0,
        lookingDownDuration: 0,
        lastGazeX: null,
        lastGazeY: null,
        gazeHistory: [],
      };
      setStatus("Calibration reset. Please calibrate again.");
    };

    function startMonitoring() {
      // Clear any existing interval
      if (scoreInterval) {
        clearInterval(scoreInterval);
      }
      
      setCalibrationStatus("monitoring");
      setStatus("Monitoring your gaze...");
      console.log("Starting monitoring...");

      // Calculate cheat score based on gaze behavior
      scoreInterval = setInterval(() => {
        const data = trackingDataRef.current;
        const gaze = gazeDataRef.current; // Use ref instead of state
        const screenCenterX = window.innerWidth / 2;
        const screenCenterY = window.innerHeight / 2;
        const screenHeight = window.innerHeight;
        const screenWidth = window.innerWidth;

        // Use gaze from ref (always latest)
        const currentGazeX = gaze.x;
        const currentGazeY = gaze.y;

        if (currentGazeX !== null && currentGazeY !== null && !isNaN(currentGazeX) && !isNaN(currentGazeY)) {
          // Calculate deviation from center (normalized 0-1)
          const xDeviation = Math.abs(currentGazeX - screenCenterX) / screenWidth;
          const yDeviation = Math.abs(currentGazeY - screenCenterY) / screenHeight;
          const totalDeviation = Math.sqrt(xDeviation * xDeviation + yDeviation * yDeviation);
          
          // Debug: log first calculation
          if (!data.hasLoggedCalculation) {
            console.log('✅ Score calculation started. Gaze:', currentGazeX, currentGazeY, 'Deviation:', totalDeviation.toFixed(3));
            data.hasLoggedCalculation = true;
          }

          // Track if looking up (top 20% of screen)
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

          // Track if looking down (bottom 30% of screen)
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

          // Update time displays
          setLookingUpTime(Math.round(data.lookingUpDuration * 10) / 10);
          setLookingDownTime(Math.round(data.lookingDownDuration * 10) / 10);

          // Calculate movement (rapid eye movement)
          let movementPenalty = 0;
          if (data.lastGazeX !== null && data.lastGazeY !== null) {
            const dx = Math.abs(currentGazeX - data.lastGazeX) / screenWidth;
            const dy = Math.abs(currentGazeY - data.lastGazeY) / screenHeight;
            const movement = Math.sqrt(dx * dx + dy * dy);
            movementPenalty = Math.min(30, movement * 200);
          }
          data.lastGazeX = currentGazeX;
          data.lastGazeY = currentGazeY;

          // Track off-center glances (lower threshold for more sensitivity)
          if (totalDeviation > 0.15) { // Lowered from 0.25 to 0.15
            data.offCenterTicks++;
          }
          data.totalTicks++;

          // Reset historical tracking periodically
          if (data.totalTicks > 100) {
            data.offCenterTicks = Math.floor(data.offCenterTicks * 0.9);
            data.totalTicks = Math.floor(data.totalTicks * 0.9);
          }

          const glanceRatio = data.offCenterTicks / Math.max(1, data.totalTicks);

          // Calculate immediate score (lower thresholds for more sensitivity)
          let immediateScore = 0;
          if (totalDeviation > 0.4) {
            immediateScore = 80 + Math.min(20, (totalDeviation - 0.4) * 50);
          } else if (totalDeviation > 0.25) {
            immediateScore = 50 + ((totalDeviation - 0.25) / 0.15) * 30;
          } else if (totalDeviation > 0.15) {
            immediateScore = 20 + ((totalDeviation - 0.15) / 0.1) * 30;
          } else if (totalDeviation > 0.05) {
            immediateScore = 2 + ((totalDeviation - 0.05) / 0.1) * 18; // Lower threshold: 0.05 instead of 0.08
          }
          // Even small deviations (< 0.05) get a tiny score to show it's working
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

          // Calculate final score
          const maxTimePenalty = Math.max(lookingUpPenalty, lookingDownPenalty);
          const immediateComponent = immediateScore * 0.5;
          const movementComponent = movementPenalty * 0.2;
          const historicalComponent = glanceRatio * 100 * 0.1;
          const timePenaltyComponent = maxTimePenalty * 0.2;

          const cheatScore = Math.round(
            Math.min(100, immediateComponent + movementComponent + historicalComponent + timePenaltyComponent)
          );

          // Always update score, even if it's 0 (to show it's working)
          setScore(cheatScore);
          setScoreAnimation(true);
          setTimeout(() => setScoreAnimation(false), 200);
          
          // Debug logging (only first few times)
          if (!data.hasLoggedScoreBreakdown && cheatScore > 0) {
            console.log('📊 Score breakdown:', {
              totalDeviation: totalDeviation.toFixed(3),
              immediateScore: immediateScore.toFixed(1),
              movementPenalty: movementPenalty.toFixed(1),
              glanceRatio: (glanceRatio * 100).toFixed(1) + '%',
              timePenalty: maxTimePenalty.toFixed(1),
              finalScore: cheatScore
            });
            data.hasLoggedScoreBreakdown = true;
          }
        } else {
          // Debug: log when no gaze data (only once)
          if (!data.hasLoggedNoGaze) {
            console.log('⚠️ No gaze data available. Current gaze:', currentGazeX, currentGazeY);
            console.log('💡 Make sure you have:');
            console.log('   1. Completed calibration (clicked all 5 dots)');
            console.log('   2. Your face is visible in the camera');
            console.log('   3. You are looking at the screen');
            data.hasLoggedNoGaze = true;
          }
        }
      }, 100); // Update score every 100ms
    }

    // Only initialize after script is loaded
    if (scriptLoaded) {
      initWebGazer();
    }

    return () => {
      if (gazeInterval) clearInterval(gazeInterval);
      if (scoreInterval) clearInterval(scoreInterval);
      if (webgazer) {
        webgazer.end();
      }
      // Clean up window handlers
      delete window.__startCalibration;
      delete window.__handleCalibrationClick;
      delete window.__resetCalibration;
    };
  }, [scriptLoaded]); // Run when script is loaded

  // Cleanup effect to hide stuck prediction points
  useEffect(() => {
    if (!webgazerReady) return;

    // Function to hide WebGazer prediction points
    const hidePredictionPoints = () => {
      const wg = webgazerRef.current || webgazerInstanceRef.current;
      if (wg) {
        if (typeof wg.showPredictionPoints === 'function') {
          wg.showPredictionPoints(false);
        }
        if (typeof wg.setPredictionPoints === 'function') {
          wg.setPredictionPoints(false);
        }
      }

      // Also hide any DOM elements that WebGazer might have created
      // WebGazer prediction points are typically red circles/dots with high z-index
      if (!showPredictionPoints) {
        // Check for elements with WebGazer-specific attributes (case-insensitive)
        const allElements = document.querySelectorAll('[id], [class]');
        allElements.forEach((el) => {
          if (el.hasAttribute('data-calibration-dot')) return;
          
          const id = (el.id || '').toLowerCase();
          const className = (el.className || '').toString().toLowerCase();
          
          if (id.includes('webgazer') || className.includes('webgazer')) {
            el.style.display = 'none';
            el.style.visibility = 'hidden';
          }
        });
        
        // Also check for elements with very high z-index that might be prediction points
        // This catches elements without IDs/classes that WebGazer creates
        const allDivs = document.querySelectorAll('div');
        allDivs.forEach((el) => {
          if (el.hasAttribute('data-calibration-dot')) return;
          
          const style = window.getComputedStyle(el);
          if (style.position !== 'fixed' && style.position !== 'absolute') return;
          
          const zIndex = parseInt(style.zIndex || '0');
          if (zIndex > 9999) {
            const width = parseFloat(style.width) || 0;
            const height = parseFloat(style.height) || 0;
            // WebGazer prediction points: very high z-index + small size
            if (width < 50 && height < 50) {
              el.style.display = 'none';
              el.style.visibility = 'hidden';
            }
          }
        });
      }
    };

    // Hide immediately
    hidePredictionPoints();

    // Also set up an interval to periodically check and hide stuck points
    const cleanupInterval = setInterval(() => {
      if (!showPredictionPoints) {
        hidePredictionPoints();
      }
    }, 1000);

    return () => {
      clearInterval(cleanupInterval);
      const style = document.getElementById('webgazer-prediction-point-hider');
      if (style) {
        style.remove();
      }
    };
  }, [webgazerReady, showPredictionPoints]);

  // Handler functions for JSX - use useCallback to prevent re-renders
  const startCalibration = React.useCallback(() => {
    console.log("🔵 Start calibration button clicked");
    console.log("WebGazer ready ref:", webgazerReadyRef.current);
    console.log("WebGazer instance ref:", !!webgazerInstanceRef.current);
    console.log("WebGazer ready state:", webgazerReady);
    
    // Use ref for immediate check (doesn't cause re-render)
    if (!webgazerReadyRef.current) {
      setStatus("Please wait, WebGazer is still initializing...");
      console.log("⏳ Calibration attempted but WebGazer not ready");
      return;
    }
    
    const wgInstance = webgazerInstanceRef.current;
    if (!wgInstance) {
      setStatus("Error: WebGazer not initialized. Please refresh the page.");
      console.error("❌ WebGazer instance not available in ref");
      console.log("Trying to get from window...");
      
      // Try to recover from window
      if (typeof window !== "undefined" && window.webgazer) {
        console.log("✅ Found WebGazer on window, recovering...");
        webgazerInstanceRef.current = window.webgazer;
        webgazerRef.current = window.webgazer;
      } else {
        console.error("❌ WebGazer not found anywhere");
        return;
      }
    }
    
    console.log("✅ Starting calibration...");
    console.log("WebGazer instance methods:", wgInstance ? Object.keys(wgInstance) : "none");
    
    // Batch state updates
    setCalibrationStatus("calibrating");
    setCurrentCalibrationPoint(0);
    const points = calibrationPointsRef.current;
    setStatus(`Look at the red dot and click on it (1/${points.length})`);
  }, [webgazerReady]); // Include webgazerReady to check state

  const handleCalibrationClick = (pointIndex) => {
    if (window.__handleCalibrationClick) {
      window.__handleCalibrationClick(pointIndex);
    }
  };

  const resetCalibration = () => {
    if (window.__resetCalibration) {
      window.__resetCalibration();
    }
  };

  const calibrationPoints = calibrationPointsRef.current;
  const currentPoint = calibrationPoints[currentCalibrationPoint];

  return (
    <>
      <Script
        src="https://webgazer.cs.brown.edu/webgazer.js"
        strategy="afterInteractive"
        onLoad={() => {
          console.log("✅ WebGazer script loaded from CDN");
          console.log("window.webgazer available:", typeof window !== "undefined" && !!window.webgazer);
          // Make sure it's accessible
          if (typeof window !== "undefined") {
            window.webgazerReady = true;
          }
          // Mark script as loaded to trigger initialization
          setScriptLoaded(true);
        }}
        onError={(e) => {
          console.error("❌ Failed to load WebGazer script from CDN:", e);
          setStatus("Failed to load WebGazer. Please check your internet connection and refresh.");
        }}
        onReady={() => {
          console.log("✅ WebGazer script ready");
        }}
      />
      <div className="min-h-screen bg-black text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent">
          Integrity Monitor
        </h1>

        {/* Status - Only show if not in monitoring mode to reduce flicker */}
        {calibrationStatus !== "monitoring" && (
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 mb-6">
            <p className="text-sky-300 text-lg">{status}</p>
          </div>
        )}

        {/* Loading State */}
        {calibrationStatus === "loading" && (
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-8 text-center">
            <div className="animate-pulse">
              <div className="w-16 h-16 border-4 border-sky-500 border-t-transparent rounded-full mx-auto mb-4 animate-spin"></div>
              <p className="text-slate-300">{status}</p>
              <p className="text-slate-500 text-sm mt-2">Please allow camera access when prompted</p>
            </div>
          </div>
        )}

        {/* Calibration UI */}
        {calibrationStatus === "not_started" && (
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-8 text-center">
            <p className="text-slate-300 mb-2 text-lg font-semibold">
              Calibration Required
            </p>
            <p className="text-slate-400 mb-6 text-sm">
              {redirectUrl ? (
                <>
                  Calibration is required before you can start your assessment.
                  You'll see 6 red dots appear one at a time. Please look directly at each dot and click on it.
                  After calibration, you'll be redirected back to your assessment.
                </>
              ) : (
                <>
                  Before we start monitoring, we need to calibrate your eye tracking.
                  You'll see 6 red dots appear one at a time. Please look directly at each dot and click on it.
                </>
              )}
            </p>
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                startCalibration();
              }}
              disabled={!webgazerReady}
              className={`px-8 py-3 rounded-lg font-bold transition-all ${
                webgazerReady
                  ? "bg-gradient-to-r from-sky-500 to-blue-600 text-white hover:from-sky-400 hover:to-blue-500 cursor-pointer active:scale-95"
                  : "bg-slate-700 text-slate-400 cursor-not-allowed opacity-50"
              }`}
              style={{ minWidth: '200px' }}
            >
              {webgazerReady ? "Start Calibration" : "Loading..."}
            </button>
            {!webgazerReady && (
              <p className="text-yellow-400 text-xs mt-2">Please wait for WebGazer to initialize</p>
            )}
          </div>
        )}

        {calibrationStatus === "calibrating" && currentPoint && (
          <>
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-6 mb-6 text-center">
              <p className="text-slate-300 text-lg mb-2">Calibration in Progress</p>
              <p className="text-sky-400 text-sm">{status}</p>
              <div className="mt-4 flex justify-center gap-2">
                {[0, 1, 2, 3, 4, 5].map((i) => (
                  <div
                    key={i}
                    className={`h-2 rounded-full transition-all ${
                      i <= currentCalibrationPoint
                        ? "bg-sky-500 w-8"
                        : "bg-slate-700 w-2"
                    }`}
                  />
                ))}
              </div>
            </div>
            <div
              className="fixed"
              data-calibration-dot="true"
              style={{
                left: currentPoint.x,
                top: currentPoint.y,
                transform: "translate(-50%, -50%)",
                zIndex: 10000,
                pointerEvents: "auto",
              }}
            >
              <div
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  const points = calibrationPointsRef.current;
                  console.log(`🔴 Calibration dot ${currentCalibrationPoint + 1}/${points.length} clicked`);
                  handleCalibrationClick(currentCalibrationPoint);
                }}
                onMouseDown={(e) => {
                  e.preventDefault();
                }}
                className="w-28 h-28 bg-red-500 rounded-full cursor-pointer shadow-[0_0_50px_rgba(239,68,68,1)] border-4 border-white hover:scale-110 active:scale-95 transition-all"
                data-calibration-dot="true"
                style={{
                  animation: "pulse 1.5s ease-in-out infinite",
                  boxShadow: "0 0 50px rgba(239, 68, 68, 1), inset 0 0 20px rgba(255, 255, 255, 0.3)"
                }}
                title="Look at this dot and click it"
              >
                <div className="absolute inset-0 flex items-center justify-center text-white font-bold text-lg">
                  {currentCalibrationPoint + 1}/{calibrationPoints.length}
                </div>
              </div>
            </div>
          </>
        )}

        {/* Score Display */}
        {calibrationStatus === "monitoring" && (
          <div className="space-y-6">
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-6">
              <div className="text-center">
                <p className="text-slate-400 text-sm mb-2">Cheat Score</p>
                <div
                  className={`text-6xl font-bold mb-4 transition-all duration-200 ${
                    scoreAnimation ? "scale-125 text-red-300" : "text-sky-400"
                  } ${score > 70 ? "text-red-400" : score > 40 ? "text-yellow-400" : "text-green-400"}`}
                >
                  {score}
                </div>
                <p className="text-slate-500 text-xs">
                  Score updates live - try moving your eyes to see it change!
                </p>
              </div>
            </div>

            {/* Gaze Position */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4">
              <p className="text-slate-400 text-sm">
                {gazeX !== null && gazeY !== null ? (
                  <>Gaze Position: ({Math.round(gazeX)}, {Math.round(gazeY)})</>
                ) : (
                  <span className="text-yellow-400">⚠️ Waiting for gaze data... Make sure you've calibrated and are looking at the screen.</span>
                )}
              </p>
            </div>

            {/* Time Tracking */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-2">Looking Up</p>
                <p className={`text-2xl font-bold ${lookingUpTime > 4 ? "text-red-400" : lookingUpTime > 2 ? "text-yellow-400" : "text-slate-300"}`}>
                  {lookingUpTime.toFixed(1)}s
                </p>
                {lookingUpTime > 4 && (
                  <p className="text-red-400 text-xs mt-1">⚠️ Suspicious: Looking up for more than 4 seconds</p>
                )}
              </div>
              <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-2">Looking Down</p>
                <p className={`text-2xl font-bold ${lookingDownTime > 3 ? "text-red-400" : lookingDownTime > 1.5 ? "text-yellow-400" : "text-slate-300"}`}>
                  {lookingDownTime.toFixed(1)}s
                </p>
                {lookingDownTime > 3 && (
                  <p className="text-red-400 text-xs mt-1">⚠️ Suspicious: Reading for more than 3 seconds</p>
                )}
              </div>
            </div>

            {/* Toggle Prediction Points */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-300 text-sm font-semibold mb-1">Gaze Indicator</p>
                  <p className="text-slate-500 text-xs">Toggle the red dot that shows where you're looking</p>
                </div>
                <button
                  onClick={() => {
                    const newValue = !showPredictionPoints;
                    setShowPredictionPoints(newValue);
                    const wg = webgazerRef.current || webgazerInstanceRef.current;
                    if (wg) {
                      // Try multiple methods to ensure prediction points are toggled
                      if (typeof wg.showPredictionPoints === 'function') {
                        wg.showPredictionPoints(newValue);
                      }
                      if (typeof wg.setPredictionPoints === 'function') {
                        wg.setPredictionPoints(newValue);
                      }
                      // Force hide if we're turning off
                      if (!newValue) {
                        // Try to remove any existing prediction point elements
                        setTimeout(() => {
                          // Look for WebGazer's prediction point elements (usually a div with high z-index)
                          const allElements = document.querySelectorAll('div');
                          allElements.forEach((el) => {
                            const style = window.getComputedStyle(el);
                            if (style.position === 'fixed' || style.position === 'absolute') {
                              const zIndex = parseInt(style.zIndex || '0');
                              // WebGazer prediction points typically have very high z-index
                              if (zIndex > 9999 || (el.id && el.id.includes('webgazer')) || 
                                  (el.className && typeof el.className === 'string' && el.className.includes('webgazer'))) {
                                el.style.display = 'none';
                              }
                            }
                          });
                        }, 100);
                      }
                    }
                  }}
                  className={`px-4 py-2 rounded-lg font-bold transition-all ${
                    showPredictionPoints
                      ? "bg-sky-500/20 border border-sky-500 text-sky-300 hover:bg-sky-500/30"
                      : "bg-slate-700 border border-slate-600 text-slate-400 hover:bg-slate-600"
                  }`}
                >
                  {showPredictionPoints ? "👁️ On" : "👁️ Off"}
                </button>
              </div>
            </div>

            {/* Reset Calibration Button */}
            <button
              onClick={resetCalibration}
              className="bg-slate-800 border border-slate-700 text-slate-300 px-4 py-2 rounded-lg hover:bg-slate-700 transition-all text-sm"
            >
              Reset Calibration
            </button>
          </div>
        )}

        {calibrationStatus === "calibrated" && calibrationStatus !== "monitoring" && (
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-8 text-center">
            <p className="text-slate-300">Starting monitoring...</p>
          </div>
        )}
      </div>
    </div>
    </>
  );
}
