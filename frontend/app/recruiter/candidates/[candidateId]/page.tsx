"use client";

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import apiClient from '@/lib/api';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';

export default function CandidateDetailPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const candidateId = parseInt(params.candidateId as string);
  
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [sendingOA, setSendingOA] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }

    if (user && user.role !== 'recruiter' && user.role !== 'admin') {
      router.push('/candidate/dashboard');
      return;
    }

    if (user && candidateId) {
      fetchCandidateDetails();
    }
  }, [user, authLoading, candidateId]);

  const fetchCandidateDetails = async () => {
    try {
      const res = await apiClient.recruiter.getCandidateDetails(candidateId);
      setData(res.data);
      // Log integrity score for debugging
      console.log('📊 Candidate Details:', {
        candidateId,
        maxCheatingScore: res.data.max_cheating_score,
        oaScore: res.data.oa_score,
        oaResult: res.data.oa_result,
        oaSessions: res.data.oa_sessions?.map((s: any) => ({
          id: s.ID || s.id,
          maxCheatingScore: s.MAX_CHEATING_SCORE || s.max_cheating_score,
          status: s.STATUS || s.status
        }))
      });
    } catch (error: any) {
      console.error('Failed to fetch candidate details:', error);
      if (error.response?.status === 404) {
        setData(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSendOA = async () => {
    if (!confirm('Send OA invitation to this candidate?')) return;
    
    setSendingOA(true);
    try {
      await apiClient.candidates.sendOA(candidateId, false);
      alert('OA invitation sent successfully!');
      fetchCandidateDetails();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to send OA invitation');
    } finally {
      setSendingOA(false);
    }
  };

  const getCheatingScoreLabel = (score: number | null | undefined) => {
    if (score === null || score === undefined) return 'No Data';
    if (score < 30) return 'Low Risk';
    if (score < 60) return 'Medium Risk';
    return 'High Risk';
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (!data || !data.candidate) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-gray-900 mb-4">Candidate not found</h1>
          <Link href="/recruiter/candidates" className="text-blue-600 hover:text-blue-700">
            Back to Candidates
          </Link>
        </div>
      </div>
    );
  }

  const candidate = data.candidate;
  const profile = data.profile || {};
  const maxCheatingScore = data.max_cheating_score;
  const oaScore = data.oa_score;
  const oaMaxScore = data.oa_max_score;
  const oaPercentage = data.oa_percentage;
  const job = data.job;
  const oaSessions = data.oa_sessions || [];

  // Parse skills if it's an array or string
  let skills: string[] = [];
  if (profile.SKILLS) {
    if (Array.isArray(profile.SKILLS)) {
      skills = profile.SKILLS;
    } else if (typeof profile.SKILLS === 'string') {
      try {
        skills = JSON.parse(profile.SKILLS);
      } catch {
        skills = profile.SKILLS.split(',').map((s: string) => s.trim());
      }
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/recruiter/candidates"
            className="text-gray-600 hover:text-gray-900 mb-4 inline-block text-sm font-medium"
          >
            ← Back to Candidates
          </Link>
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-3xl font-semibold text-gray-900 mb-2">
                {candidate.NAME || candidate.name || 'Unknown Candidate'}
              </h1>
              <p className="text-gray-600">{candidate.EMAIL || candidate.email}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSendOA}
                disabled={sendingOA}
                className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sendingOA ? 'Sending...' : 'Send OA'}
              </button>
            </div>
          </div>
        </div>

        {/* Scores Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* OA Score */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h2 className="text-sm font-medium text-gray-700 mb-4 uppercase tracking-wide">
              OA Score
            </h2>
            {oaScore !== null && oaScore !== undefined && oaMaxScore !== null && oaMaxScore !== undefined ? (
              <div>
                <div className="text-3xl font-semibold text-gray-900 mb-2">
                  {oaPercentage !== null && oaPercentage !== undefined
                    ? `${oaPercentage.toFixed(1)}%`
                    : `${oaScore}/${oaMaxScore}`}
                </div>
                <div className="text-sm text-gray-500">
                  {oaScore} / {oaMaxScore} points
                </div>
              </div>
            ) : (
              <div className="text-gray-500 text-sm">No OA completed yet</div>
            )}
          </div>

          {/* Integrity Score */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h2 className="text-sm font-medium text-gray-700 mb-4 uppercase tracking-wide">
              Integrity Score
            </h2>
            {maxCheatingScore !== null && maxCheatingScore !== undefined ? (
              <div>
                <div className={`text-3xl font-semibold mb-2 ${
                  maxCheatingScore < 30 ? 'text-green-600' : 
                  maxCheatingScore < 60 ? 'text-yellow-600' : 
                  'text-red-600'
                }`}>
                  {maxCheatingScore.toFixed(1)}
                </div>
                <div className={`text-sm font-medium ${
                  maxCheatingScore < 30 ? 'text-green-600' : 
                  maxCheatingScore < 60 ? 'text-yellow-600' : 
                  'text-red-600'
                }`}>
                  {getCheatingScoreLabel(maxCheatingScore)}
                </div>
                <div className="text-xs text-gray-500 mt-2">
                  Higher score indicates higher risk
                </div>
              </div>
            ) : (
              <div className="text-gray-500 text-sm">No integrity data available</div>
            )}
          </div>

          {/* Fit Score */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h2 className="text-sm font-medium text-gray-700 mb-4 uppercase tracking-wide">
              Fit Score
            </h2>
            {candidate.FIT_SCORE || candidate.fit_score ? (
              <div>
                <div className="text-3xl font-semibold text-gray-900 mb-2">
                  {parseFloat(candidate.FIT_SCORE || candidate.fit_score || '0').toFixed(1)}%
                </div>
                <div className="text-sm text-gray-500">
                  Match with job requirements
                </div>
              </div>
            ) : (
              <div className="text-gray-500 text-sm">No fit score available</div>
            )}
          </div>
        </div>

        {/* Candidate Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide mb-4">
              Candidate Information
            </h2>
            <div className="space-y-4">
              <div>
                <p className="text-xs text-gray-500 mb-1">Stage</p>
                <span className={`inline-block px-3 py-1 rounded-md text-xs font-medium uppercase tracking-wide border ${
                  (candidate.STAGE || candidate.stage || 'applied').toLowerCase() === 'applied' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                  (candidate.STAGE || candidate.stage || 'applied').toLowerCase() === 'oa_sent' ? 'bg-cyan-50 text-cyan-700 border-cyan-200' :
                  (candidate.STAGE || candidate.stage || 'applied').toLowerCase() === 'oa_completed' || (candidate.STAGE || candidate.stage || 'applied').toLowerCase() === 'oa_passed' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                  (candidate.STAGE || candidate.stage || 'applied').toLowerCase() === 'interview' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                  (candidate.STAGE || candidate.stage || 'applied').toLowerCase() === 'accepted' ? 'bg-green-50 text-green-700 border-green-200' :
                  (candidate.STAGE || candidate.stage || 'applied').toLowerCase() === 'rejected' ? 'bg-red-50 text-red-700 border-red-200' :
                  'bg-gray-50 text-gray-700 border-gray-200'
                }`}>
                  {candidate.STAGE || candidate.stage || 'applied'}
                </span>
              </div>
              {job && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Job</p>
                  <p className="text-sm font-medium text-gray-900">{job.TITLE || job.title}</p>
                </div>
              )}
              {candidate.JOB_ID || candidate.job_id ? (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Job ID</p>
                  <p className="text-sm font-medium text-gray-900">{candidate.JOB_ID || candidate.job_id}</p>
                </div>
              ) : null}
              {candidate.CREATED_AT || candidate.created_at ? (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Applied Date</p>
                  <p className="text-sm font-medium text-gray-900">
                    {new Date(candidate.CREATED_AT || candidate.created_at).toLocaleDateString()}
                  </p>
                </div>
              ) : null}
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide mb-4">
              Contact Information
            </h2>
            <div className="space-y-4">
              {profile.PHONE || profile.phone ? (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Phone</p>
                  <p className="text-sm font-medium text-gray-900">{profile.PHONE || profile.phone}</p>
                </div>
              ) : (
                <div className="text-sm text-gray-400">No phone provided</div>
              )}
              {profile.LOCATION || profile.location ? (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Location</p>
                  <p className="text-sm font-medium text-gray-900">{profile.LOCATION || profile.location}</p>
                </div>
              ) : null}
              {profile.LINKEDIN_URL || profile.linkedin_url ? (
                <div>
                  <p className="text-xs text-gray-500 mb-1">LinkedIn</p>
                  <a
                    href={profile.LINKEDIN_URL || profile.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:text-blue-700 underline"
                  >
                    View Profile
                  </a>
                </div>
              ) : null}
              {profile.PORTFOLIO_URL || profile.portfolio_url ? (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Portfolio</p>
                  <a
                    href={profile.PORTFOLIO_URL || profile.portfolio_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:text-blue-700 underline"
                  >
                    View Portfolio
                  </a>
                </div>
              ) : null}
            </div>
          </div>
        </div>

        {/* Profile Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Skills and Experience */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide mb-4">
              Skills & Experience
            </h2>
            <div className="space-y-4">
              {skills.length > 0 ? (
                <div>
                  <p className="text-xs text-gray-500 mb-2">Skills</p>
                  <div className="flex flex-wrap gap-2">
                    {skills.map((skill: string, index: number) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-gray-100 text-gray-800 rounded-md text-xs font-medium border border-gray-200"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-400">No skills listed</div>
              )}
              {profile.EXPERIENCE_YEARS || profile.experience_years ? (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Experience</p>
                  <p className="text-sm font-medium text-gray-900">
                    {profile.EXPERIENCE_YEARS || profile.experience_years} years
                  </p>
                </div>
              ) : null}
              {profile.EDUCATION || profile.education ? (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Education</p>
                  <p className="text-sm font-medium text-gray-900">{profile.EDUCATION || profile.education}</p>
                </div>
              ) : null}
            </div>
          </div>

          {/* Bio and Description */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide mb-4">
              About
            </h2>
            <div className="space-y-4">
              {profile.BIO || profile.bio ? (
                <div>
                  <p className="text-xs text-gray-500 mb-2">Bio</p>
                  <p className="text-sm text-gray-700 leading-relaxed">{profile.BIO || profile.bio}</p>
                </div>
              ) : null}
              {profile.DESCRIPTION || profile.description ? (
                <div>
                  <p className="text-xs text-gray-500 mb-2">Resume Summary</p>
                  <p className="text-sm text-gray-700 leading-relaxed">{profile.DESCRIPTION || profile.description}</p>
                </div>
              ) : null}
              {!(profile.BIO || profile.bio || profile.DESCRIPTION || profile.description) && (
                <div className="text-sm text-gray-400">No additional information provided</div>
              )}
            </div>
          </div>
        </div>

        {/* Resume */}
        {(candidate.RESUME_URL || candidate.resume_url || profile.RESUME_URL || profile.resume_url) && (
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 mb-8">
            <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide mb-4">
              Resume
            </h2>
            <a
              href={candidate.RESUME_URL || candidate.resume_url || profile.RESUME_URL || profile.resume_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-700 underline"
            >
              View Resume
            </a>
          </div>
        )}

        {/* OA Sessions */}
        {oaSessions.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide mb-4">
              OA Sessions
            </h2>
            <div className="space-y-4">
              {oaSessions.map((session: any, index: number) => {
                const sessionStatus = session.STATUS || session.status || 'unknown';
                const sessionScore = session.SCORE || session.score;
                const sessionMaxScore = session.MAX_SCORE || session.max_score;
                const sessionCheatingScore = session.MAX_CHEATING_SCORE || session.max_cheating_score;
                const sessionPercentage = sessionScore && sessionMaxScore && sessionMaxScore > 0
                  ? ((sessionScore / sessionMaxScore) * 100).toFixed(1)
                  : null;
                
                return (
                  <div
                    key={session.ID || session.id || index}
                    className="bg-gray-50 border border-gray-200 rounded-lg p-4"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          Session #{session.ID || session.id || index + 1}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {session.CREATED_AT || session.created_at
                            ? new Date(session.CREATED_AT || session.created_at).toLocaleString()
                            : 'Unknown date'}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded-md text-xs font-medium uppercase ${
                        sessionStatus.toLowerCase() === 'completed' || sessionStatus.toLowerCase() === 'COMPLETED' ? 'bg-green-50 text-green-700 border border-green-200' :
                        sessionStatus.toLowerCase() === 'pending' || sessionStatus.toLowerCase() === 'PENDING' ? 'bg-yellow-50 text-yellow-700 border border-yellow-200' :
                        'bg-gray-50 text-gray-700 border border-gray-200'
                      }`}>
                        {sessionStatus}
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      {sessionScore !== null && sessionScore !== undefined && sessionMaxScore !== null && sessionMaxScore !== undefined ? (
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Score</p>
                          <p className="text-sm font-medium text-gray-900">
                            {sessionScore} / {sessionMaxScore}
                            {sessionPercentage && ` (${sessionPercentage}%)`}
                          </p>
                        </div>
                      ) : (
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Score</p>
                          <p className="text-sm text-gray-400">N/A</p>
                        </div>
                      )}
                      {sessionCheatingScore !== null && sessionCheatingScore !== undefined ? (
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Integrity</p>
                          <p className={`text-sm font-medium ${
                            sessionCheatingScore < 30 ? 'text-green-600' : 
                            sessionCheatingScore < 60 ? 'text-yellow-600' : 
                            'text-red-600'
                          }`}>
                            {sessionCheatingScore.toFixed(1)}
                          </p>
                        </div>
                      ) : (
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Integrity</p>
                          <p className="text-sm text-gray-400">N/A</p>
                        </div>
                      )}
                      {session.COMPLETED_AT || session.completed_at ? (
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Completed</p>
                          <p className="text-xs text-gray-700">
                            {new Date(session.COMPLETED_AT || session.completed_at).toLocaleString()}
                          </p>
                        </div>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
