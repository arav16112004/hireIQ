"use client";

import Link from 'next/link';
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api';

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...');

  useEffect(() => {
    // Check backend health
    apiClient.health()
      .then(res => setHealthStatus(res.data.status))
      .catch(() => setHealthStatus('offline'));
  }, []);

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <div className="mb-4">
            <span className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-bold uppercase tracking-wider border-2 ${
              healthStatus === 'healthy' 
                ? 'bg-green-100 border-green-400 text-green-700 shadow-[0_0_20px_rgba(34,197,94,0.2)]' 
                : 'bg-red-100 border-red-400 text-red-700 shadow-[0_0_20px_rgba(239,68,68,0.2)]'
            }`}>
              <span className={`w-2 h-2 rounded-full mr-2 ${
                healthStatus === 'healthy' ? 'bg-green-600' : 'bg-red-600'
              }`} />
              Backend: {healthStatus}
            </span>
          </div>

          <h1 className="text-5xl md:text-6xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-tight mb-6 drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">
            Transform Your Hiring with
            <span className="block">
              AI-Powered Assessments
            </span>
          </h1>
          
          <p className="text-xl text-gray-700 mb-12 max-w-2xl mx-auto">
            Screen candidates faster, assess skills accurately, and make better hiring decisions with our intelligent platform.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              href="/apply"
              className="px-8 py-4 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-lg hover:from-sky-400 hover:to-blue-500 font-black uppercase tracking-wider text-lg shadow-[0_0_20px_rgba(56,189,248,0.4)] hover:shadow-[0_0_30px_rgba(56,189,248,0.6)] hover:scale-105 transition-all ring-2 ring-sky-400/30"
            >
              Apply as Candidate
            </Link>
            <Link 
              href="/recruiter/dashboard"
              className="px-8 py-4 bg-transparent border-2 border-sky-400/20 rounded-lg hover:bg-sky-400/10 hover:border-sky-400/50 font-black uppercase tracking-wider text-lg transition-all hover:scale-105"
              style={{ 
                background: 'linear-gradient(to right, rgb(56, 189, 248), rgb(59, 130, 246), rgb(34, 211, 238))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                filter: 'drop-shadow(0 0 8px rgba(56, 189, 248, 0.35))'
              }}
            >
              Recruiter Dashboard
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="mt-32 grid md:grid-cols-3 gap-8">
          <div className="bg-white border-2 border-sky-200 p-8 rounded-2xl hover:border-sky-400/50 transition-all shadow-lg">
            <div className="w-12 h-12 bg-sky-100 border-2 border-sky-300 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-sky-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2 drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">AI Resume Screening</h3>
            <p className="text-gray-700">
              Automatically analyze resumes and match candidates to jobs using advanced AI algorithms.
            </p>
          </div>

          <div className="bg-white border-2 border-sky-200 p-8 rounded-2xl hover:border-sky-400/50 transition-all shadow-lg">
            <div className="w-12 h-12 bg-sky-100 border-2 border-sky-300 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-sky-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <h3 className="text-xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2 drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">Coding Assessments</h3>
            <p className="text-gray-700">
              Test technical skills with automated coding challenges in multiple programming languages.
            </p>
          </div>

          <div className="bg-white border-2 border-sky-200 p-8 rounded-2xl hover:border-sky-400/50 transition-all shadow-lg">
            <div className="w-12 h-12 bg-sky-100 border-2 border-sky-300 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-sky-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2 drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">AI Interviews</h3>
            <p className="text-gray-700">
              Conduct automated video interviews with real-time behavioral analysis and feedback.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
