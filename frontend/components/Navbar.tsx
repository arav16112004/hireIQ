"use client";

import Link from 'next/link';
import { useAuth } from '@/lib/auth';

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-black/90 backdrop-blur-md border-b-2 border-sky-400/20 shadow-[0_0_30px_rgba(56,189,248,0.15)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-2xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(56,189,248,0.35)] hover:drop-shadow-[0_0_12px_rgba(56,189,248,0.5)] transition-all duration-200 tracking-tight">
              HireIQ
            </Link>
            
            {user && (
              <div className="hidden md:flex space-x-6">
                {user.role === 'candidate' && (
                  <>
                    <Link href="/candidate/dashboard" className="font-bold text-sm uppercase tracking-wider bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(56,189,248,0.35)] hover:drop-shadow-[0_0_12px_rgba(56,189,248,0.5)] transition-all duration-200 hover:scale-105">
                      Dashboard
                    </Link>
                    <Link href="/jobs" className="font-bold text-sm uppercase tracking-wider bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(56,189,248,0.35)] hover:drop-shadow-[0_0_12px_rgba(56,189,248,0.5)] transition-all duration-200 hover:scale-105">
                      Jobs
                    </Link>
                    <Link href="/apply" className="font-bold text-sm uppercase tracking-wider bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(56,189,248,0.35)] hover:drop-shadow-[0_0_12px_rgba(56,189,248,0.5)] transition-all duration-200 hover:scale-105">
                      Apply
                    </Link>
                    <Link href="/candidate/profile" className="font-bold text-sm uppercase tracking-wider bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(56,189,248,0.35)] hover:drop-shadow-[0_0_12px_rgba(56,189,248,0.5)] transition-all duration-200 hover:scale-105">
                      Profile
                    </Link>
                  </>
                )}
                
                {(user.role === 'recruiter' || user.role === 'admin') && (
                  <>
                    <Link href="/recruiter/dashboard" className="font-bold text-sm uppercase tracking-wider bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(56,189,248,0.35)] hover:drop-shadow-[0_0_12px_rgba(56,189,248,0.5)] transition-all duration-200 hover:scale-105">
                      Dashboard
                    </Link>
                    <Link href="/recruiter/candidates" className="font-bold text-sm uppercase tracking-wider bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(56,189,248,0.35)] hover:drop-shadow-[0_0_12px_rgba(56,189,248,0.5)] transition-all duration-200 hover:scale-105">
                      Candidates
                    </Link>
                    <Link href="/recruiter/jobs" className="font-bold text-sm uppercase tracking-wider bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(56,189,248,0.35)] hover:drop-shadow-[0_0_12px_rgba(56,189,248,0.5)] transition-all duration-200 hover:scale-105">
                      Jobs
                    </Link>
                  </>
                )}
                
                {user.role === 'admin' && (
                  <Link href="/admin/oa-questions" className="font-bold text-sm uppercase tracking-wider bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(56,189,248,0.35)] hover:drop-shadow-[0_0_12px_rgba(56,189,248,0.5)] transition-all duration-200 hover:scale-105">
                    OA Questions
                  </Link>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-6">
            {user ? (
              <>
                <div className="text-sm">
                  <div className="font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(56,189,248,0.35)] uppercase tracking-wider text-base">
                    {user.name}
                  </div>
                  <div className="text-sky-300 text-xs uppercase tracking-widest font-bold">
                    {user.role}
                  </div>
                </div>
                <button
                  onClick={logout}
                  className="px-6 py-2.5 font-bold uppercase tracking-wider text-sm transition-all duration-200 border-2 border-sky-400/30 rounded-lg hover:border-sky-400/50 hover:bg-sky-400/10 hover:scale-105"
                  style={{ 
                    background: 'linear-gradient(to right, rgb(56, 189, 248), rgb(59, 130, 246), rgb(34, 211, 238))',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    filter: 'drop-shadow(0 0 8px rgba(56, 189, 248, 0.35))'
                  }}
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link 
                  href="/auth/login"
                  className="px-6 py-2.5 font-bold uppercase tracking-wider text-sm transition-all duration-200 hover:scale-105"
                  style={{ 
                    background: 'linear-gradient(to right, rgb(56, 189, 248), rgb(59, 130, 246), rgb(34, 211, 238))',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    filter: 'drop-shadow(0 0 8px rgba(56, 189, 248, 0.35))'
                  }}
                >
                  Login
                </Link>
                <Link 
                  href="/auth/register"
                  className="px-6 py-2.5 font-bold uppercase tracking-wider text-sm transition-all duration-200 hover:scale-105"
                  style={{ 
                    background: 'linear-gradient(to right, rgb(56, 189, 248), rgb(59, 130, 246), rgb(34, 211, 238))',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    filter: 'drop-shadow(0 0 8px rgba(56, 189, 248, 0.35))'
                  }}
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

