"use client";

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import apiClient from '@/lib/api';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function JobsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [jobs, setJobs] = useState<any[]>([]);
  const [filteredJobs, setFilteredJobs] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }

    if (user) {
      fetchJobs();
    }
  }, [user, authLoading]);

  const fetchJobs = async () => {
    try {
      const response = await apiClient.jobs.getAll();
      const jobsList = response.data.jobs || [];
      setJobs(jobsList);
      setFilteredJobs(jobsList);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredJobs(jobs);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = jobs.filter((job) => {
        const title = (job.TITLE || '').toLowerCase();
        const department = (job.DEPARTMENT || '').toLowerCase();
        const description = (job.DESCRIPTION || '').toLowerCase();
        return title.includes(query) || department.includes(query) || description.includes(query);
      });
      setFilteredJobs(filtered);
    }
  }, [searchQuery, jobs]);

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-400 mx-auto"></div>
          <p className="mt-4 text-gray-700">Loading jobs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2 drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">
            Browse Jobs
          </h1>
          <p className="text-gray-700">Find your next opportunity</p>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search jobs by title, department, or description..."
              className="w-full pl-12 pr-4 py-4 bg-white/80 backdrop-blur-md border-2 border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 hover:border-sky-400/50 transition-all shadow placeholder-gray-400"
            />
          </div>
          {searchQuery && (
            <p className="mt-2 text-sm text-sky-600">
              Found {filteredJobs.length} job{filteredJobs.length !== 1 ? 's' : ''} matching "{searchQuery}"
            </p>
          )}
        </div>

        {/* Jobs List */}
        <div className="space-y-4">
          {filteredJobs.length > 0 ? (
            filteredJobs.map((job) => (
              <div
                key={job.ID}
                className="bg-white/80 backdrop-blur-md border-2 border-gray-200 rounded-xl shadow-lg p-6 hover:border-gray-300 hover:shadow-lg transition-all"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <h3 className="text-2xl font-bold text-gray-900">
                        {job.TITLE}
                      </h3>
                      <span className="px-3 py-1 rounded-lg text-xs font-medium bg-sky-50 text-sky-700 border border-sky-200">
                        {job.DEPARTMENT}
                      </span>
                    </div>
                    <p className="text-gray-700 mb-4 line-clamp-3">
                      {job.DESCRIPTION}
                    </p>
                    {job.CREATED_AT && (
                      <p className="text-xs text-gray-500">
                        Posted {new Date(job.CREATED_AT).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                  <Link
                    href="/apply"
                    className="ml-6 px-6 py-3 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-lg hover:from-sky-400 hover:to-blue-500 text-sm font-bold uppercase tracking-wider whitespace-nowrap transition-all shadow-lg ring-1 ring-sky-400/40 hover:shadow-sky-500/30 hover:scale-105"
                  >
                    Apply Now
                  </Link>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-16">
              <div className="bg-white/80 backdrop-blur-md border-2 border-gray-200 rounded-xl p-12">
                <svg className="h-16 w-16 text-sky-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="text-xl font-bold text-gray-700 mb-2">
                  {searchQuery ? 'No jobs found' : 'No jobs available'}
                </h3>
                <p className="text-gray-500">
                  {searchQuery
                    ? `Try a different search term or check back later.`
                    : 'Check back later for new opportunities.'}
                </p>
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="mt-4 px-4 py-2 text-sm text-sky-400 hover:text-sky-600 underline"
                  >
                    Clear search
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

