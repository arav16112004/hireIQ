"use client";

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import apiClient from '@/lib/api';

export default function ApplyPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<any[]>([]);
  const [selectedJob, setSelectedJob] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await apiClient.jobs.getAll();
      setJobs(response.data.jobs || []);
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !selectedJob) {
      setError('Please select a job and upload your resume');
      return;
    }

    if (!user) {
      setError('You must be logged in to apply');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const job = jobs.find(j => j.ID === selectedJob);
      
      // Backend will use authenticated user's email and name
      const response = await apiClient.candidates.ingestResume(
        file,
        selectedJob,
        job?.DESCRIPTION || ''
      );
      
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit application');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-semibold text-gray-900 mb-2">Apply for a Position</h1>
          <p className="text-gray-600">Upload your resume to get matched with opportunities</p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {/* User Info Bar */}
          {user && (
            <div className="bg-gray-50 border-b border-gray-200 px-6 py-4">
              <p className="text-sm text-gray-600">
                Applying as <span className="font-medium text-gray-900">{user.name}</span>
                <span className="text-gray-500"> • {user.email}</span>
              </p>
            </div>
          )}

          <div className="p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Job Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Position
                </label>
                <select
                  value={selectedJob || ''}
                  onChange={(e) => setSelectedJob(Number(e.target.value))}
                  className="w-full px-4 py-2.5 bg-white border border-gray-300 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                  required
                >
                  <option value="">Select a position...</option>
                  {jobs.map(job => (
                    <option key={job.ID} value={job.ID}>
                      {job.TITLE} - {job.DEPARTMENT}
                    </option>
                  ))}
                </select>
              </div>

              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Resume
                </label>
                <div className="relative">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="resume-upload"
                    required
                  />
                  <label 
                    htmlFor="resume-upload" 
                    className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-gray-400 hover:bg-gray-50 transition-colors"
                  >
                    {file ? (
                      <div className="flex flex-col items-center">
                        <svg className="w-8 h-8 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        <p className="text-sm font-medium text-gray-900">{file.name}</p>
                        <p className="text-xs text-gray-500 mt-1">Click to change</p>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center">
                        <svg className="w-8 h-8 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        <p className="text-sm text-gray-600">
                          <span className="text-blue-600 hover:text-blue-700 font-medium">Click to upload</span>
                          <span className="text-gray-500"> or drag and drop</span>
                        </p>
                        <p className="text-xs text-gray-500 mt-1">PDF files only</p>
                      </div>
                    )}
                  </label>
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gray-900 text-white py-2.5 px-4 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-800 transition-colors text-sm"
              >
                {loading ? 'Processing...' : 'Submit Application'}
              </button>
            </form>
          </div>
        </div>

        {/* Results */}
        {result && (
          <div className="mt-6 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Application Submitted</h2>
              <span className="text-2xl">🎉</span>
            </div>
            
            {/* Fit Score */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-gray-700">Fit Score</span>
                <span className="text-2xl font-semibold text-gray-900">{result.fit_score}%</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all ${result.fit_score >= 85 ? 'bg-green-500' : result.fit_score >= 70 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${result.fit_score}%` }}
                />
              </div>
            </div>

            {/* Skills */}
            {result.skills && result.skills.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Matched Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {result.skills.map((skill: string, i: number) => (
                    <span 
                      key={i} 
                      className="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800 border border-gray-200"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Next Steps */}
            <div className="pt-4 border-t border-gray-200">
              {result.fit_score >= 85 ? (
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                      <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 mb-1">You qualify for our Online Assessment</p>
                    <p className="text-sm text-gray-600">
                      Check your email ({user?.email}) for the assessment invitation. You'll have 60 minutes to complete the coding challenges.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                      <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 mb-1">Application Received</p>
                    <p className="text-sm text-gray-600">
                      Thank you for applying. Our team will review your application and get back to you soon.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
