import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// API Client
export const apiClient = {
  // ============================================================
  // HEALTH & STATUS
  // ============================================================
  health: () => api.get('/health'),
  root: () => api.get('/'),

  // ============================================================
  // AUTHENTICATION
  // ============================================================
  auth: {
    register: (data: { email: string; password: string; name: string; role?: string; company_name?: string }) =>
      api.post('/auth/register', data),
    
    login: (email: string, password: string) =>
      api.post('/auth/login', { email, password }),
    
    me: () => api.get('/auth/me'),
    
    updateProfile: (data: { name?: string; phone?: string; company_name?: string }) =>
      api.put('/auth/profile', data),
  },

  // ============================================================
  // JOBS
  // ============================================================
  jobs: {
    getAll: () => api.get('/jobs'),
    
    getById: (id: number) => api.get(`/jobs/${id}`),
    
    create: (data: { title: string; description: string; department: string; company_principles?: string }) =>
      api.post('/jobs', data),
    
    update: (id: number, data: { title?: string; description?: string; department?: string; company_principles?: string }) =>
      api.put(`/jobs/${id}`, data),
    
    delete: (id: number) => api.delete(`/jobs/${id}`),
    
    getCandidates: (id: number) => api.get(`/jobs/${id}/candidates`),
    
    match: (candidateId: number) => api.post('/jobs/match', null, { params: { candidate_id: candidateId } }),
    
    matchBySkills: (skills: string[], topK: number = 5) =>
      api.post('/jobs/match_by_skills', { skills, top_k: topK }),
    
    matchAI: (candidateId: number) => api.post('/jobs/match_ai', null, { params: { candidate_id: candidateId } }),
  },

  // ============================================================
  // CANDIDATES
  // ============================================================
  candidates: {
    getAll: (jobId?: number, stage?: string) => {
      const params: any = {};
      if (jobId) params.job_id = jobId;
      if (stage) params.stage = stage;
      return api.get('/candidates', { params });
    },
    
    ingestResume: (file: File, jobId: number, jobDescription: string) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('job_id', jobId.toString());
      formData.append('job_description', jobDescription);
      return api.post('/candidates/ingest', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    
    getById: (id: number) => api.get(`/candidates/${id}`),
    
    delete: (id: number) => api.delete(`/candidates/${id}`),
    
    sendOA: (candidateId: number, force: boolean = false, threshold?: number) =>
      api.post(`/candidates/${candidateId}/send-oa`, { force, threshold }),
    
    getEmailLogs: (candidateId: number) => api.get(`/candidates/${candidateId}/email-logs`),
    
    matchJobs: (skills: string[], topK: number = 5) =>
      api.post('/candidates/match', { skills, top_k: topK }),
    
    evaluate: (candidateId: number) => api.post(`/candidates/${candidateId}/evaluate`),
  },

  // ============================================================
  // OA (Online Assessment)
  // ============================================================
  oa: {
    // Public endpoint - no auth required
    access: (candidateId: number, token: string, sessionId?: number) =>
      api.post('/oa/access', { candidate_id: candidateId, token, session_id: sessionId }),
    
    // Public endpoint - no auth required
    getSessionPublic: (sessionId: number, token: string) =>
      api.get(`/oa/session/${sessionId}/public?token=${token}`),
    
    // Get all OA sessions for current user
    getMySessions: () => api.get('/oa/my-sessions'),
    
    start: (candidateId: number, questionIds: number[], durationMinutes: number = 60) =>
      api.post('/oa/start', { candidate_id: candidateId, question_ids: questionIds, duration_minutes: durationMinutes }),
    
    getSession: (sessionId: number) => api.get(`/oa/session/${sessionId}`),
    
    getQuestions: (sessionId: number) => api.get(`/oa/session/${sessionId}/questions`),
    
    submitCode: (sessionId: number, questionId: number, sourceCode: string, language: string) =>
      api.post('/oa/submit', { session_id: sessionId, question_id: questionId, source_code: sourceCode, language }),
    
    complete: (sessionId: number, maxCheatingScore?: number) => api.post('/oa/complete', { session_id: sessionId, max_cheating_score: maxCheatingScore }),
    
    getResults: (sessionId: number) => api.get(`/oa/session/${sessionId}/results`),
  },

  // ============================================================
  // OA ADMIN
  // ============================================================
  oaAdmin: {
    getAllQuestions: () => api.get('/oa/admin/questions'),
    
    getQuestion: (id: number) => api.get(`/oa/admin/questions/${id}`),
    
    createQuestion: (data: {
      title: string;
      description: string;
      difficulty: string;
      time_limit_seconds: number;
      sample_input: string;
      sample_output: string;
      hidden_test_cases: string;
    }) => api.post('/oa/admin/questions', data),
    
    updateQuestion: (id: number, data: any) => api.put(`/oa/admin/questions/${id}`, data),
    
    deleteQuestion: (id: number) => api.delete(`/oa/admin/questions/${id}`),
    
    getAllSessions: () => api.get('/oa/admin/sessions'),
    
    getSession: (id: number) => api.get(`/oa/admin/sessions/${id}`),
  },

  // ============================================================
  // INTERVIEWS
  // ============================================================
  interviews: {
    start: (candidateId: number, jobId: number) =>
      api.post('/interviews/start', null, { params: { candidate_id: candidateId, job_id: jobId } }),
    
    next: (sessionId: string, responseText: string) =>
      api.post('/interviews/next', null, { params: { session_id: sessionId, response_text: responseText } }),
    
    end: (sessionId: string) =>
      api.post('/interviews/end', null, { params: { session_id: sessionId } }),
    
    submitEyeMetrics: (sessionId: string, gazeData: any) =>
      api.post('/interviews/metrics/eye', null, { params: { session_id: sessionId, gaze_data: gazeData } }),
  },

  // ============================================================
  // CANDIDATE PROFILE
  // ============================================================
  profile: {
    get: () => api.get('/candidate/profile'),
    
    update: (data: {
      phone?: string;
      location?: string;
      linkedin_url?: string;
      portfolio_url?: string;
      skills?: string;
      experience_years?: number;
      education?: string;
      bio?: string;
      resume_url?: string;
      description?: string;
    }) => api.put('/candidate/profile', data),
    
    uploadResume: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post('/candidate/profile/resume', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
  },

  // ============================================================
  // RECRUITER
  // ============================================================
  recruiter: {
    getCompanyCandidates: () => api.get('/recruiter/candidates'),
    
    getCandidateDetails: (candidateId: number) => api.get(`/recruiter/candidates/${candidateId}`),
  },

  // ============================================================
  // SYSTEM
  // ============================================================
  system: {
    status: () => api.get('/system/status'),
  },
};

export default apiClient;
