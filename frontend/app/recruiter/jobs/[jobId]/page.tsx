"use client";

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import apiClient from '@/lib/api';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';

export default function JobDetailPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const jobId = parseInt(params.jobId as string);
  
  const [job, setJob] = useState<any>(null);
  const [candidates, setCandidates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sendingOA, setSendingOA] = useState<number | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }

    if (user && user.role !== 'recruiter' && user.role !== 'admin') {
      router.push('/candidate/dashboard');
      return;
    }

    if (user && jobId) {
      fetchData();
    }
  }, [user, authLoading, jobId]);

  const fetchData = async () => {
    try {
      const [jobRes, candidatesRes] = await Promise.all([
        apiClient.jobs.getById(jobId),
        apiClient.jobs.getCandidates(jobId),
      ]);

      setJob(jobRes.data);
      setCandidates(candidatesRes.data.candidates || []);
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

  if (!job) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-400 mb-4">Job not found</h1>
          <Link href="/recruiter/jobs" className="text-cyan-400 hover:text-cyan-300">
            Back to Jobs
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/recruiter/jobs"
            className="text-sky-400 hover:text-sky-300 mb-4 inline-block font-bold uppercase tracking-wider"
          >
            ← Back to Jobs
          </Link>
          <h1 className="text-3xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2 drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">
            {job.TITLE}
          </h1>
          <p className="text-gray-500 text-sm mb-4">
            <span className="text-sky-400 font-bold">Department:</span> {job.DEPARTMENT}
          </p>
          <div className="bg-white/80 backdrop-blur-md border-2 border-gray-200 rounded-xl shadow-[0_0_30px_rgba(56,189,248,0.15)] p-6 mb-4">
            <h2 className="text-lg font-bold text-gray-900 uppercase tracking-wider mb-2">
              Description
            </h2>
            <p className="text-gray-700 whitespace-pre-wrap">
              {job.DESCRIPTION}
            </p>
          </div>
          {(job.COMPANY_PRINCIPLES || job.company_principles) && (
            <div className="bg-white/80 backdrop-blur-md border-2 border-sky-200 rounded-xl shadow-[0_0_30px_rgba(56,189,248,0.15)] p-6">
              <h2 className="text-lg font-bold text-gray-900 uppercase tracking-wider mb-2">
                Company Principles
                <span className="text-xs font-normal text-gray-500 ml-2">(For AI Avatar Video Interviews)</span>
              </h2>
              <p className="text-gray-700 whitespace-pre-wrap">
                {job.COMPANY_PRINCIPLES || job.company_principles}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                These principles will be used by the AI avatar to ask relevant questions and assess candidate fit during video interviews.
              </p>
            </div>
          )}
        </div>

        {/* Candidates Section */}
        <div className="bg-white/80 backdrop-blur-md border-2 border-gray-200 rounded-xl shadow-[0_0_30px_rgba(56,189,248,0.15)] overflow-hidden">
          <div className="px-6 py-4 border-b-2 border-gray-200 bg-sky-900/10">
            <h2 className="text-xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">
              Candidates ({candidates.length})
            </h2>
          </div>
          <div className="divide-y divide-sky-400/20">
            {candidates.length > 0 ? (
              candidates.map((candidate) => (
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
                      </div>
                      <p className="text-gray-700 text-sm mb-1">
                        {candidate.EMAIL}
                      </p>
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
                        className="px-4 py-2 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-lg hover:from-sky-400 hover:to-blue-500 text-sm font-bold uppercase tracking-wider shadow-[0_0_20px_rgba(56,189,248,0.4)] hover:shadow-[0_0_30px_rgba(56,189,248,0.6)] hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {sendingOA === candidate.ID ? 'Sending...' : 'Send OA'}
                      </button>
                      <Link
                        href={`/recruiter/candidates/${candidate.ID}`}
                        className="px-4 py-2 bg-gray-100 border-2 border-gray-200 text-sky-400 rounded-lg hover:border-sky-400/50 hover:bg-sky-400/10 text-sm font-bold uppercase tracking-wider transition-all"
                      >
                        View Details
                      </Link>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-6 py-12 text-center text-gray-500">
                No candidates for this job yet
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

