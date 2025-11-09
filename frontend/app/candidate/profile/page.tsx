"use client";

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import apiClient from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function CandidateProfile() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [profile, setProfile] = useState<any>({
    email: '',
    phone: '',
    location: '',
    linkedin_url: '',
    portfolio_url: '',
    skills: '',
    experience_years: 0,
    education: '',
    bio: '',
    resume_url: '',
    description: '',
  });
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }

    if (user) {
      fetchProfile();
    }
  }, [user, authLoading]);

  const fetchProfile = async () => {
    try {
      const response = await apiClient.profile.get();
      const data = response.data || {};
      // Ensure all fields are never null - convert to empty strings or 0
      setProfile({
        email: data.email ?? '',
        phone: data.phone ?? '',
        location: data.location ?? '',
        linkedin_url: data.linkedin_url ?? '',
        portfolio_url: data.portfolio_url ?? '',
        skills: data.skills ?? '',
        experience_years: data.experience_years ?? 0,
        education: data.education ?? '',
        bio: data.bio ?? '',
        resume_url: data.resume_url ?? '',
        description: data.description ?? '',
      });
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      console.log('Form submitted with profile data:', profile);
      
      // Send ALL form fields - use the actual values from the form state
      // IMPORTANT: Don't use || '' because that converts undefined to empty string
      // Instead, explicitly check if the field exists in the profile object
      const profileUpdate: any = {};
      
      // Send phone - use actual value if it exists (even if empty string)
      if ('phone' in profile) {
        profileUpdate.phone = typeof profile.phone === 'string' ? profile.phone.trim() : (profile.phone || '');
      }
      
      // Send location
      if ('location' in profile) {
        profileUpdate.location = typeof profile.location === 'string' ? profile.location.trim() : (profile.location || '');
      }
      
      // Send linkedin_url
      if ('linkedin_url' in profile) {
        profileUpdate.linkedin_url = typeof profile.linkedin_url === 'string' ? profile.linkedin_url.trim() : (profile.linkedin_url || '');
      }
      
      // Send portfolio_url
      if ('portfolio_url' in profile) {
        profileUpdate.portfolio_url = typeof profile.portfolio_url === 'string' ? profile.portfolio_url.trim() : (profile.portfolio_url || '');
      }
      
      // Send skills
      if ('skills' in profile) {
        profileUpdate.skills = typeof profile.skills === 'string' ? profile.skills.trim() : (profile.skills || '');
      }
      
      // Send experience_years
      if ('experience_years' in profile) {
        profileUpdate.experience_years = profile.experience_years ?? 0;
      }
      
      // Send education
      if ('education' in profile) {
        profileUpdate.education = typeof profile.education === 'string' ? profile.education.trim() : (profile.education || '');
      }
      
      // Send bio
      if ('bio' in profile) {
        profileUpdate.bio = typeof profile.bio === 'string' ? profile.bio.trim() : (profile.bio || '');
      }
      
      // Only include resume_url and description if they exist (preserve if not set)
      if (profile.resume_url) {
        profileUpdate.resume_url = profile.resume_url.trim();
      }
      if (profile.description) {
        profileUpdate.description = profile.description.trim();
      }
      
      console.log('=== PROFILE UPDATE DEBUG ===');
      console.log('Form profile state:', JSON.stringify(profile, null, 2));
      console.log('Sending profile update to API:', JSON.stringify(profileUpdate, null, 2));
      console.log('Phone - raw:', profile.phone, 'type:', typeof profile.phone, '→ sent:', profileUpdate.phone);
      console.log('LinkedIn - raw:', profile.linkedin_url, 'type:', typeof profile.linkedin_url, '→ sent:', profileUpdate.linkedin_url);
      console.log('Portfolio - raw:', profile.portfolio_url, 'type:', typeof profile.portfolio_url, '→ sent:', profileUpdate.portfolio_url);
      
      let updatedProfileData = null;
      
      // Always try to update profile (backend will handle empty fields)
      console.log('Calling profile.update API...');
      try {
        const response = await apiClient.profile.update(profileUpdate);
        updatedProfileData = response.data;
        console.log('Profile update response:', updatedProfileData);
        setSuccess('Profile updated successfully!');
      } catch (updateError: any) {
        console.error('Profile update error:', updateError);
        // If it's a "No updates provided" error, check if we have a resume file
        if (updateError.response?.data?.detail?.includes('No updates provided')) {
          if (!resumeFile) {
            setError('Please fill in at least one field or upload a resume');
            setLoading(false);
            return;
          }
        } else {
          throw updateError; // Re-throw other errors
        }
      }
      
      // If resume file is provided, upload it (this will also update the profile)
      if (resumeFile) {
        console.log('Uploading resume file...');
        try {
          const resumeResponse = await apiClient.profile.uploadResume(resumeFile);
          updatedProfileData = resumeResponse.data;
          console.log('Resume upload response:', updatedProfileData);
          setSuccess('Profile and resume updated successfully!');
        } catch (resumeError: any) {
          console.error('Resume upload error:', resumeError);
          setError(resumeError.response?.data?.detail || 'Failed to upload resume');
          setLoading(false);
          return;
        }
      }
      
      // Update profile state with returned data (ensure no null values)
      if (updatedProfileData) {
        setProfile({
          email: updatedProfileData.email ?? '',
          phone: updatedProfileData.phone ?? '',
          location: updatedProfileData.location ?? '',
          linkedin_url: updatedProfileData.linkedin_url ?? '',
          portfolio_url: updatedProfileData.portfolio_url ?? '',
          skills: updatedProfileData.skills ?? '',
          experience_years: updatedProfileData.experience_years ?? 0,
          education: updatedProfileData.education ?? '',
          bio: updatedProfileData.bio ?? '',
          resume_url: updatedProfileData.resume_url ?? '',
          description: updatedProfileData.description ?? '',
        });
      }
      
      // Clear resume file after successful upload
      if (resumeFile) {
        setResumeFile(null);
      }
    } catch (err: any) {
      console.error('Error updating profile:', err);
      console.error('Error response:', err.response);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to update profile';
      setError(errorMessage);
      console.error('Error message:', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white border border-gray-200 rounded-lg p-8 shadow-lg">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Your Profile</h1>

          <form onSubmit={handleSubmit} className="space-y-6">
            {success && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
                {success}
              </div>
            )}

            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}

            {/* Email display (read-only, from account) */}
            {profile.email && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={profile.email}
                  disabled
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-300 text-gray-500 rounded-lg cursor-not-allowed"
                  readOnly
                />
                <p className="text-xs text-gray-500 mt-1">Email is managed by your account settings</p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Phone (Optional)
              </label>
              <input
                type="tel"
                value={profile.phone || ''}
                onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="+1 (555) 000-0000"
              />
            </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Location
                </label>
              <input
                type="text"
                value={profile.location || ''}
                onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="San Francisco, CA"
              />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                LinkedIn URL (Optional)
              </label>
              <input
                type="url"
                value={profile.linkedin_url || ''}
                onChange={(e) => setProfile({ ...profile, linkedin_url: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="https://linkedin.com/in/yourprofile"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Portfolio URL (Optional)
              </label>
              <input
                type="url"
                value={profile.portfolio_url || ''}
                onChange={(e) => setProfile({ ...profile, portfolio_url: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="https://yourportfolio.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Skills (comma-separated)
              </label>
              <input
                type="text"
                value={profile.skills || ''}
                onChange={(e) => setProfile({ ...profile, skills: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Python, JavaScript, React, Node.js"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Years of Experience
              </label>
              <input
                type="number"
                value={profile.experience_years ?? 0}
                onChange={(e) => setProfile({ ...profile, experience_years: parseInt(e.target.value) || 0 })}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Education
              </label>
              <textarea
                value={profile.education || ''}
                onChange={(e) => setProfile({ ...profile, education: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                placeholder="B.S. Computer Science, Stanford University, 2020"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bio
              </label>
              <textarea
                value={profile.bio || ''}
                onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={4}
                placeholder="Tell us about yourself..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Resume (PDF)
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                className="w-full px-4 py-3 bg-white border border-gray-300 text-gray-900 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500"
              />
              {resumeFile && (
                <p className="text-sm text-gray-500 mt-2">{resumeFile.name}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-500 font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Saving...' : 'Save Profile'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
