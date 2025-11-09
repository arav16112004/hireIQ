"use client";

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import apiClient from '@/lib/api';

export default function InterviewPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [eligibility, setEligibility] = useState<any>(null);
  const [checking, setChecking] = useState(true);
  const [interviewStarted, setInterviewStarted] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [candidateId, setCandidateId] = useState<number | null>(null);
  const [jobId, setJobId] = useState<number | null>(null);
  
  const userVideoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const agentContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load D-ID agent script on mount - it should be ready when interview starts
    if (document.getElementById('did-agent-script')) {
      return;
    }

    console.log('Loading D-ID agent (Ava) script...');
    const script = document.createElement('script');
    script.id = 'did-agent-script';
    script.type = 'module';
    script.src = 'https://agent.d-id.com/v2/index.js';
    
    // Configure for conversational mode with voice input/output
    script.setAttribute('data-mode', 'full');
    script.setAttribute('data-client-key', 'Z29vZ2xlLW9hdXRoMnwxMDY5MTYxMzUwMTQzMzQ4Njg3Njc6VGxjWVdCc0tDc0lsU0VtUnRlTXZ3');
    script.setAttribute('data-agent-id', 'v2_agt_eUdbXoE4');
    script.setAttribute('data-name', 'did-agent');
    script.setAttribute('data-monitor', 'true');
    script.setAttribute('data-target-id', 'ava-agent');
    // Enable voice input/output for conversation
    script.setAttribute('data-voice-enabled', 'true');
    script.setAttribute('data-listening', 'true');
    
    script.onload = () => {
      console.log('✅ D-ID agent (Ava) script loaded successfully');
      // Wait for agent to initialize
      setTimeout(() => {
        const agentContainer = document.getElementById('ava-agent');
        if (agentContainer) {
          const iframe = agentContainer.querySelector('iframe');
          if (iframe) {
            console.log('✅ Ava (D-ID agent) is ready for conversation');
          }
        }
      }, 2000);
    };
    
    script.onerror = (error) => {
      console.error('❌ Failed to load D-ID agent script:', error);
    };
    
    document.body.appendChild(script);

    return () => {
      const scriptEl = document.getElementById('did-agent-script');
      if (scriptEl && scriptEl.parentNode) {
        scriptEl.parentNode.removeChild(scriptEl);
      }
    };
  }, []); // Load once on mount

  // Send question to Ava when it changes and interview has started
  useEffect(() => {
    if (interviewStarted && currentQuestion?.text) {
      console.log('📝 New question received, sending to Ava:', currentQuestion.text);
      // Wait for agent to be ready, then send question
      setTimeout(() => {
        speakQuestion(currentQuestion.text);
      }, 3000); // Give Ava time to initialize
    }
  }, [currentQuestion, interviewStarted]);
  
  // Listen for messages from D-ID agent (Ava's responses)
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Listen for messages from D-ID agent
      if (event.data && typeof event.data === 'object') {
        console.log('📨 Message from Ava:', event.data);
        
        // Handle different message types from D-ID agent
        if (event.data.type === 'agent_response' || event.data.type === 'transcript') {
          const transcript = event.data.text || event.data.transcript;
          if (transcript) {
            console.log('💬 Ava said:', transcript);
          }
        }
      }
    };
    
    window.addEventListener('message', handleMessage);
    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, []);

  useEffect(() => {
    if (authLoading) {
      return; // Still loading auth, wait
    }

    if (!user) {
      router.push('/auth/login');
      return;
    }

    if (user.role !== 'candidate') {
      router.push('/recruiter/dashboard');
      return;
    }

    // User is authenticated and is a candidate
    // Fetch candidate info and check eligibility in parallel
    const initialize = async () => {
      try {
        await Promise.all([
          fetchCandidateInfo(),
          checkEligibility()
        ]);
      } catch (error) {
        console.error('Error initializing interview page:', error);
        setChecking(false);
      }
    };
    
    initialize();
  }, [user, authLoading]);

  const fetchCandidateInfo = async () => {
    try {
      console.log('Fetching candidate info...');
      
      // Try to get candidate_id from OA sessions first (most reliable)
      try {
        const oaRes = await apiClient.oa.getMySessions();
        console.log('OA sessions response:', oaRes.data);
        
        if (oaRes.data?.candidate_id) {
          setCandidateId(oaRes.data.candidate_id);
          console.log('Set candidate_id from OA response:', oaRes.data.candidate_id);
        } else if (oaRes.data?.sessions && Array.isArray(oaRes.data.sessions) && oaRes.data.sessions.length > 0) {
          // Try to get candidate_id from first session
          const firstSession = oaRes.data.sessions[0];
          const candidateIdFromSession = firstSession.CANDIDATE_ID || firstSession.candidate_id || firstSession.CANDIDATE_ID;
          if (candidateIdFromSession) {
            setCandidateId(candidateIdFromSession);
            console.log('Set candidate_id from session:', candidateIdFromSession);
          }
        }
      } catch (error) {
        console.error('Error fetching OA sessions:', error);
      }
      
      // Get first available job
      try {
        const jobsRes = await apiClient.jobs.getAll();
        console.log('Jobs response:', jobsRes.data);
        if (jobsRes.data?.jobs && Array.isArray(jobsRes.data.jobs) && jobsRes.data.jobs.length > 0) {
          const firstJob = jobsRes.data.jobs[0];
          const jobIdValue = firstJob.ID || firstJob.id || firstJob.ID;
          if (jobIdValue) {
            setJobId(jobIdValue);
            console.log('Set job_id:', jobIdValue);
          }
        }
      } catch (error) {
        console.error('Error fetching jobs:', error);
      }
      
      console.log('Candidate info fetch complete. candidateId:', candidateId, 'jobId:', jobId);
    } catch (error) {
      console.error('Error in fetchCandidateInfo:', error);
    }
  };

  const checkEligibility = async () => {
    try {
      setChecking(true);
      console.log('Checking interview eligibility...');
      
      // Add timeout to prevent infinite loading
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Eligibility check timeout')), 10000)
      );
      
      const response = await Promise.race([
        apiClient.interviews.checkEligibility(),
        timeoutPromise
      ]) as any;
      
      console.log('Eligibility response:', response.data);
      setEligibility(response.data || { eligible: false, reason: 'Unknown error' });
    } catch (error: any) {
      console.error('Error checking eligibility:', error);
      setEligibility({
        eligible: false,
        reason: error.response?.data?.detail || error.message || 'Error checking eligibility'
      });
    } finally {
      setChecking(false);
      console.log('Eligibility check complete');
    }
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: true, 
        audio: false 
      });
      if (userVideoRef.current) {
        userVideoRef.current.srcObject = stream;
        streamRef.current = stream;
      }
    } catch (err) {
      console.error('Failed to access webcam:', err);
      alert('Please allow camera access to continue the interview.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      if (userVideoRef.current) {
        userVideoRef.current.srcObject = null;
      }
      streamRef.current = null;
    }
  };

  const speakQuestion = (questionText: string) => {
    console.log('🎤 Attempting to speak question:', questionText);
    
    try {
      // D-ID agent should automatically display in the container
      // The agent is conversational and will speak when given input
      // Try to find the agent iframe or send a message to it
      const agentContainer = document.getElementById('ava-agent');
      
      if (agentContainer) {
        // Check if agent iframe is loaded
        const iframe = agentContainer.querySelector('iframe');
        if (iframe) {
          console.log('✅ D-ID agent iframe found');
          // Try to send message to agent (if supported)
          try {
            iframe.contentWindow?.postMessage({
              type: 'speak',
              text: questionText
            }, '*');
          } catch (e) {
            console.log('Could not send message to agent iframe:', e);
          }
        } else {
          console.log('⏳ Waiting for D-ID agent iframe to load...');
        }
        
        // Also try to use browser TTS as fallback/immediate feedback
        if ('speechSynthesis' in window) {
          // Stop any ongoing speech
          window.speechSynthesis.cancel();
          
          const utterance = new SpeechSynthesisUtterance(questionText);
          utterance.rate = 0.9;
          utterance.pitch = 1.0;
          utterance.volume = 1.0;
          
          utterance.onstart = () => {
            console.log('🔊 Browser TTS started speaking');
          };
          
          utterance.onend = () => {
            console.log('✅ Browser TTS finished speaking');
          };
          
          utterance.onerror = (error) => {
            console.error('❌ Browser TTS error:', error);
          };
          
          window.speechSynthesis.speak(utterance);
        }
      } else {
        console.error('❌ Agent container not found');
      }
    } catch (error) {
      console.error('❌ Error in speakQuestion:', error);
    }
  };

  const startInterview = async () => {
    if (!jobId) {
      alert('Unable to start interview: Missing job information');
      return;
    }

    try {
      setLoading(true);
      const response = await apiClient.interviews.start(jobId, candidateId || undefined);
      setSessionId(response.data.session_id);
      setCurrentQuestion(response.data.first_question);
      setInterviewStarted(true);
      setQuestionNumber(1);
      
      // Start camera automatically
      await startCamera();
      
      // Ensure agent container is visible and properly sized
      const agentContainer = document.getElementById('ava-agent');
      if (agentContainer) {
        agentContainer.style.display = 'block';
        agentContainer.style.visibility = 'visible';
        agentContainer.style.opacity = '1';
        console.log('✅ Agent container made visible');
        
        // Check if agent is loading
        setTimeout(() => {
          const iframe = agentContainer.querySelector('iframe');
          if (iframe) {
            console.log('✅ D-ID agent iframe detected in container');
          } else {
            console.log('⏳ D-ID agent iframe not yet loaded, waiting...');
          }
        }, 1000);
      }
      
      // The question will be spoken via the useEffect hook when currentQuestion is set
    } catch (error: any) {
      console.error('Error starting interview:', error);
      alert(error.response?.data?.detail || 'Failed to start interview');
    } finally {
      setLoading(false);
    }
  };

  const submitResponse = async () => {
    if (!sessionId || !response.trim()) {
      alert('Please provide a response');
      return;
    }

    try {
      setLoading(true);
      const result = await apiClient.interviews.next(sessionId, response);
      
      setResponse('');
      setQuestionNumber(prev => prev + 1);
      
      if (result.data.next_question) {
        setCurrentQuestion(result.data.next_question);
        // Question will be spoken automatically via useEffect when currentQuestion changes
      } else {
        // Interview complete
        await endInterview();
      }
    } catch (error: any) {
      console.error('Error submitting response:', error);
      alert(error.response?.data?.detail || 'Failed to submit response');
    } finally {
      setLoading(false);
    }
  };

  const endInterview = async () => {
    if (!sessionId) return;

    try {
      setLoading(true);
      await apiClient.interviews.end(sessionId);
      stopCamera();
      alert('Interview completed successfully!');
      router.push('/candidate/dashboard');
    } catch (error: any) {
      console.error('Error ending interview:', error);
      alert(error.response?.data?.detail || 'Failed to end interview');
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center text-white">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto"></div>
          <p className="mt-4">Loading authentication...</p>
        </div>
      </div>
    );
  }

  if (checking) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center text-white">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto"></div>
          <p className="mt-4">Checking interview eligibility...</p>
          <p className="mt-2 text-sm text-gray-400">This may take a moment</p>
          <button
            onClick={() => {
              console.log('Force stopping eligibility check');
              setChecking(false);
              setEligibility({ eligible: false, reason: 'Check cancelled' });
            }}
            className="mt-4 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition text-sm"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  // If eligibility is null/undefined, show a message
  if (!eligibility) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center text-white">
          <p className="text-xl mb-4">Unable to check eligibility</p>
          <button
            onClick={() => {
              setChecking(true);
              checkEligibility();
            }}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Retry
          </button>
          <button
            onClick={() => router.push('/candidate/dashboard')}
            className="ml-4 px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!eligibility?.eligible) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black flex items-center justify-center p-4">
        <div className="max-w-2xl w-full bg-gray-800 rounded-2xl shadow-2xl p-8 text-center">
          <div className="mb-6">
            <div className="text-6xl mb-4">🚫</div>
            <h1 className="text-3xl font-bold text-white mb-2">Interview Access Restricted</h1>
            <p className="text-gray-400">{eligibility?.reason || 'You are not eligible for an interview at this time.'}</p>
          </div>
          
          {eligibility?.best_score !== null && eligibility?.best_score !== undefined && (
            <div className="mb-6 p-4 bg-gray-700 rounded-lg">
              <p className="text-gray-300 mb-2">Your Best OA Score:</p>
              <p className="text-3xl font-bold text-blue-400">{eligibility.best_score.toFixed(1)}%</p>
              <p className="text-sm text-gray-400 mt-2">Required: {eligibility.threshold}%</p>
            </div>
          )}
          
          <div className="space-y-4">
            <button
              onClick={() => router.push('/candidate/dashboard')}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Back to Dashboard
            </button>
            <button
              onClick={() => router.push('/oa')}
              className="w-full px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
            >
              View OA Assessments
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!interviewStarted) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-4">
        <div className="max-w-2xl w-full text-center">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-4">AI Interview Ready</h1>
            <p className="text-gray-400 text-lg">
              You're eligible for an interview! Your OA score is {eligibility.best_score.toFixed(1)}%
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-white mb-4">Interview Guidelines</h2>
            <ul className="text-left text-gray-300 space-y-2">
              <li>• The interview will consist of {totalQuestions} questions</li>
              <li>• You'll have time to think and respond to each question</li>
              <li>• Your camera will be used for the interview</li>
              <li>• Answer each question thoughtfully and completely</li>
            </ul>
          </div>
          
          <button
            onClick={startInterview}
            disabled={loading || !candidateId || !jobId}
            className="px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition disabled:bg-gray-600 disabled:cursor-not-allowed"
          >
            {loading ? 'Starting...' : 'Start Interview'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black overflow-hidden relative">
      {/* D-ID Agent Container - Fullscreen - Ava the AI Interviewer */}
      <div 
        id="ava-agent" 
        ref={agentContainerRef}
        className="fixed top-0 left-0 w-full h-full bg-black"
        style={{ 
          display: interviewStarted ? 'block' : 'none',
          width: '100vw',
          height: '100vh',
          position: 'fixed',
          top: 0,
          left: 0,
          zIndex: 1,
          visibility: interviewStarted ? 'visible' : 'hidden',
          opacity: interviewStarted ? 1 : 0,
          overflow: 'hidden'
        }}
      />
      
      {/* Info overlay showing Ava is ready */}
      {interviewStarted && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-blue-600/90 text-white px-4 py-2 rounded-lg z-50 text-sm">
          🎤 Ava is ready - You can speak your responses or type them below
        </div>
      )}
      
      {/* Loading indicator for agent */}
      {interviewStarted && (
        <div 
          id="agent-loading"
          className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-white z-10"
          style={{ display: 'none' }}
        >
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
          <p className="mt-4 text-center">Loading AI Avatar...</p>
        </div>
      )}
      
      {/* Floating Webcam - Bottom Right */}
      <video
        ref={userVideoRef}
        autoPlay
        playsInline
        muted
        className="fixed bottom-8 right-8 w-64 h-48 rounded-lg object-cover shadow-2xl border-2 border-white/20 bg-gray-900 z-20"
      />
      
      {/* Controls Overlay - Top Right */}
      <div className="fixed top-6 right-6 z-30 flex gap-3">
        <button
          onClick={startCamera}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm shadow-lg"
        >
          🎥 Start Camera
        </button>
        <button
          onClick={stopCamera}
          className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition text-sm shadow-lg"
        >
          ⏹ Stop Camera
        </button>
      </div>
      
      {/* Question & Response Panel */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-lg border-t border-gray-700 p-6 z-10">
        <div className="max-w-4xl mx-auto">
          {/* Question */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">
                Question {questionNumber} of {totalQuestions}
              </span>
              <span className="text-sm text-blue-400 font-medium">
                {Math.round((questionNumber / totalQuestions) * 100)}% Complete
              </span>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">
              {currentQuestion?.text || 'Loading question...'}
            </h2>
          </div>
          
          {/* Response Input */}
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <textarea
                value={response}
                onChange={(e) => setResponse(e.target.value)}
                placeholder="Type your response here, or speak to Ava directly..."
                className="w-full px-4 py-3 bg-gray-800 text-white rounded-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows={3}
                disabled={loading}
              />
              <p className="text-xs text-gray-400 mt-1">
                💡 Tip: You can speak directly to Ava, or type your response here
              </p>
            </div>
            <div className="flex flex-col gap-2">
              <button
                onClick={submitResponse}
                disabled={loading || !response.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-600 disabled:cursor-not-allowed font-semibold"
              >
                {loading ? 'Submitting...' : questionNumber === totalQuestions ? 'Finish' : 'Submit'}
              </button>
              <button
                onClick={endInterview}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm"
              >
                End Interview
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

