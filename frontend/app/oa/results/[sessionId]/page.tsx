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

  useEffect(() => {
    fetchResults();
  }, [sessionId]);

  const fetchResults = async () => {
    try {
      const response = await apiClient.oa.getResults(sessionId);
      setResults(response.data);
    } catch (error) {
      console.error('Failed to fetch results:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  const passed = results?.passed || results?.overall_score >= 70;

  return (
    <div className="min-h-screen bg-white py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-black text-cyan-400 uppercase tracking-wider mb-2 drop-shadow-[0_0_25px_rgba(34,211,238,1)]">
            Assessment Complete!
          </h1>
          <p className="text-gray-700 text-lg">
            Here are your results
          </p>
        </div>

        {/* Score Card */}
        <div className={`bg-white/80 backdrop-blur-md border-4 rounded-2xl shadow-[0_0_40px_rgba(34,211,238,0.4)] p-8 mb-6 ${
          passed ? 'border-green-400/50' : 'border-yellow-400/50'
        }`}>
          <div className="text-center mb-6">
            <div className={`text-6xl font-black mb-2 drop-shadow-[0_0_30px_rgba(34,211,238,1)] ${
              passed ? 'text-green-400' : 'text-yellow-400'
            }`}>
              {results?.overall_score || 0}%
            </div>
            <p className="text-lg text-gray-700 font-bold uppercase tracking-wider">Overall Score</p>
          </div>

          <div className={`p-4 rounded-lg border-2 ${
            passed ? 'bg-green-900/20 border-green-400/30' : 'bg-yellow-900/20 border-yellow-400/30'
          }`}>
            <p className={`text-center font-black uppercase tracking-wider drop-shadow-[0_0_15px_rgba(34,211,238,0.8)] ${
              passed ? 'text-green-400' : 'text-yellow-400'
            }`}>
              {passed ? '✅ Congratulations! You passed the assessment!' : '⚠️ You did not meet the passing threshold (70%)'}
            </p>
          </div>
        </div>

        {/* Question Results */}
        {results?.questions && results.questions.length > 0 && (
          <div className="bg-white/80 backdrop-blur-md border-2 border-cyan-400/30 rounded-2xl shadow-[0_0_40px_rgba(34,211,238,0.3)] p-8">
            <h2 className="text-2xl font-black text-cyan-400 uppercase tracking-wider mb-6 drop-shadow-[0_0_20px_rgba(34,211,238,0.8)]">
              Question Breakdown
            </h2>

            <div className="space-y-4">
              {results.questions.map((q: any, index: number) => (
                <div
                  key={index}
                  className="border-2 border-cyan-400/30 rounded-xl p-4 hover:border-cyan-400/50 hover:shadow-[0_0_20px_rgba(34,211,238,0.3)] transition-all bg-slate-800/50"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-bold text-cyan-300 uppercase tracking-wider">
                        Question {index + 1}: {q.question_title}
                      </h3>
                      <p className="text-sm text-slate-400 mt-1">
                        Test Cases: <span className="text-cyan-400 font-bold">{q.test_cases_passed}/{q.total_test_cases}</span> passed
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {q.passed ? (
                        <span className="px-3 py-1 bg-green-900/30 border-2 border-green-400/50 text-green-400 rounded-full text-sm font-bold uppercase tracking-wider shadow-[0_0_10px_rgba(34,211,238,0.4)]">
                          ✓ Passed
                        </span>
                      ) : (
                        <span className="px-3 py-1 bg-red-900/30 border-2 border-red-400/50 text-red-400 rounded-full text-sm font-bold uppercase tracking-wider shadow-[0_0_10px_rgba(239,68,68,0.4)]">
                          ✗ Failed
                        </span>
                      )}
                      <span className="text-lg font-black text-cyan-400 drop-shadow-[0_0_15px_rgba(34,211,238,0.8)]">
                        {q.score}%
                      </span>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="mt-3">
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden border border-cyan-400/30">
                      <div
                        className={`h-full shadow-[0_0_10px_rgba(34,211,238,0.5)] ${
                          q.passed 
                            ? 'bg-gradient-to-r from-green-500 to-emerald-500' 
                            : 'bg-gradient-to-r from-red-500 to-pink-500'
                        }`}
                        style={{ width: `${(q.test_cases_passed / q.total_test_cases) * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  {q.execution_time && (
                    <p className="text-xs text-slate-400 mt-2 font-medium">
                      Execution time: <span className="text-cyan-400">{q.execution_time.toFixed(2)}s</span>
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-8 flex justify-center space-x-4">
          <button
            onClick={() => router.push('/candidate/dashboard')}
            className="px-6 py-3 bg-slate-800 border-2 border-cyan-400/30 text-cyan-400 rounded-lg hover:border-cyan-400 hover:bg-cyan-400/10 font-bold uppercase tracking-wider transition-all shadow-[0_0_20px_rgba(34,211,238,0.3)] hover:shadow-[0_0_30px_rgba(34,211,238,0.5)] hover:scale-105"
          >
            Back to Dashboard
          </button>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg hover:from-cyan-400 hover:to-blue-500 font-black uppercase tracking-wider transition-all shadow-[0_0_30px_rgba(34,211,238,0.6)] hover:shadow-[0_0_40px_rgba(34,211,238,0.8)] hover:scale-105 ring-2 ring-cyan-400/50"
          >
            Return Home
          </button>
        </div>
      </div>
    </div>
  );
}
