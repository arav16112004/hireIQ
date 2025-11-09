"use client";

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import apiClient from '@/lib/api';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function RecruiterDashboard() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [jobs, setJobs] = useState<any[]>([]);
  const [stats, setStats] = useState({ 
    totalCandidates: 0, 
    activeSessions: 0,
    pendingReviews: 0 
  });
  const [loading, setLoading] = useState(true);
  const [recentCandidates, setRecentCandidates] = useState<any[]>([]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }

    if (user && user.role === 'candidate') {
      router.push('/candidate/dashboard');
      return;
    }

    if (user) {
      fetchData();
    }
  }, [user, authLoading]);

  const fetchData = async () => {
    try {
      const [jobsRes, candidatesRes, sessionsRes] = await Promise.all([
        apiClient.jobs.getAll(),
        apiClient.candidates.getAll().catch(() => ({ data: { candidates: [] } })),
        apiClient.oaAdmin.getAllSessions().catch(() => ({ data: [] })),
      ]);

      const allCandidates = candidatesRes.data.candidates || [];
      const activeSessions = Array.isArray(sessionsRes.data) ? sessionsRes.data.length : 0;
      
      // Calculate pending reviews (candidates who have completed OA but not yet reviewed)
      const pendingReviews = allCandidates.filter(
        (c: any) => c.STAGE === 'oa_completed' || c.STAGE === 'interview'
      ).length;

      setJobs(jobsRes.data.jobs || []);
      setStats({
        totalCandidates: allCandidates.length,
        activeSessions: activeSessions,
        pendingReviews: pendingReviews,
      });
      
      // Get recent candidates (last 5)
      const recent = allCandidates
        .sort((a: any, b: any) => {
          const dateA = new Date(a.CREATED_AT || 0).getTime();
          const dateB = new Date(b.CREATED_AT || 0).getTime();
          return dateB - dateA;
        })
        .slice(0, 5);
      setRecentCandidates(recent);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
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
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Recruiter Dashboard</h1>
          <p className="text-gray-700 mt-2">
            Welcome back, <span className="font-semibold text-gray-900">{user?.name}</span> {user?.company_name && <span className="text-gray-500">from {user.company_name}</span>}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500 font-medium">Total Jobs</p>
                <p className="text-2xl font-bold text-gray-900">{jobs.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500 font-medium">Candidates</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalCandidates}</p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500 font-medium">Active Sessions</p>
                <p className="text-2xl font-bold text-gray-900">{stats.activeSessions}</p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500 font-medium">Pending Reviews</p>
                <p className="text-2xl font-bold text-gray-900">{stats.pendingReviews}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <Link
                href="/recruiter/candidates"
                className="block px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-center font-medium"
              >
                View All Candidates
              </Link>
              <Link
                href="/recruiter/jobs"
                className="block px-4 py-3 bg-gray-100 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-center font-medium"
              >
                Manage Jobs
              </Link>
              {user?.role === 'admin' && (
                <Link
                  href="/admin/oa-questions"
                  className="block px-4 py-3 bg-gray-100 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-center font-medium"
                >
                  Manage OA Questions
                </Link>
              )}
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Recent Candidates</h3>
            <div className="space-y-3">
              {recentCandidates.length > 0 ? (
                recentCandidates.map((candidate) => (
                  <Link
                    key={candidate.ID}
                    href={`/recruiter/candidates/${candidate.ID}`}
                    className="block p-3 bg-gray-50 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-semibold text-gray-900 text-sm">{candidate.NAME || 'Unknown'}</p>
                        <p className="text-gray-600 text-xs">{candidate.EMAIL}</p>
                      </div>
                      <span className="text-xs text-gray-500">
                        {candidate.CREATED_AT ? new Date(candidate.CREATED_AT).toLocaleDateString() : ''}
                      </span>
                    </div>
                  </Link>
                ))
              ) : (
                <p className="text-gray-500 text-sm">No recent candidates</p>
              )}
            </div>
          </div>
        </div>

        {/* Open Positions */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h2 className="text-xl font-bold text-gray-900">Open Positions</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {jobs.length > 0 ? (
              jobs.map((job) => (
                <div key={job.ID} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold text-gray-900">{job.TITLE}</h3>
                      <p className="text-sm text-gray-600 mt-1">{job.DEPARTMENT}</p>
                      <p className="text-sm text-gray-700 mt-2 line-clamp-2">{job.DESCRIPTION}</p>
                    </div>
                    <Link
                      href={`/recruiter/jobs/${job.ID}`}
                      className="ml-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium transition-colors"
                    >
                      View Details
                    </Link>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-6 py-12 text-center text-gray-500">
                No open positions
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
