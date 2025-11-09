"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api';

export default function OAResultsPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = parseInt(params.sessionId as string);
  
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchResults();
  }, [sessionId]);

  const fetchResults = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Use the results endpoint which calculates everything
      const response = await apiClient.oa.getResults(sessionId);
      setResults(response.data);
    } catch (error: any) {
      console.error('Failed to fetch results:', error);
      setError(error.response?.data?.detail || 'Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => router.push('/candidate/dashboard')}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const passed = results?.passed || (results?.overall_score || 0) >= 70;
  const score = results?.overall_score || 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-block p-3 bg-blue-100 rounded-full mb-4">
            <svg className="w-12 h-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Assessment Complete
          </h1>
          <p className="text-gray-600 text-lg">
            Your results are ready
          </p>
        </div>

        {/* Score Card */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden mb-8">
          <div className={`${passed ? 'bg-gradient-to-r from-green-500 to-emerald-600' : 'bg-gradient-to-r from-orange-500 to-red-500'} p-8 text-center`}>
            <div className="text-white">
              <p className="text-sm font-medium mb-2 opacity-90">YOUR SCORE</p>
              <div className="text-7xl font-bold mb-2">{score.toFixed(1)}%</div>
              <p className="text-lg opacity-90">
                {results?.total_score?.toFixed(0) || 0} out of {results?.max_score?.toFixed(0) || 0} points
              </p>
            </div>
          </div>
          
          <div className="p-6">
            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${
              passed 
                ? 'bg-green-50 text-green-700' 
                : 'bg-orange-50 text-orange-700'
            }`}>
              {passed ? (
                <>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="font-semibold">Passed - Great job!</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span className="font-semibold">Did not meet passing threshold (70%)</span>
                </>
              )}
            </div>
            
            {score >= 90 && (
              <div className="mt-4 p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
                <p className="text-sm text-emerald-800">
                  <span className="font-semibold">🎉 Congratulations!</span> You scored {score.toFixed(1)}%, which makes you eligible for the AI interview!
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Question Breakdown */}
        {results?.questions && results.questions.length > 0 && (
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Question Breakdown</h2>
            
            <div className="space-y-4">
              {results.questions.map((q: any, index: number) => (
                <div
                  key={index}
                  className="border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">
                        Question {index + 1}: {q.question_title}
                      </h3>
                      {q.total_test_cases > 0 && (
                        <p className="text-sm text-gray-600">
                          {q.test_cases_passed} of {q.total_test_cases} test cases passed
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-3 ml-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        q.passed
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {q.passed ? '✓ Passed' : '✗ Failed'}
                      </span>
                      <span className="text-xl font-bold text-gray-900">
                        {q.score.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  
                  {/* Progress bar */}
                  {q.total_test_cases > 0 && (
                    <div className="mt-3">
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all ${
                            q.passed
                              ? 'bg-green-500'
                              : 'bg-red-500'
                          }`}
                          style={{ width: `${Math.min((q.test_cases_passed / q.total_test_cases) * 100, 100)}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                  
                  {q.execution_time && (
                    <p className="text-xs text-gray-500 mt-2">
                      Execution time: {q.execution_time.toFixed(2)}s
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => router.push('/candidate/dashboard')}
            className="px-8 py-3 bg-white border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-semibold transition shadow-sm hover:shadow"
          >
            Back to Dashboard
          </button>
          {score >= 90 && (
            <button
              onClick={() => router.push('/interview')}
              className="px-8 py-3 bg-gradient-to-r from-emerald-600 to-teal-700 text-white rounded-lg hover:from-emerald-700 hover:to-teal-800 font-semibold transition shadow-lg hover:shadow-xl"
            >
              🎥 Start AI Interview
            </button>
          )}
          <button
            onClick={() => router.push('/')}
            className="px-8 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 font-semibold transition shadow-sm hover:shadow"
          >
            Return Home
          </button>
        </div>
      </div>
    </div>
  );
}
