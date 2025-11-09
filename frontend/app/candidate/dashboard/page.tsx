"use client";

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import apiClient from '@/lib/api';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function CandidateDashboard() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [oaSessions, setOaSessions] = useState<any[]>([]);
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }

    if (user && user.role !== 'candidate') {
      router.push('/recruiter/dashboard');
      return;
    }

    if (user) {
      setDataLoading(false); // Show page immediately
      fetchData(); // Load data in background
    }
  }, [user, authLoading]);

  const fetchData = async () => {
    try {
      setDataLoading(true);
      // Fetch all data in parallel, but don't block rendering
      const [profileRes, jobsRes, oaRes] = await Promise.all([
        apiClient.profile.get().catch((err) => {
          console.error('Failed to fetch profile:', err);
          return null;
        }),
        apiClient.jobs.getAll().catch((err) => {
          console.error('Failed to fetch jobs:', err);
          return { data: { jobs: [] } };
        }),
        apiClient.oa.getMySessions().catch((err) => {
          console.error('❌ Failed to fetch OA sessions:', err);
          console.error('Error status:', err.response?.status);
          console.error('Error details:', err.response?.data || err.message);
          console.error('Full error:', err);
          // Return empty sessions but preserve structure
          return { data: { sessions: [], message: err.response?.data?.message || err.message } };
        }),
      ]);

      if (profileRes) setProfile(profileRes.data);
      if (jobsRes) setJobs(jobsRes.data.jobs || []);
      // Log the raw response first
      console.log('=== OA SESSIONS RAW RESPONSE ===');
      console.log('oaRes:', oaRes);
      console.log('oaRes.data:', oaRes?.data);
      console.log('oaRes.status:', oaRes?.status);
      console.log('oaRes.statusText:', oaRes?.statusText);
      
      if (oaRes && oaRes.data) {
        console.log('=== OA SESSIONS API RESPONSE ===');
        console.log('Full response:', JSON.stringify(oaRes, null, 2));
        console.log('Response data:', JSON.stringify(oaRes.data, null, 2));
        
        // Handle both response formats: {sessions: []} and {data: {sessions: []}}
        const sessions = oaRes.data?.sessions || oaRes.data?.data?.sessions || [];
        console.log('Sessions array:', sessions);
        console.log('Sessions count:', sessions.length);
        console.log('Candidate ID:', oaRes.data?.candidate_id);
        console.log('User Email:', oaRes.data?.user_email);
        console.log('Message:', oaRes.data?.message);
        
        if (oaRes.data?.message) {
          console.warn('⚠️ OA sessions message:', oaRes.data.message);
          // Show message to user if there's one
          if (oaRes.data.message.includes('No candidate record found')) {
            console.error('❌ ISSUE: No candidate record found for email:', user?.email);
            console.error('   This means you need to apply for a job first to create a candidate record');
          }
        }
        
        console.log('Setting sessions to state:', sessions);
        setOaSessions(sessions);
        
        if (sessions.length === 0) {
          console.warn('⚠️ No OA sessions found. Possible reasons:');
          console.warn('  1. User email might not match any candidate record');
          console.warn('  2. No OA sessions have been created for this candidate');
          console.warn('  3. Candidate might need to apply for a job first');
          console.warn('  4. OA sessions exist but for a different candidate_id');
        } else {
          console.log('✅ Successfully loaded', sessions.length, 'OA session(s)');
        }
      } else {
        console.error('❌ No OA response data received');
        console.error('oaRes:', oaRes);
        setOaSessions([]);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setDataLoading(false);
    }
  };

  // Show loading only for auth, not for data
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-400 mx-auto"></div>
          <p className="mt-4 text-gray-700">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-12">
          <div className="relative overflow-hidden rounded-2xl border border-gray-200 bg-gray-50 md:shadow-lg">
            <div className="absolute inset-0 opacity-30" aria-hidden="true">
              <div className="h-24 w-full bg-gradient-to-r from-sky-100 via-blue-100 to-cyan-100"></div>
            </div>
            <div className="relative px-6 py-8 sm:px-8">
              <div className="flex items-start justify-between gap-6">
                <div className="max-w-2xl">
                  <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-medium text-sky-700">
                    <span className="h-1.5 w-1.5 rounded-full bg-sky-500 shadow-[0_0_10px_rgba(56,189,248,0.8)]"></span>
                    Candidate Dashboard
                  </div>
                  <h1 className="mt-3 text-4xl font-semibold tracking-tight text-gray-900">
                    Welcome back, <span className="bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">{user?.name || '...'}</span>
                  </h1>
                  <p className="mt-2 text-gray-700">Track your assessments and applications in one place.</p>
                  <div className="mt-5 flex flex-wrap items-center gap-3">
                    <span className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-medium text-sky-700">
                      <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 7V6a2 2 0 012-2h8a2 2 0 012 2v1M6 7h12M6 7l-2 5h16l-2-5M6 12v4a2 2 0 002 2h8a2 2 0 002-2v-4" />
                      </svg>
                      {jobs.length > 0 ? `${jobs.length} openings` : 'Loading...'}
                    </span>
                    <span className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                      <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3M3 11h18M5 19h14a2 2 0 002-2v-6H3v6a2 2 0 002 2z" />
                      </svg>
                      {oaSessions.length > 0 ? `${oaSessions.length} assessments` : 'Loading...'}
                    </span>
                    {(oaSessions.some((s: any) => {
                      const status = s.STATUS || s.status || '';
                      return status === 'in_progress' || status === 'IN_PROGRESS' || status === 'pending' || status === 'PENDING';
                    })) && (() => {
                      const activeSession = oaSessions.find((s: any) => {
                        const status = s.STATUS || s.status || '';
                        return status === 'in_progress' || status === 'IN_PROGRESS' || status === 'pending' || status === 'PENDING';
                      });
                      const sessionId = activeSession?.ID || activeSession?.id || activeSession?.SESSION_ID || activeSession?.session_id;
                      return sessionId ? (
                        <Link
                          href={`/oa/${sessionId}`}
                          className="ml-auto inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 px-4 py-2 text-sm font-medium text-white shadow-lg ring-1 ring-sky-400/40 hover:from-sky-400 hover:to-blue-500 hover:shadow-sky-500/30 transition"
                        >
                          Continue assessment
                          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </Link>
                      ) : null;
                    })()}
                  </div>
                </div>
                <div className="hidden sm:flex flex-col items-end gap-3">
                  <div className="rounded-xl border border-gray-200 bg-white px-4 py-3 shadow">
                    <p className="text-xs font-medium text-gray-500">Today</p>
                    <p className="text-sm font-semibold text-gray-900">
                      {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Profile Completion Alert - Only show if profile is empty */}
        {profile && (() => {
          // Check if user has filled out any profile fields
          const hasProfileData = !!(
            (profile.phone && profile.phone.trim()) ||
            (profile.location && profile.location.trim()) ||
            (profile.skills && profile.skills.trim()) ||
            (profile.education && profile.education.trim()) ||
            (profile.bio && profile.bio.trim()) ||
            (profile.linkedin_url && profile.linkedin_url.trim()) ||
            (profile.portfolio_url && profile.portfolio_url.trim()) ||
            profile.resume_url
          );
          
          // Only show alert if profile is empty (no data filled)
          return !hasProfileData;
        })() && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start shadow-sm">
            <svg className="w-5 h-5 text-amber-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div className="flex-1">
              <p className="text-amber-800 font-medium">Complete your profile to get better job matches</p>
              <Link href="/candidate/profile" className="text-amber-700 underline text-sm mt-1 inline-block hover:text-amber-900">
                Update Profile →
              </Link>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-10">
          {/* Quick Actions */}
          <div className="bg-white border border-gray-200 rounded-xl shadow p-6 hover:shadow-lg transition-all">
            <div className="flex items-center gap-3 mb-5">
              <div className="p-2.5 bg-sky-100 rounded-lg border border-sky-200">
                <svg className="w-5 h-5 text-sky-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-900">Quick Actions</h3>
            </div>
            <div className="space-y-2.5">
              <Link href="/apply" className="block px-5 py-3 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-lg hover:from-sky-400 hover:to-blue-500 transition-all text-center font-medium text-sm shadow-lg ring-1 ring-sky-400/40 hover:shadow-sky-500/30">
                Apply for a Job
              </Link>
              <Link href="/candidate/profile" className="block px-5 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all text-center font-medium text-sm border border-gray-300">
                Update Profile
              </Link>
            </div>
          </div>

          {/* Profile Overview */}
          <div className="bg-white border border-gray-200 rounded-xl shadow p-6 hover:shadow-lg transition-all">
            <div className="flex items-center gap-3 mb-5">
              <div className="p-2.5 bg-cyan-100 rounded-lg border border-cyan-200">
                <svg className="w-5 h-5 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-900">Profile Overview</h3>
            </div>
            <div className="space-y-3.5">
              <div className="rounded-lg p-4 border border-gray-200 bg-gray-50">
                <p className="text-xs text-gray-500 font-medium mb-1">Email</p>
                <p className="font-medium text-gray-900 text-sm">{user?.email}</p>
              </div>
              {profile?.skills && (
                <div className="rounded-lg p-4 border border-gray-200 bg-gray-50">
                  <p className="text-xs text-gray-500 font-medium mb-1">Skills</p>
                  <p className="text-sm text-gray-900">{profile.skills.substring(0, 50)}...</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* OA Assessments */}
        <div className="bg-white border border-gray-200 rounded-xl shadow mb-10 overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Your Assessments
            </h2>
          </div>
          <div className="divide-y divide-gray-200">
            {dataLoading ? (
              <div className="px-6 py-12 text-center text-gray-500">
                Loading assessments...
              </div>
            ) : (() => {
              console.log('Rendering OA sessions section. Sessions count:', oaSessions.length);
              console.log('Sessions data:', oaSessions);
              return oaSessions.length > 0 ? (
              oaSessions.map((session) => {
                const status = session.STATUS || session.status || 'pending';
                const isPending = status === 'pending' || status === 'PENDING';
                const isInProgress = status === 'in_progress' || status === 'IN_PROGRESS' || status === 'in_progress';
                const isCompleted = status === 'completed' || status === 'COMPLETED';
                
                let statusColor = 'bg-gray-100 text-gray-700 border border-gray-300';
                let statusText = status;
                
                if (isPending) {
                  statusColor = 'bg-amber-50 text-amber-700 border border-amber-200';
                  statusText = 'Not Started';
                } else if (isInProgress) {
                  statusColor = 'bg-sky-50 text-sky-700 border border-sky-200';
                  statusText = 'In Progress';
                } else if (isCompleted) {
                  statusColor = 'bg-emerald-50 text-emerald-700 border border-emerald-200';
                  statusText = 'Completed';
                }
                
                const sessionId = session.ID || session.id || session.SESSION_ID || session.session_id;
                const duration = session.DURATION_MINUTES || session.duration_minutes || 60;
                const questionIds = session.QUESTION_IDS || session.question_ids || [];
                const createdAt = session.CREATED_AT || session.created_at;
                
                if (!sessionId) {
                  console.error('Session missing ID:', session);
                  return null;
                }
                
                return (
                  <div key={sessionId} className="px-6 py-5 hover:bg-gray-50 transition-colors">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <h3 className="font-semibold text-gray-900">
                            Online Assessment #{sessionId}
                          </h3>
                          <span className={`px-3 py-1 rounded-lg text-xs font-medium ${statusColor}`}>
                            {statusText}
                          </span>
                        </div>
                        <div className="flex gap-5">
                          <div className="px-3 py-2 rounded-lg border border-gray-200 bg-gray-50">
                            <p className="text-xs text-gray-500 mb-0.5 font-medium">Duration</p>
                            <p className="text-sm font-semibold text-gray-900">{duration} min</p>
                          </div>
                          <div className="px-3 py-2 rounded-lg border border-gray-200 bg-gray-50">
                            <p className="text-xs text-gray-500 mb-0.5 font-medium">Questions</p>
                            <p className="text-sm font-semibold text-gray-900">{Array.isArray(questionIds) ? questionIds.length : 0}</p>
                          </div>
                          {createdAt && (
                            <div className="px-3 py-2 rounded-lg border border-gray-200 bg-gray-50">
                              <p className="text-xs text-gray-500 mb-0.5 font-medium">Sent</p>
                              <p className="text-sm font-semibold text-gray-900">{new Date(createdAt).toLocaleDateString()}</p>
                            </div>
                          )}
                        </div>
                      </div>
                      {!isCompleted && (
                        <Link
                          href={`/oa/${sessionId}`}
                          className="ml-6 px-6 py-2.5 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-lg hover:from-sky-400 hover:to-blue-500 text-sm font-medium whitespace-nowrap transition-all shadow-lg ring-1 ring-sky-400/40 hover:shadow-sky-500/30"
                        >
                          {isPending ? 'Start Assessment' : 'Continue'}
                        </Link>
                      )}
                      {isCompleted && (
                        <Link
                          href={`/oa/results/${sessionId}`}
                          className="ml-6 px-6 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-lg hover:from-emerald-400 hover:to-teal-500 text-sm font-medium whitespace-nowrap transition-all shadow-lg ring-1 ring-emerald-400/30"
                        >
                          View Results
                        </Link>
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="px-6 py-12 text-center">
                <p className="text-gray-500 mb-2">No assessments yet</p>
                <p className="text-sm text-gray-400">
                  Assessments will appear here once you apply for a job and qualify.
                </p>
                {/* Debug info - always show in development */}
                <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded text-left text-xs">
                  <p className="font-semibold mb-2 text-yellow-800">Debug Info:</p>
                  <p className="text-yellow-700">User Email: {user?.email}</p>
                  <p className="text-yellow-700">Sessions Count: {oaSessions.length}</p>
                  <p className="text-yellow-700">Data Loading: {dataLoading ? 'Yes' : 'No'}</p>
                  <p className="text-yellow-700 mt-2">Check browser console (F12) for detailed API response.</p>
                  <p className="text-yellow-600 text-xs mt-2">
                    💡 If sessions count is 0, check backend logs to see if:
                    <br />1. Candidate record exists for your email
                    <br />2. OA sessions exist for that candidate
                  </p>
                </div>
              </div>
            );
            })()}
          </div>
        </div>

        {/* Available Jobs */}
        <div className="bg-white border border-gray-200 rounded-xl shadow">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Available Positions</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {jobs.length > 0 ? (
              jobs.map((job) => (
                <div key={job.ID} className="px-6 py-5 hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold text-gray-900">{job.TITLE}</h3>
                      <p className="text-sm text-gray-600 mt-1">{job.DEPARTMENT}</p>
                      <p className="text-sm text-gray-700 mt-2 line-clamp-2">{job.DESCRIPTION}</p>
                    </div>
                    <Link
                      href="/apply"
                      className="ml-4 px-6 py-2.5 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-lg hover:from-sky-400 hover:to-blue-500 text-sm font-medium whitespace-nowrap transition-all shadow-lg ring-1 ring-sky-400/40 hover:shadow-sky-500/30"
                    >
                      Apply Now
                    </Link>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-6 py-12 text-center text-gray-500">
                No jobs available at the moment
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

