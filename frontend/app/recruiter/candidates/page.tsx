"use client";

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import apiClient from '@/lib/api';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function RecruiterCandidatesPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [candidates, setCandidates] = useState<any[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterJobId, setFilterJobId] = useState<string>('');
  const [filterStage, setFilterStage] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [sendingOA, setSendingOA] = useState<number | null>(null);
  const [deletingCandidate, setDeletingCandidate] = useState<number | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }

    if (user && user.role !== 'recruiter' && user.role !== 'admin') {
      router.push('/candidate/dashboard');
      return;
    }

    if (user) {
      fetchData();
    }
  }, [user, authLoading, filterJobId, filterStage]);

  const fetchData = async () => {
    try {
      // Use the company-specific endpoint to get candidates for recruiter's company
      const [candidatesRes, jobsRes] = await Promise.all([
        apiClient.recruiter.getCompanyCandidates(),
        apiClient.jobs.getAll(),
      ]);

      let allCandidates = candidatesRes.data.candidates || [];
      
      // Apply client-side filters
      if (filterJobId) {
        allCandidates = allCandidates.filter((c: any) => c.JOB_ID === parseInt(filterJobId));
      }
      if (filterStage) {
        allCandidates = allCandidates.filter((c: any) => c.STAGE === filterStage);
      }
      
      setCandidates(allCandidates);
      setJobs(jobsRes.data.jobs || []);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendOA = async (candidateId: number) => {
    if (!confirm('Send OA invitation to this candidate?')) return;
    
    setSendingOA(candidateId);
    try {
      await apiClient.candidates.sendOA(candidateId, false);
      alert('OA invitation sent successfully!');
      fetchData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to send OA invitation');
    } finally {
      setSendingOA(null);
    }
  };

  const handleDeleteCandidate = async (candidateId: number) => {
    if (!confirm('Are you sure you want to delete this candidate? This action cannot be undone.')) {
      return;
    }

    setDeletingCandidate(candidateId);
    try {
      await apiClient.candidates.delete(candidateId);
      alert('Candidate deleted successfully!');
      fetchData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to delete candidate');
    } finally {
      setDeletingCandidate(null);
    }
  };

  const filteredCandidates = candidates.filter((candidate) => {
    const matchesSearch = searchQuery === '' || 
      candidate.NAME?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      candidate.EMAIL?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const getStageColor = (stage: string) => {
    switch (stage?.toLowerCase()) {
      case 'applied':
        return 'bg-blue-900/30 text-blue-300 border-blue-700';
      case 'oa_sent':
        return 'bg-cyan-900/30 text-cyan-300 border-cyan-700';
      case 'oa_completed':
        return 'bg-purple-900/30 text-purple-300 border-purple-700';
      case 'interview':
        return 'bg-yellow-900/30 text-yellow-300 border-yellow-700';
      case 'accepted':
        return 'bg-green-900/30 text-green-300 border-green-700';
      case 'rejected':
        return 'bg-red-900/30 text-red-300 border-red-700';
      default:
        return 'bg-white/30 text-gray-700 border-slate-700';
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2 drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">
            All Candidates
          </h1>
          <p className="text-gray-700">
            Manage and review all candidates for your company
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white/80 backdrop-blur-md border border-gray-200 rounded-xl p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2">
                Search
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Name or email..."
                className="w-full px-4 py-2 bg-gray-100 border border-gray-200 text-sky-200 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400"
              />
            </div>
            <div>
              <label className="block text-sm font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2">
                Filter by Job
              </label>
              <select
                value={filterJobId}
                onChange={(e) => setFilterJobId(e.target.value)}
                className="w-full px-4 py-2 bg-gray-100 border border-gray-200 text-sky-200 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400"
              >
                <option value="">All Jobs</option>
                {jobs.map((job) => (
                  <option key={job.ID} value={job.ID}>
                    {job.TITLE}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2">
                Filter by Stage
              </label>
              <select
                value={filterStage}
                onChange={(e) => setFilterStage(e.target.value)}
                className="w-full px-4 py-2 bg-gray-100 border border-gray-200 text-sky-200 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400"
              >
                <option value="">All Stages</option>
                <option value="applied">Applied</option>
                <option value="oa_sent">OA Sent</option>
                <option value="oa_completed">OA Completed</option>
                <option value="interview">Interview</option>
                <option value="accepted">Accepted</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={() => {
                  setFilterJobId('');
                  setFilterStage('');
                  setSearchQuery('');
                }}
                className="w-full px-4 py-2 bg-gray-100 border border-gray-200 text-sky-400 rounded-lg hover:border-sky-400/50 hover:bg-sky-400/10 transition-all font-bold uppercase tracking-wider"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Candidates List */}
        <div className="bg-white/80 backdrop-blur-md border border-gray-200 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-sky-900/10">
            <h2 className="text-xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider">
              Candidates ({filteredCandidates.length})
            </h2>
          </div>
          <div className="divide-y divide-sky-400/20">
            {filteredCandidates.length > 0 ? (
              filteredCandidates.map((candidate) => (
                <div key={candidate.ID} className="px-6 py-4 hover:bg-sky-900/10 transition-all">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-2">
                        <h3 className="font-bold text-gray-900 uppercase tracking-wider text-lg">
                          {candidate.NAME || 'Unknown'}
                        </h3>
                        <span className={`px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-wider border ${getStageColor(candidate.STAGE)}`}>
                          {candidate.STAGE || 'applied'}
                        </span>
                        {candidate.FIT_SCORE && (
                          <span className="px-3 py-1 rounded-lg text-xs font-bold text-sky-600 bg-sky-50 border border-sky-200">
                            Fit: {parseFloat(candidate.FIT_SCORE).toFixed(1)}%
                          </span>
                        )}
                        {candidate.has_completed_oa && (
                          <>
                            {candidate.oa_percentage !== null && candidate.oa_percentage !== undefined && (
                              <span className="px-3 py-1 rounded-lg text-xs font-bold text-blue-700 bg-blue-50 border border-blue-200">
                                OA: {candidate.oa_percentage.toFixed(1)}%
                              </span>
                            )}
                            {candidate.max_cheating_score !== null && candidate.max_cheating_score !== undefined && (
                              <span className={`px-3 py-1 rounded-lg text-xs font-bold border ${
                                candidate.max_cheating_score < 30 
                                  ? 'text-green-700 bg-green-50 border-green-200'
                                  : candidate.max_cheating_score < 60
                                  ? 'text-yellow-700 bg-yellow-50 border-yellow-200'
                                  : 'text-red-700 bg-red-50 border-red-200'
                              }`}>
                                Integrity: {candidate.max_cheating_score.toFixed(1)}
                              </span>
                            )}
                          </>
                        )}
                        {candidate.job_title && (
                          <span className="px-3 py-1 rounded-lg text-xs font-bold text-gray-700 bg-gray-100 border border-gray-300">
                            {candidate.job_title}
                          </span>
                        )}
                      </div>
                      <p className="text-gray-700 text-sm mb-1">
                        {candidate.EMAIL}
                      </p>
                      {candidate.JOB_ID && (
                        <p className="text-gray-500 text-xs">
                          Job ID: {candidate.JOB_ID}
                        </p>
                      )}
                      {candidate.CREATED_AT && (
                        <p className="text-gray-500 text-xs mt-1">
                          Applied: {new Date(candidate.CREATED_AT).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => handleSendOA(candidate.ID)}
                        disabled={sendingOA === candidate.ID}
                        className="px-4 py-2 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-lg hover:from-sky-400 hover:to-blue-500 text-sm font-bold uppercase tracking-wider transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {sendingOA === candidate.ID ? 'Sending...' : 'Send OA'}
                      </button>
                      <Link
                        href={`/recruiter/candidates/${candidate.ID}`}
                        className="px-4 py-2 bg-gray-100 border border-sky-400/30 text-sky-400 rounded-lg hover:border-sky-400/50 hover:bg-sky-400/10 text-sm font-bold uppercase tracking-wider transition-all"
                      >
                        View Details
                      </Link>
                      <button
                        onClick={() => handleDeleteCandidate(candidate.ID)}
                        disabled={deletingCandidate === candidate.ID}
                        className="px-4 py-2 bg-red-900/30 border border-red-700 text-red-300 rounded-lg hover:border-red-500 hover:bg-red-900/50 text-sm font-bold uppercase tracking-wider transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {deletingCandidate === candidate.ID ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-6 py-12 text-center text-gray-500">
                No candidates found
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

