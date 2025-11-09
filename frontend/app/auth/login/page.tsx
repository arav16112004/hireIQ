"use client";

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectParam = searchParams.get('redirect');
  const redirectUrl = redirectParam ? decodeURIComponent(redirectParam) : null;
  
  console.log('Login page - redirect param:', redirectParam);
  console.log('Login page - decoded redirect URL:', redirectUrl);

  // If already logged in, redirect appropriately
  useEffect(() => {
    if (user && !loading) {
      if (redirectUrl) {
        router.push(redirectUrl);
      }
      // Don't auto-redirect if no redirectUrl - let them see the login page
    }
  }, [user, redirectUrl, loading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      console.log('Login form submitted, redirect URL:', redirectUrl);
      
      // Pass redirect URL to login function and get user data
      const userData = await login(email, password, redirectUrl || undefined);
      
      // After successful login, redirect immediately
      console.log('Login successful, redirecting...');
      if (redirectUrl) {
        console.log('Redirecting to OA:', redirectUrl);
        router.push(redirectUrl);
      } else {
        // Default redirect based on role
        if (userData.role === 'recruiter' || userData.role === 'admin') {
          router.push('/recruiter/dashboard');
        } else {
          router.push('/candidate/dashboard');
        }
      }
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-white border border-sky-400/30 rounded-2xl shadow-lg p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2">
              {redirectUrl ? 'Sign In to Continue' : 'Welcome Back'}
            </h1>
            <p className="text-gray-600">
              {redirectUrl 
                ? 'Please sign in to access your assessment' 
                : 'Sign in to your HireIQ account'}
            </p>
            {redirectUrl && (
              <div className="mt-3 p-3 bg-blue-50 border border-sky-400/30 rounded-lg">
                <p className="text-sm text-gray-700">
                  Don't have an account? <Link href={`/auth/register?redirect=${encodeURIComponent(redirectUrl)}`} className="font-bold text-sky-500 hover:text-sky-600 underline">Sign up here</Link>
                </p>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-4 bg-red-50 border border-red-300 rounded-lg text-red-700 text-sm font-medium">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 hover:border-sky-400/50 transition-all"
                placeholder="you@example.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 hover:border-sky-400/50 transition-all"
                placeholder="••••••••"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-4 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-lg hover:from-sky-400 hover:to-blue-500 font-black uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Don't have an account?{' '}
              <Link href="/auth/register" className="text-sky-500 hover:text-sky-600 font-bold">
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
