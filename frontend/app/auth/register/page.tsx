"use client";

import { useState } from 'react';
import { useAuth } from '@/lib/auth';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'candidate',
    company_name: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectParam = searchParams.get('redirect');
  const redirectUrl = redirectParam ? decodeURIComponent(redirectParam) : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (formData.role === 'recruiter' && !formData.company_name.trim()) {
      setError('Company name is required for recruiters');
      return;
    }

    setLoading(true);

    try {
      await register(
        formData.email, 
        formData.password, 
        formData.name, 
        formData.role,
        formData.company_name || undefined
      );
      
      // After successful registration, redirect if URL provided
      if (redirectUrl) {
        router.push(redirectUrl);
      }
      // Otherwise register function will handle default redirect
    } catch (err: any) {
      console.error('Registration error:', err);
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full">
        <div className="bg-white border border-sky-400/30 rounded-2xl shadow-lg p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2">Create Account</h1>
            <p className="text-gray-600">
              {redirectUrl ? 'Sign up to access your assessment' : 'Join HireIQ today'}
            </p>
            {redirectUrl && (
              <div className="mt-3 p-3 bg-blue-50 border border-sky-400/30 rounded-lg">
                <p className="text-sm text-gray-700">
                  Already have an account? <Link href={`/auth/login?redirect=${encodeURIComponent(redirectUrl)}`} className="font-bold text-sky-500 hover:text-sky-600 underline">Sign in here</Link>
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
                Full Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 hover:border-sky-400/50 transition-all"
                placeholder="John Doe"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2">
                Email
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
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
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 hover:border-sky-400/50 transition-all"
                placeholder="••••••••"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2">
                Confirm Password
              </label>
              <input
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 hover:border-sky-400/50 transition-all"
                placeholder="••••••••"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2">
                I am a...
              </label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value, company_name: e.target.value === 'candidate' ? '' : formData.company_name })}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 hover:border-sky-400/50 transition-all"
              >
                <option value="candidate" className="bg-white">Candidate (Job Seeker)</option>
                <option value="recruiter" className="bg-white">Recruiter (Employer)</option>
              </select>
            </div>

            {formData.role === 'recruiter' && (
              <div>
                <label className="block text-sm font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2">
                  Company Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 hover:border-sky-400/50 transition-all"
                  placeholder="Your Company Name"
                  required
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-4 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-lg hover:from-sky-400 hover:to-blue-500 font-black uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? 'Creating account...' : 'Sign Up'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Already have an account?{' '}
              <Link 
                href={redirectUrl ? `/auth/login?redirect=${encodeURIComponent(redirectUrl)}` : '/auth/login'} 
                className="text-sky-500 hover:text-sky-600 font-bold"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
