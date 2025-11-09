"use client";

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api';

export default function OALandingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const startOASession = async () => {
      try {
        const candidateId = searchParams.get('candidate_id');
        const token = searchParams.get('token');

        if (!candidateId) {
          setError('Invalid OA link: Missing candidate ID');
          setLoading(false);
          return;
        }

        console.log('Starting OA session for candidate:', candidateId);

        // Fetch all available questions
        console.log('Fetching available questions...');
        const questionsResponse = await apiClient.oaAdmin.getAllQuestions();
        const allQuestions = questionsResponse.data.questions || [];
        
        console.log('Available questions:', allQuestions);
        
        if (allQuestions.length < 3) {
          setError('Not enough questions available in the system. Please contact support.');
          setLoading(false);
          return;
        }
        
        // Randomly select 3 questions
        const shuffled = [...allQuestions].sort(() => Math.random() - 0.5);
        const selectedQuestions = shuffled.slice(0, 3);
        const questionIds = selectedQuestions.map((q: any) => q.ID);  // Changed to uppercase ID
        
        console.log('Selected question IDs:', questionIds);

        // Start OA session with selected questions
        const response = await apiClient.oa.start(
          parseInt(candidateId),
          questionIds,
          60 // Duration in minutes
        );

        const sessionId = response.data.session_id;
        console.log('OA session created:', sessionId);

        // Redirect to the actual OA test page
        router.push(`/oa/${sessionId}`);

      } catch (err: any) {
        console.error('Failed to start OA session:', err);
        console.error('Error response:', err.response);
        console.error('Error data:', err.response?.data);
        
        let errorMsg = 'Failed to start assessment. ';
        if (err.response?.data?.detail) {
          errorMsg += err.response.data.detail;
        } else if (err.message) {
          errorMsg += err.message;
        } else {
          errorMsg += 'Please contact support.';
        }
        
        setError(errorMsg);
        setLoading(false);
      }
    };

    startOASession();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Preparing Your Assessment
            </h1>
            <p className="text-gray-600">
              Setting up your coding challenges...
            </p>
          </>
        ) : error ? (
          <>
            <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Unable to Start Assessment
            </h1>
            <p className="text-red-600 mb-4">{error}</p>
            <p className="text-sm text-gray-500">
              If this problem persists, please contact support@hiq.tech
            </p>
          </>
        ) : null}
      </div>
    </div>
  );
}

