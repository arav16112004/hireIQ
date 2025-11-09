"use client";

import { useEffect, useState } from 'react';
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

  useEffect(() => {
    if (authLoading) {
      return;
    }

    if (!user) {
      router.push('/auth/login');
      return;
    }

    if (user.role !== 'candidate') {
      router.push('/recruiter/dashboard');
      return;
    }

    // Fetch candidate info and check eligibility
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
      
      try {
        const oaRes = await apiClient.oa.getMySessions();
        console.log('OA sessions response:', oaRes.data);
        
        if (oaRes.data?.candidate_id) {
          setCandidateId(oaRes.data.candidate_id);
          console.log('Set candidate_id from OA response:', oaRes.data.candidate_id);
        } else if (oaRes.data?.sessions && Array.isArray(oaRes.data.sessions) && oaRes.data.sessions.length > 0) {
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
    } catch (error) {
      console.error('Error in fetchCandidateInfo:', error);
    }
  };

  const checkEligibility = async () => {
    try {
      setChecking(true);
      console.log('Checking interview eligibility...');
      
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
      
      // Store session ID in localStorage for the HTML page
      localStorage.setItem('interviewSessionId', response.data.session_id);
      
      // Redirect to the HTML interview page with session ID
      window.location.href = `/interview/index.html?sessionId=${response.data.session_id}`;
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
      } else {
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
              <li>• You'll be speaking with Ava, our AI interviewer</li>
            </ul>
          </div>
          
          <button
            onClick={startInterview}
            disabled={loading || !candidateId || !jobId}
            className="px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition disabled:bg-gray-600 disabled:cursor-not-allowed"
          >
            {loading ? 'Starting...' : 'Start Interview with Ava'}
          </button>
        </div>
      </div>
    );
  }

  // This shouldn't be reached since we redirect, but just in case
  return null;
}
