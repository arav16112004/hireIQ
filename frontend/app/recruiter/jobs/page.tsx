"use client";

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth';
import apiClient from '@/lib/api';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function RecruiterJobsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingJob, setEditingJob] = useState<any | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    department: '',
    company_principles: '',
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }

    if (user && user.role !== 'recruiter' && user.role !== 'admin') {
      router.push('/candidate/dashboard');
      return;
    }

    if (user) {
      fetchJobs();
    }
  }, [user, authLoading]);

  const fetchJobs = async () => {
    try {
      const res = await apiClient.jobs.getAll();
      setJobs(res.data.jobs || []);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.title || !formData.description || !formData.department) {
      alert('Please fill in all required fields');
      return;
    }

    setSubmitting(true);
    try {
      await apiClient.jobs.create(formData);
      alert('Job created successfully!');
      setShowCreateModal(false);
      setFormData({ title: '', description: '', department: '', company_principles: '' });
      fetchJobs();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to create job');
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async () => {
    if (!editingJob || !formData.title || !formData.description || !formData.department) {
      alert('Please fill in all required fields');
      return;
    }

    setSubmitting(true);
    try {
      await apiClient.jobs.update(editingJob.ID, formData);
      alert('Job updated successfully!');
      setEditingJob(null);
      setFormData({ title: '', description: '', department: '', company_principles: '' });
      fetchJobs();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to update job');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (jobId: number) => {
    if (!confirm('Are you sure you want to delete this job?')) return;

    try {
      await apiClient.jobs.delete(jobId);
      alert('Job deleted successfully!');
      fetchJobs();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to delete job');
    }
  };

  const openEditModal = (job: any) => {
    setEditingJob(job);
    setFormData({
      title: job.TITLE || '',
      description: job.DESCRIPTION || '',
      department: job.DEPARTMENT || '',
      company_principles: job.COMPANY_PRINCIPLES || job.company_principles || '',
    });
  };

  const closeModal = () => {
    setShowCreateModal(false);
    setEditingJob(null);
    setFormData({ title: '', description: '', department: '', company_principles: '' });
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
        {/* Header */}
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2 drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">
              Manage Jobs
            </h1>
            <p className="text-gray-700">
              Create, edit, and manage job postings
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-lg hover:from-sky-400 hover:to-blue-500 font-black uppercase tracking-wider shadow-[0_0_20px_rgba(56,189,248,0.4)] hover:shadow-[0_0_30px_rgba(56,189,248,0.6)] hover:scale-105 transition-all ring-2 ring-sky-400/30"
          >
            + Create Job
          </button>
        </div>

        {/* Jobs List */}
        <div className="bg-white/80 backdrop-blur-md border-2 border-gray-200 rounded-xl shadow-[0_0_30px_rgba(56,189,248,0.15)] overflow-hidden">
          <div className="px-6 py-4 border-b-2 border-gray-200 bg-sky-900/10">
            <h2 className="text-xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">
              Jobs ({jobs.length})
            </h2>
          </div>
          <div className="divide-y divide-sky-400/20">
            {jobs.length > 0 ? (
              jobs.map((job) => (
                <div key={job.ID} className="px-6 py-4 hover:bg-sky-900/10 transition-all">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-bold text-sky-300 uppercase tracking-wider text-lg mb-2">
                        {job.TITLE}
                      </h3>
                      <p className="text-gray-500 text-sm mb-2">
                        <span className="text-sky-400 font-bold">Department:</span> {job.DEPARTMENT}
                      </p>
                      <p className="text-gray-700 text-sm line-clamp-2">
                        {job.DESCRIPTION}
                      </p>
                      {job.CREATED_AT && (
                        <p className="text-slate-500 text-xs mt-2">
                          Created: {new Date(job.CREATED_AT).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2 ml-4">
                      <Link
                        href={`/recruiter/jobs/${job.ID}`}
                        className="px-4 py-2 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-lg hover:from-sky-400 hover:to-blue-500 text-sm font-bold uppercase tracking-wider shadow-[0_0_20px_rgba(56,189,248,0.4)] hover:shadow-[0_0_30px_rgba(56,189,248,0.6)] hover:scale-105 transition-all"
                      >
                        View Details
                      </Link>
                      <button
                        onClick={() => openEditModal(job)}
                        className="px-4 py-2 bg-gray-100 border-2 border-gray-200 text-sky-400 rounded-lg hover:border-sky-400/50 hover:bg-sky-400/10 text-sm font-bold uppercase tracking-wider transition-all"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(job.ID)}
                        className="px-4 py-2 bg-red-900/30 border-2 border-red-700 text-red-300 rounded-lg hover:border-red-500 hover:bg-red-900/50 text-sm font-bold uppercase tracking-wider transition-all"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-6 py-12 text-center text-gray-500">
                No jobs found. Create your first job!
              </div>
            )}
          </div>
        </div>

        {/* Create/Edit Modal */}
        {(showCreateModal || editingJob) && (
          <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-white/95 backdrop-blur-md border-2 border-gray-200 rounded-xl shadow-[0_0_30px_rgba(56,189,248,0.15)] p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-black bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-6 drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">
                {editingJob ? 'Edit Job' : 'Create Job'}
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2 drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">
                    Title
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full px-4 py-3 bg-gray-100 border-2 border-gray-200 text-gray-900 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400"
                    placeholder="Job Title"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2 drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">
                    Department
                  </label>
                  <input
                    type="text"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    className="w-full px-4 py-3 bg-gray-100 border-2 border-gray-200 text-gray-900 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400"
                    placeholder="Department"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2 drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={6}
                    className="w-full px-4 py-3 bg-gray-100 border-2 border-gray-200 text-gray-900 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 resize-none"
                    placeholder="Job Description"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-bold bg-gradient-to-r from-sky-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent uppercase tracking-wider mb-2 drop-shadow-[0_0_8px_rgba(56,189,248,0.35)]">
                    Company Principles
                    <span className="text-xs font-normal text-gray-500 ml-2">(Optional - For AI Avatar Video Interviews)</span>
                  </label>
                  <textarea
                    value={formData.company_principles}
                    onChange={(e) => setFormData({ ...formData, company_principles: e.target.value })}
                    rows={4}
                    className="w-full px-4 py-3 bg-gray-100 border-2 border-gray-200 text-gray-900 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400 resize-none"
                    placeholder="Enter your company principles, values, or culture that the AI should emphasize during video interviews (e.g., 'Team collaboration', 'Innovation', 'Customer-first approach', etc.)"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    These principles will be used by the AI avatar to ask relevant questions and assess candidate fit during video interviews.
                  </p>
                </div>
              </div>
              
              <div className="flex gap-4 mt-6">
                <button
                  onClick={editingJob ? handleUpdate : handleCreate}
                  disabled={submitting}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-lg hover:from-sky-400 hover:to-blue-500 font-black uppercase tracking-wider shadow-[0_0_20px_rgba(56,189,248,0.4)] hover:shadow-[0_0_30px_rgba(56,189,248,0.6)] hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? 'Saving...' : editingJob ? 'Update' : 'Create'}
                </button>
                <button
                  onClick={closeModal}
                  className="flex-1 px-6 py-3 bg-gray-100 border-2 border-gray-200 text-sky-400 rounded-lg hover:border-sky-400/50 hover:bg-sky-400/10 font-bold uppercase tracking-wider transition-all"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

