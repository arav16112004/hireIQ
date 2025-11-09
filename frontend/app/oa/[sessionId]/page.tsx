"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api';
import { useAuth } from '@/lib/auth';
import Editor from '@monaco-editor/react';
import Script from 'next/script';
import { useIntegrityMonitor } from '@/lib/integrity';

export default function OAAssessmentPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading: authLoading } = useAuth();
  
  const sessionId = parseInt(params.sessionId as string);
  const candidateId = searchParams.get('candidate_id');
  const token = searchParams.get('token');
  
  const [session, setSession] = useState<any>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [timeLeft, setTimeLeft] = useState(0);
  const [accessVerified, setAccessVerified] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [leftWidth, setLeftWidth] = useState(50); // Percentage for left panel
  const [isResizing, setIsResizing] = useState(false);
  const [consoleHeight, setConsoleHeight] = useState(35); // Percentage for console
  const [isResizingConsole, setIsResizingConsole] = useState(false);
  
  // Integrity monitoring
  const integrity = useIntegrityMonitor();
  const [maxCheatingScore, setMaxCheatingScore] = useState<number>(0);

  // Check calibration status - redirect to calibration if not calibrated
  // This must be before any early returns to follow Rules of Hooks
  useEffect(() => {
    if (!authLoading && user && accessVerified) {
      const isCalibrated = localStorage.getItem("webgazer_calibrated") === "true";
      if (!isCalibrated) {
        console.log("⚠️ User is not calibrated. Redirecting to calibration page...");
        // Build the redirect URL to come back to this OA after calibration
        const currentPath = `/oa/${sessionId}${candidateId && token ? `?candidate_id=${candidateId}&token=${token}` : ''}`;
        const encodedRedirect = encodeURIComponent(currentPath);
        router.push(`/integrity?redirect=${encodedRedirect}`);
        return;
      }
    }
  }, [authLoading, user, accessVerified, sessionId, candidateId, token, router]);

  // Start monitoring when session loads and WebGazer is ready (only if calibrated)
  useEffect(() => {
    if (accessVerified && integrity.isReady && !integrity.isMonitoring) {
      const isCalibrated = localStorage.getItem("webgazer_calibrated") === "true";
      if (isCalibrated) {
        console.log("✅ User is calibrated, starting monitoring...");
        console.log("🔍 Integrity monitor state:", {
          isReady: integrity.isReady,
          isMonitoring: integrity.isMonitoring,
          score: integrity.score,
          gazeX: integrity.gazeX,
          gazeY: integrity.gazeY
        });
        // Small delay to ensure WebGazer is fully initialized
        setTimeout(() => {
          integrity.startMonitoring();
        }, 500);
      } else {
        console.log("⚠️ User is not calibrated yet");
      }
    }
  }, [accessVerified, integrity.isReady, integrity.isMonitoring, integrity.startMonitoring, integrity.score, integrity.gazeX, integrity.gazeY]);

  // Track the highest cheating score during the session
  // Update max score whenever score changes, regardless of monitoring state
  // This ensures we capture the max even if monitoring is temporarily interrupted
  useEffect(() => {
    if (integrity.score !== null && integrity.score !== undefined && !isNaN(integrity.score)) {
      setMaxCheatingScore((prevMax) => {
        const newMax = Math.max(prevMax, integrity.score);
        if (newMax > prevMax) {
          console.log(`📊 New max cheating score: ${newMax} (previous: ${prevMax})`);
        }
        return newMax;
      });
    }
  }, [integrity.score]);

  // Simplified auth flow - redirect to login immediately if not authenticated
  useEffect(() => {
    console.log('Access check useEffect - authLoading:', authLoading, 'user:', !!user, 'candidateId:', candidateId, 'token:', !!token);
    
    if (authLoading) {
      console.log('Auth still loading, waiting...');
      return;
    }
    
    console.log('Auth loaded. Checking access...');
    
    // If not authenticated, redirect to login immediately
    if (!user) {
      console.log('No user, redirecting to login/register');
      const redirectPath = candidateId && token 
        ? `/oa/${sessionId}?candidate_id=${candidateId}&token=${token}`
        : `/oa/${sessionId}`;
      const encodedRedirect = encodeURIComponent(redirectPath);
      router.push(`/auth/login?redirect=${encodedRedirect}`);
      return;
    }
    
    // User is authenticated - verify access
    if (candidateId && token) {
      // Email link flow - verify token matches this user
      console.log('Has candidateId and token, verifying access...');
      console.log('SessionId from URL:', sessionId);
      console.log('CandidateId from URL:', candidateId);
      console.log('Token from URL:', token ? token.substring(0, 20) + '...' : 'NONE');
      verifyAccess();
    } else if (sessionId) {
      // Direct access from dashboard - verify session ownership by checking if user's email matches candidate
      console.log('User authenticated, verifying session ownership...');
      console.log('SessionId:', sessionId, 'User email:', user?.email);
      // We'll verify in fetchSession by checking if the session belongs to this user
      setAccessVerified(true);
    } else {
      console.error('No sessionId, candidateId, or token - cannot verify access');
      setError('Invalid assessment link. Missing required parameters.');
      setLoading(false);
    }
  }, [authLoading, candidateId, token, user]);

  // Fetch session once access is verified and auth is loaded
  useEffect(() => {
    if (accessVerified && !authLoading && user) {
      console.log('Access verified and user loaded, fetching session');
    fetchSession();
    }
  }, [accessVerified, authLoading, user]);

  useEffect(() => {
    if (timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          handleComplete();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft]);

  const verifyAccess = async () => {
    try {
      console.log('Verifying access - user:', user?.email);
      
      // Call public endpoint to verify token and get session info
      // Pass sessionId from URL so backend can verify even if token is invalid (server restart)
      const response = await apiClient.oa.access(
        parseInt(candidateId as string),
        token as string,
        sessionId  // Include sessionId from URL path
      );
      
      console.log('Access response:', response.data);
      
      if (response.data.success) {
        const candidateEmail = response.data.candidate_email;
        
        console.log('User email:', user?.email, 'Candidate email:', candidateEmail);
        
        // Check if logged-in user matches the candidate (case-insensitive)
        const userEmailLower = (user?.email || '').toLowerCase();
        const candidateEmailLower = (candidateEmail || '').toLowerCase();
        if (userEmailLower !== candidateEmailLower) {
          console.error(`Email mismatch: user=${user?.email}, candidate=${candidateEmail}`);
          setError(`This assessment is for ${candidateEmail}. Please log in with the correct account.`);
          setTimeout(() => {
            // Log out and redirect to login
            localStorage.removeItem('token');
            const redirectPath = `/oa/${sessionId}?candidate_id=${candidateId}&token=${token}`;
            const encodedRedirect = encodeURIComponent(redirectPath);
            router.push(`/auth/login?redirect=${encodedRedirect}`);
          }, 3000);
          return;
        }
        
        // All checks passed
        console.log('Access verified successfully');
        setAccessVerified(true);
      }
    } catch (err: any) {
      console.error('Access verification error:', err);
      console.error('Error response:', err.response?.data);
      console.error('Error status:', err.response?.status);
      
      const errorMsg = err.response?.data?.detail || err.message || 'Invalid or expired OA link';
      setError(errorMsg);
      setLoading(false);
      
      // If it's a candidate ID mismatch, show more helpful message
      if (err.response?.status === 403 && errorMsg.includes('candidate')) {
        console.error('Candidate ID mismatch detected. Session may belong to different candidate.');
      }
    }
  };

  const fetchSession = async () => {
    try {
      const authToken = localStorage.getItem('token');
      console.log('=== FETCHING SESSION ===');
      console.log('Session ID:', sessionId);
      console.log('Token in localStorage:', authToken ? authToken.substring(0, 20) + '...' : 'NONE');
      console.log('User object:', user);
      console.log('Candidate ID:', candidateId);
      console.log('Token:', token ? token.substring(0, 20) + '...' : 'NONE');
      
      // Double check token exists
      if (!authToken) {
        console.error('NO TOKEN FOUND - Cannot fetch session');
        setError('Authentication token missing. Please log in again.');
        setTimeout(() => {
          const redirectPath = candidateId && token 
            ? `/oa/${sessionId}?candidate_id=${candidateId}&token=${token}`
            : `/oa/${sessionId}`;
          const encodedRedirect = encodeURIComponent(redirectPath);
          router.push(`/auth/login?redirect=${encodedRedirect}`);
        }, 2000);
        setLoading(false);
        return;
      }
      
      // Validate sessionId
      if (!sessionId || isNaN(sessionId)) {
        console.error('Invalid session ID:', sessionId);
        setError('Invalid assessment link. Please contact support.');
        setLoading(false);
        return;
      }
      
      console.log('Making authenticated request to /oa/session/' + sessionId);
      const sessionRes = await apiClient.oa.getSession(sessionId);
      console.log('Session response received:', sessionRes.data);
      
      const sessionData = sessionRes.data.session || sessionRes.data;
      const fetchedQuestions = sessionRes.data.questions || [];
      
      console.log('Session data:', sessionData);
      console.log('Questions count:', fetchedQuestions.length);
      
      if (!sessionData) {
        console.error('No session data returned');
        setError('Session not found. Please check your assessment link.');
        setLoading(false);
        return;
      }
      
      setSession(sessionData);
      setQuestions(fetchedQuestions);
      
      // Set starter code for first question
      if (fetchedQuestions[0]?.STARTER_CODE) {
        setCode(fetchedQuestions[0].STARTER_CODE);
      }
      
      // Calculate time left - duration in minutes
      const durationMinutes = sessionData.DURATION_MINUTES || sessionData.duration_minutes || 60;
      const startedAt = new Date(sessionData.STARTED_AT || sessionData.started_at || sessionData.CREATED_AT).getTime();
      const now = new Date().getTime();
      const elapsedSeconds = Math.floor((now - startedAt) / 1000);
      const totalSeconds = durationMinutes * 60;
      const secondsLeft = Math.max(0, totalSeconds - elapsedSeconds);
      
      setTimeLeft(secondsLeft);
      setLoading(false);
      console.log('=== SESSION LOADED SUCCESSFULLY ===');
    } catch (error: any) {
      console.error('=== FAILED TO FETCH SESSION ===');
      console.error('Error:', error);
      console.error('Status:', error.response?.status);
      console.error('Response data:', error.response?.data);
      
      const errorDetail = error.response?.data?.detail || error.message;
      
      // Check if it's an authentication error
      if (error.response?.status === 401 || errorDetail?.includes('not authenticated')) {
        console.error('Authentication error detected');
        setError('Authentication failed. Please log in again.');
        setTimeout(() => {
          // Clear token and redirect to login
          localStorage.removeItem('token');
          const redirectPath = candidateId && token 
            ? `/oa/${sessionId}?candidate_id=${candidateId}&token=${token}`
            : `/oa/${sessionId}`;
          const encodedRedirect = encodeURIComponent(redirectPath);
          router.push(`/auth/login?redirect=${encodedRedirect}`);
        }, 2000);
      } else if (error.response?.status === 403) {
        setError(error.response?.data?.detail || 'You do not have permission to access this assessment.');
      } else if (error.response?.status === 404) {
        setError('Assessment not found. The link may be invalid or the assessment may have been removed.');
      } else {
        setError(error.response?.data?.detail || errorDetail || 'Failed to load assessment');
      }
      setLoading(false);
    }
  };

  const handleSubmitCode = async () => {
    if (!questions[currentQuestion]) return;
    
    setSubmitting(true);
    setResult(null);

    try {
      const response = await apiClient.oa.submitCode(
        sessionId,
        questions[currentQuestion].ID,
        code,
        language
      );
      
      const data = response.data;
      
      // Format results for display
      if (data.status === 'error' || data.error) {
        setResult({ 
          error: data.error || 'Execution failed',
          passed: 0,
          total: data.total || 0
        });
      } else {
        setResult({
          passed: data.passed || 0,
          total: data.total || 0,
          raw_output: data.raw_output || '',
          compile_error: data.compile_error,
          test_cases: data.test_cases || [],
          execution_time: data.execution_time,
          memory_used: data.memory_used,
          score: data.score
        });
      }
    } catch (error: any) {
      setResult({ 
        error: error.response?.data?.detail || 'Submission failed',
        passed: 0,
        total: 0
      });
    } finally {
      setSubmitting(false);
    }
  };
  
  // Generate starter code for different languages
  const generateStarterCode = (pythonCode: string, targetLanguage: string): string => {
    if (!pythonCode) return '';
    
    // Extract function name and parameters from Python code
    const match = pythonCode.match(/def\s+(\w+)\s*\((.*?)\):/);
    if (!match) return pythonCode;
    
    const [, funcName, params] = match;
    const paramList = params.split(',').map(p => p.trim()).filter(Boolean);
    
    switch (targetLanguage) {
      case 'javascript':
        return `function ${funcName}(${paramList.join(', ')}) {\n    // Your code here\n    \n}`;
      
      case 'java':
        const javaParams = paramList.map(p => `Object ${p}`).join(', ');
        return `class Solution {\n    public Object ${funcName}(${javaParams}) {\n        // Your code here\n        \n    }\n}`;
      
      case 'cpp':
        const cppParams = paramList.map(p => `auto ${p}`).join(', ');
        return `#include <iostream>\n#include <vector>\nusing namespace std;\n\nauto ${funcName}(${cppParams}) {\n    // Your code here\n    \n}`;
      
      case 'c':
        return `#include <stdio.h>\n\nvoid ${funcName}() {\n    // Your code here\n    \n}`;
      
      default:
        return pythonCode;
    }
  };
  
  // Load starter code when question or language changes
  useEffect(() => {
    if (questions[currentQuestion]?.STARTER_CODE) {
      const starterCode = generateStarterCode(
        questions[currentQuestion].STARTER_CODE,
        language
      );
      setCode(starterCode);
    }
  }, [currentQuestion, language, questions]);

  const handleComplete = async () => {
    if (!confirm('Are you sure you want to submit your assessment? You cannot change your answers after submission.')) {
      return;
    }
    
    try {
      setSubmitting(true);
      
      // Stop integrity monitoring
      if (integrity.isMonitoring) {
        integrity.stopMonitoring();
      }
      
      // Send the highest cheating score recorded during the session
      console.log(`Submitting OA session with max cheating score: ${maxCheatingScore}`);
      const response = await apiClient.oa.complete(sessionId, maxCheatingScore > 0 ? maxCheatingScore : undefined);
      console.log('Assessment completed:', response.data);
      
      // Redirect to dashboard - no popup
      router.push(`/candidate/dashboard`);
    } catch (error: any) {
      console.error('Failed to complete session:', error);
      alert(`Failed to submit assessment: ${error.response?.data?.detail || error.message}`);
      setSubmitting(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle horizontal resizing (left/right panels)
  const handleMouseDown = () => {
    setIsResizing(true);
  };

  const handleMouseUp = () => {
    setIsResizing(false);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizing) return;
    
    const newWidth = (e.clientX / window.innerWidth) * 100;
    if (newWidth > 20 && newWidth < 80) {
      setLeftWidth(newWidth);
    }
  };

  // Handle vertical resizing (editor/console)
  const handleConsoleMouseDown = () => {
    setIsResizingConsole(true);
  };

  const handleConsoleMouseUp = () => {
    setIsResizingConsole(false);
  };

  const handleConsoleMouseMove = (e: MouseEvent) => {
    if (!isResizingConsole) return;
    
    const rightPanel = document.querySelector('.right-panel') as HTMLElement;
    if (!rightPanel) return;
    
    const rect = rightPanel.getBoundingClientRect();
    const newHeight = ((rect.bottom - e.clientY) / rect.height) * 100;
    if (newHeight > 15 && newHeight < 70) {
      setConsoleHeight(newHeight);
    }
  };

  useEffect(() => {
    const onMouseMove = (e: any) => handleMouseMove(e);
    const onMouseUp = () => handleMouseUp();
    
    if (isResizing) {
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [isResizing, leftWidth]);

  useEffect(() => {
    const onMouseMove = (e: any) => handleConsoleMouseMove(e);
    const onMouseUp = () => handleConsoleMouseUp();
    
    if (isResizingConsole) {
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [isResizingConsole, consoleHeight]);

  if (loading || authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          {error && (
            <div className="mt-4 text-red-600 max-w-md">
              {error}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md text-center">
          <div className="text-red-600 text-lg font-semibold mb-4">
            Access Error
          </div>
          <p className="text-gray-700 mb-4">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Go Home
          </button>
        </div>
      </div>
    );
  }

  if (!accessVerified) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Check calibration status - show loading if redirecting
  const isCalibrated = typeof window !== 'undefined' && localStorage.getItem("webgazer_calibrated") === "true";
  if (accessVerified && user && !authLoading && !isCalibrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500 mx-auto mb-4"></div>
          <p className="text-sky-300 text-lg font-semibold">Redirecting to calibration...</p>
          <p className="text-slate-400 text-sm mt-2">You must calibrate before starting the assessment</p>
        </div>
      </div>
    );
  }

  const question = questions[currentQuestion];

  return (
    <>
      <Script
        src="https://webgazer.cs.brown.edu/webgazer.js"
        strategy="afterInteractive"
        onLoad={() => {
          console.log("✅ WebGazer script loaded for OA");
        }}
      />
      <div 
        className={`flex flex-col h-screen bg-gradient-to-b from-black via-slate-950 to-black ${isResizing ? 'cursor-col-resize' : ''} ${isResizingConsole ? 'cursor-row-resize' : ''}`}
        style={{ userSelect: (isResizing || isResizingConsole) ? 'none' : 'auto' }}
      >
      {/* Header */}
        <div className="text-white border-b border-slate-800 flex-shrink-0 shadow-[0_0_40px_rgba(56,189,248,0.15)] bg-slate-900/70 backdrop-blur">
          <div className="px-6 py-4 flex justify-between items-center">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold bg-gradient-to-r from-sky-400 to-blue-500 bg-clip-text text-transparent neon-text">Online Assessment</h1>
              <span className="text-sm text-sky-300 font-semibold px-3 py-1 rounded-full border border-sky-800 bg-sky-900/30">
                Question {currentQuestion + 1} / {questions.length}
              </span>
            </div>
            <div className="flex items-center gap-6">
              {/* Integrity Score */}
              {integrity.isMonitoring && (
                <div className={`text-sm font-bold px-3 py-1.5 rounded-lg border ${
                  integrity.score > 70 
                    ? 'text-red-300 bg-red-900/30 border-red-700' 
                    : integrity.score > 40 
                    ? 'text-yellow-300 bg-yellow-900/30 border-yellow-700'
                    : 'text-green-300 bg-green-900/30 border-green-700'
                }`}>
                  Integrity: {integrity.score}
                </div>
              )}
              <div className={`text-2xl font-mono font-bold px-4 py-2 rounded-lg ring-1 ${timeLeft < 300 ? 'text-amber-300 bg-amber-900/30 ring-amber-400/30' : 'text-sky-300 bg-sky-900/30 ring-sky-400/30'}`}>
                {formatTime(timeLeft)}
              </div>
              {/* Toggle Prediction Points - Show when calibrated */}
              {integrity.isReady && isCalibrated && (
                <button
                  onClick={() => {
                    const newValue = !integrity.showPredictionPoints;
                    console.log(`🔄 Toggling prediction points to: ${newValue}`);
                    integrity.setShowPredictionPoints(newValue);
                    // Also try to call directly in case the effect hasn't run yet
                    if (typeof window !== 'undefined' && window.webgazer) {
                      try {
                        if (typeof window.webgazer.showPredictionPoints === 'function') {
                          window.webgazer.showPredictionPoints(newValue);
                        }
                      } catch (e) {
                        console.error("Error directly toggling prediction points:", e);
                      }
                    }
                  }}
                  className="px-3 py-1.5 text-xs font-bold border border-slate-700 text-slate-300 rounded-lg hover:bg-slate-800 hover:border-sky-400/40 transition-all"
                  title={integrity.showPredictionPoints ? "Hide gaze indicator" : "Show gaze indicator"}
                >
                  {integrity.showPredictionPoints ? "👁️ On" : "👁️ Off"}
                </button>
              )}
          </div>
        </div>
      </div>

      {/* Main Content - Split Screen */}
      <div className="flex flex-1 overflow-hidden">
        {/* Question Panel - Left Side */}
        <div style={{ width: `${leftWidth}%` }} className="border-r border-slate-800 flex flex-col bg-slate-900/60">
          <div className="overflow-y-auto flex-1 p-8">
            {/* Difficulty Badge */}
            <div className="mb-4">
              <span className={`inline-flex items-center px-3 py-1 rounded text-xs font-semibold border ${
                question?.DIFFICULTY?.toLowerCase() === 'easy' ? 'border-emerald-400/30 bg-emerald-900/30 text-emerald-200' :
                question?.DIFFICULTY?.toLowerCase() === 'medium' ? 'border-amber-400/30 bg-amber-900/30 text-amber-200' :
                'border-rose-400/30 bg-rose-900/30 text-rose-200'
              }`}>
                {question?.DIFFICULTY?.toUpperCase()}
              </span>
            </div>

            {/* Title */}
            <h1 className="text-3xl font-bold text-slate-100 mb-6 leading-tight neon-text">
              {question?.TITLE}
            </h1>

            {/* Description */}
            <div className="space-y-4 text-slate-300 text-base leading-relaxed">
              {question?.DESCRIPTION?.split('\n\n').map((paragraph: string, idx: number) => {
                // Check if it's an example section
                if (paragraph.startsWith('Example:')) {
                  return (
                    <div key={idx} className="mt-6 rounded-lg p-5 border border-slate-800 bg-slate-900/60">
                      <h3 className="text-sm font-semibold text-slate-100 mb-3">Example</h3>
                      <div className="space-y-2 text-sm text-slate-200">
                        {paragraph.split('\n').slice(1).map((line: string, i: number) => {
                          if (line.startsWith('Input:')) {
                            return (
                              <div key={i}>
                                <span className="font-semibold text-slate-100">Input:</span>
                                <span className="ml-2 font-mono text-sky-300">{line.substring(6).trim()}</span>
                              </div>
                            );
                          } else if (line.startsWith('Output:')) {
                            return (
                              <div key={i}>
                                <span className="font-semibold text-slate-100">Output:</span>
                                <span className="ml-2 font-mono text-emerald-300">{line.substring(7).trim()}</span>
                              </div>
                            );
                          } else if (line.startsWith('Explanation:')) {
                            return (
                              <div key={i} className="mt-2 text-slate-400">
                                <span className="font-semibold text-slate-300">Explanation:</span>
                                <span className="ml-2">{line.substring(12).trim()}</span>
                              </div>
                            );
                          }
                          return null;
                        })}
                      </div>
                    </div>
                  );
                }
                
                // Check if it's constraints section
                if (paragraph.startsWith('Constraints:')) {
                  return (
                    <div key={idx} className="mt-6">
                      <h3 className="text-sm font-semibold text-slate-100 mb-3">Constraints</h3>
                      <ul className="space-y-2 text-sm">
                        {paragraph.split('\n').slice(1).map((line: string, i: number) => (
                          line.trim() && (
                            <li key={i} className="flex items-start gap-2 text-slate-300">
                              <span className="text-slate-500 mt-1">•</span>
                              <code className="font-mono text-sm bg-slate-900/60 border border-slate-800 px-2 py-0.5 rounded text-sky-300">{line.replace(/^-\s*/, '')}</code>
                            </li>
                          )
                        ))}
                      </ul>
                    </div>
                  );
                }
                
                // Regular paragraph
                return (
                  <p key={idx} className="text-slate-300 leading-relaxed">
                    {paragraph}
                  </p>
                );
              })}
            </div>

            {question?.SAMPLE_INPUT && (
              <div className="mt-8">
                <h3 className="text-sm font-semibold text-slate-100 mb-2">Sample Input</h3>
                <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg text-sm font-mono overflow-x-auto border border-slate-800">
{question.SAMPLE_INPUT}</pre>
              </div>
            )}

            {question?.SAMPLE_OUTPUT && (
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-slate-100 mb-2">Sample Output</h3>
                <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg text-sm font-mono overflow-x-auto border border-slate-800">
{question.SAMPLE_OUTPUT}</pre>
              </div>
            )}
          </div>

          {/* Navigation Buttons */}
          <div className="border-t border-slate-800 bg-slate-900/60 p-5 flex gap-4">
            <button
              onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
              disabled={currentQuestion === 0}
              className="flex-1 px-6 py-3.5 border border-slate-700 text-slate-200 rounded-xl hover:bg-slate-800 hover:border-sky-400/40 hover:text-sky-300 disabled:opacity-40 disabled:cursor-not-allowed font-bold transition-all"
            >
              ← Previous
            </button>
            {currentQuestion < questions.length - 1 ? (
              <button
                onClick={() => setCurrentQuestion(currentQuestion + 1)}
                className="flex-1 px-6 py-3.5 neon-button font-bold"
              >
                Next →
              </button>
            ) : (
              <button
                onClick={handleComplete}
                disabled={submitting}
                className="flex-1 px-6 py-3.5 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl hover:from-emerald-400 hover:to-teal-500 font-bold transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <div className="animate-spin h-5 w-5 border-3 border-white border-t-transparent rounded-full"></div>
                    <span>Submitting...</span>
                  </>
                ) : (
                  <>
                    <span className="text-xl">✓</span>
                    <span>Submit Assessment</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Resizable Divider */}
        <div
          className={`w-1.5 ${isResizing ? 'bg-sky-500' : 'bg-slate-800 hover:bg-sky-600'} cursor-col-resize flex-shrink-0 relative transition-colors duration-200 neon-divider`}
          onMouseDown={handleMouseDown}
          style={{ userSelect: 'none' }}
        >
          {/* Grip indicator */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-full p-1 shadow-md opacity-0 group-hover:opacity-100">
            <div className="w-1 h-8 bg-gray-400 rounded-full"></div>
          </div>
          {/* Invisible wider hit area for easier dragging */}
          <div className="absolute inset-y-0 -left-2 -right-2" />
        </div>

        {/* Code Editor Panel - Right Side */}
        <div style={{ width: `${100 - leftWidth}%` }} className="flex flex-col bg-slate-950 right-panel">
          {/* Editor Controls */}
          <div className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex justify-between items-center flex-shrink-0">
            <div className="flex items-center gap-3">
              <label className="text-sm font-semibold text-slate-300">Language:</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="px-4 py-2 border border-slate-700 rounded-lg text-sm bg-slate-800 text-slate-100 font-medium hover:bg-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="java">Java</option>
                <option value="cpp">C++</option>
                <option value="c">C</option>
              </select>
            </div>
            <button
              onClick={handleSubmitCode}
              disabled={submitting || !code.trim()}
              className="px-8 py-2.5 neon-button font-bold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {submitting ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  <span>Running...</span>
                </>
              ) : (
                <>
                  <span>▶</span>
                  <span>Run Code</span>
                </>
              )}
            </button>
            </div>

          {/* Monaco Editor */}
          <div style={{ height: `${100 - consoleHeight}%` }} className="flex-shrink-0">
            <Editor
              height="100%"
              language={language === 'cpp' ? 'cpp' : language === 'c' ? 'c' : language}
              value={code}
              onChange={(value) => setCode(value || '')}
              theme="vs-dark"
              options={{
                minimap: { enabled: true },
                fontSize: 14,
                lineNumbers: 'on',
                roundedSelection: false,
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 4,
                wordWrap: 'off',
                padding: { top: 16 },
              }}
            />
          </div>

          {/* Resizable Console Divider */}
          <div
            className={`h-1.5 ${isResizingConsole ? 'bg-sky-500' : 'bg-slate-800 hover:bg-sky-600'} cursor-row-resize flex-shrink-0 relative transition-colors duration-200 neon-divider`}
            onMouseDown={handleConsoleMouseDown}
            style={{ userSelect: 'none' }}
          >
            {/* Grip indicator */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-full px-2 py-0.5 shadow-md opacity-70 hover:opacity-100 transition-opacity">
              <div className="flex gap-1">
                <div className="w-6 h-0.5 bg-gray-400 rounded-full"></div>
              </div>
            </div>
            <div className="absolute inset-x-0 -top-2 -bottom-2" />
          </div>

          {/* Console Output - Always visible */}
          <div className="bg-slate-900/60 flex-1 flex flex-col overflow-hidden rounded-b-lg border border-slate-800" style={{ height: `${consoleHeight}%` }}>
            <div className="px-6 py-3 bg-slate-950 border-t border-slate-800 text-white flex justify-between items-center flex-shrink-0 shadow">
              <span className="font-extrabold text-sm tracking-wider bg-gradient-to-r from-sky-400 to-blue-500 bg-clip-text text-transparent neon-text">📋 CONSOLE OUTPUT</span>
              {result && !result.error && result.passed !== undefined && (
                <span className={`text-sm font-bold px-4 py-1.5 rounded-full ring-1 ${
                  result.passed === result.total ? 'bg-emerald-500/20 text-emerald-300 ring-emerald-400/30' : 'bg-amber-500/20 text-amber-300 ring-amber-400/30'
                }`}>
                  {result.passed}/{result.total} Test Cases Passed
                </span>
              )}
            </div>
            <div className="flex-1 overflow-y-auto bg-slate-950 p-4 pb-8">
              {submitting ? (
                <div className="flex items-center justify-center h-full">
                  <div className="flex items-center gap-3 text-slate-300">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-sky-500"></div>
                    <span className="text-sm font-medium">Running your code...</span>
                  </div>
                </div>
              ) : result ? (
                result.error || result.compile_error ? (
                  <div className="mb-4">
                    <div className="bg-red-500/10 border border-red-400/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-red-300 font-semibold">❌ Error</span>
                      </div>
                      <pre className="text-sm font-mono text-red-200 whitespace-pre-wrap">{result.error || result.compile_error}</pre>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4 max-w-full">
                    {/* Raw Output Section */}
                    {result.raw_output && (
                      <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-900/60">
                        <div className="bg-gradient-to-r from-sky-600 to-blue-700 text-white px-5 py-3 text-sm font-bold flex items-center gap-2">
                          <span>📤</span>
                          <span>YOUR PROGRAM OUTPUT</span>
                        </div>
                        <div className="p-5 bg-slate-950">
                          <pre className="text-sm font-mono text-emerald-300 whitespace-pre-wrap break-words overflow-x-auto max-w-full leading-relaxed">{result.raw_output}</pre>
                        </div>
                      </div>
                    )}

                    {/* Stats Bar */}
                    {result.execution_time !== undefined && (
                      <div className="flex gap-4 bg-slate-900/60 border border-slate-800 rounded-xl px-6 py-4">
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-slate-300 font-bold">⏱️ Time:</span>
                          <span className="font-bold text-sky-300">{parseFloat(result.execution_time || 0).toFixed(2)} ms</span>
                        </div>
                        {result.memory_used && (
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-slate-300 font-bold">💾 Memory:</span>
                            <span className="font-bold text-blue-300">{parseFloat(result.memory_used || 0).toFixed(0)} KB</span>
                          </div>
                        )}
                        {result.score !== undefined && (
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-slate-300 font-bold">⭐ Score:</span>
                            <span className="font-bold text-emerald-300">{parseFloat(result.score || 0).toFixed(1)} pts</span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Test Cases */}
                    {result.test_cases && result.test_cases.length > 0 && (
                      <div className="space-y-3">
                        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wide mb-2">Test Results</h3>
                        {result.test_cases.map((tc: any) => (
                          <div 
                            key={tc.number}
                            className={`border rounded-xl overflow-hidden ${
                              tc.passed 
                                ? 'border-emerald-400/30 bg-emerald-500/10' 
                                : 'border-rose-400/30 bg-rose-500/10'
                            }`}
                          >
                            {/* Test Case Header */}
                            <div className={`px-5 py-3 flex items-center justify-between ${
                              tc.passed ? 'bg-emerald-600/40' : 'bg-rose-600/40'
                            }`}>
                              <div className="flex items-center gap-3">
                                <span className="font-bold text-slate-100 text-sm">
                                  {tc.passed ? '✓' : '✗'} Test Case {tc.number}
                                </span>
                                {tc.time !== undefined && tc.time !== null && (
                                  <span className="text-xs text-slate-100 bg-white/10 px-2 py-1 rounded-full font-semibold">
                                    {parseFloat(tc.time).toFixed(2)}ms
                                  </span>
                                )}
                              </div>
                              <span className={`text-xs font-bold px-3 py-1.5 rounded-lg ring-1 ${
                                tc.passed 
                                  ? 'bg-emerald-500/20 text-emerald-300 ring-emerald-400/30' 
                                  : 'bg-rose-500/20 text-rose-300 ring-rose-400/30'
                              }`}>
                                {tc.passed ? 'PASSED' : 'FAILED'}
                              </span>
                            </div>

                            {/* Test Case Body */}
                            <div className="p-4 space-y-3">
                              {/* Input */}
                              {tc.input && (
                                <div>
                                  <div className="text-xs font-semibold text-slate-300 mb-1">Input:</div>
                                  <pre className="text-xs font-mono bg-slate-900/60 border border-slate-800 rounded p-2 text-sky-300 whitespace-pre-wrap break-words overflow-x-auto max-w-full">{tc.input}</pre>
                                </div>
                              )}

                              {/* Output */}
                              {tc.output && (
                                <div>
                                  <div className="text-xs font-semibold text-slate-300 mb-1">Your Output:</div>
                                  <pre className="text-xs font-mono bg-slate-900/60 border border-slate-800 rounded p-2 text-emerald-300 whitespace-pre-wrap break-words overflow-x-auto max-w-full">{tc.output}</pre>
                                </div>
                              )}

                              {/* Expected Output (for failed cases) */}
                              {!tc.passed && tc.expected && (
                                <div>
                                  <div className="text-xs font-semibold text-emerald-300 mb-1">Expected Output:</div>
                                  <pre className="text-xs font-mono bg-slate-900/60 border border-emerald-400/30 rounded p-2 text-emerald-300 whitespace-pre-wrap break-words overflow-x-auto max-w-full">{tc.expected}</pre>
                                </div>
                              )}

                              {/* Error */}
                              {tc.error && (
                                <div>
                                  <div className="text-xs font-semibold text-rose-300 mb-1">Error:</div>
                                  <pre className="text-xs font-mono bg-slate-900/60 border border-rose-400/30 rounded p-2 text-rose-300">{tc.error}</pre>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                )}
              </div>
                )
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  <div className="text-center">
                    <div className="text-4xl mb-2">▶️</div>
                    <div className="text-sm">Click "Run Code" to see output</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
    </>
  );
}

