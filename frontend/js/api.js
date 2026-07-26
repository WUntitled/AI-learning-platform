/**
 * API 客户端 — 与后端通信的统一接口
 */
const API_BASE = '/api/v1';

const api = {
  async request(method, path, data = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (data) opts.body = JSON.stringify(data);
    try {
      const resp = await fetch(`${API_BASE}${path}`, opts);
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
      return await resp.json();
    } catch (e) {
      if (e.message.includes('Failed to fetch') || e.message.includes('NetworkError')) {
        throw new Error('无法连接到服务器，请确认后端已启动');
      }
      throw e;
    }
  },

  // === 系统 ===
  systemStatus: () => api.request('GET', '/system/status'),

  // === 学情画像 ===
  diagnoseProfile: (data) => api.request('POST', '/profile/diagnose', data),
  getProfile: (id) => api.request('GET', `/profile/${id}`),
  listProfiles: () => api.request('GET', '/profile/'),
  deleteProfile: (id) => api.request('DELETE', `/profile/${id}`),

  // === 课程 ===
  getCourseAgents: () => api.request('GET', '/course/agents'),
  generateCourse: (profileId) => api.request('POST', '/course/generate', { profile_id: profileId }),
  getCourse: (id) => api.request('GET', `/course/${id}`),
  getCoursesByProfile: (profileId) => api.request('GET', `/course/by-profile/${profileId}`),

  // === 学习助手 ===
  getLearningAgents: () => api.request('GET', '/learning/agents'),
  chat: (profileId, message, sessionId = null) =>
    api.request('POST', '/learning/chat', { profile_id: profileId, message, session_id: sessionId }),
  listSessions: (profileId) => api.request('GET', `/learning/sessions/${profileId}`),
  getSession: (sessionId) => api.request('GET', `/learning/session/${sessionId}`),

  // === 陪练助手 ===
  getScenarioTypes: () => api.request('GET', '/practice/types'),
  generateScenario: (profileId, type) =>
    api.request('POST', '/practice/scenario', { profile_id: profileId, scenario_type: type }),
  submitPractice: (sessionId, answers) =>
    api.request('POST', '/practice/submit', { session_id: sessionId, answers }),
  getPracticeHistory: (profileId) => api.request('GET', `/practice/history/${profileId}`),

  // === 考试助手 ===
  getExamAgents: () => api.request('GET', '/exam/agents'),
  createExam: (profileId) => api.request('POST', '/exam/create', { profile_id: profileId }),
  submitExam: (examId, answers) =>
    api.request('POST', '/exam/submit', { exam_id: examId, answers }),
  getExam: (id) => api.request('GET', `/exam/${id}`),
  getExamHistory: (profileId) => api.request('GET', `/exam/history/${profileId}`),
  getExamReport: (examId) => api.request('GET', `/exam/report/${examId}`),
};

// ================================================================
// 全局状态
// ================================================================
const store = {
  profile: null,       // 当前学情画像
  profileId: null,     // 当前画像ID
  courseId: null,      // 当前课程ID

  async loadProfile() {
    try {
      const profiles = await api.listProfiles();
      if (profiles.length > 0) {
        this.profile = profiles[0];
        this.profileId = profiles[0].id;
        return this.profile;
      }
    } catch (e) { /* ignore */ }
    return null;
  },

  async ensureProfile() {
    if (!this.profile) await this.loadProfile();
    return this.profile;
  }
};
