import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Dashboard
export const getDashboardStats = () => api.get('/dashboard/stats');
export const getActivityLogs = (limit = 50) => api.get(`/dashboard/activity?limit=${limit}`);
export const getChartData = (days = 7) => api.get(`/dashboard/chart-data?days=${days}`);

// Tweets
export const getTweets = (status = null, limit = 20, offset = 0) => {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('limit', limit);
  params.append('offset', offset);
  return api.get(`/tweets/?${params.toString()}`);
};
export const getTweetCount = (status = null) => {
  const params = status ? `?status=${status}` : '';
  return api.get(`/tweets/count${params}`);
};
export const generateTweet = (data) => api.post('/tweets/generate', data);
export const postTweet = (tweetId) => api.post(`/tweets/${tweetId}/post`);
export const regenerateTweet = (tweetId, aiModel = null) => {
  const params = aiModel ? `?ai_model=${aiModel}` : '';
  return api.post(`/tweets/${tweetId}/regenerate${params}`);
};
export const updateTweet = (tweetId, data) => api.put(`/tweets/${tweetId}`, data);
export const deleteTweet = (tweetId) => api.delete(`/tweets/${tweetId}`);
export const autoReplyTweet = (tweetId) => api.post(`/tweets/${tweetId}/auto-reply`);

// Articles
export const getArticles = (limit = 20, offset = 0) => {
  const params = new URLSearchParams();
  params.append('limit', limit);
  params.append('offset', offset);
  return api.get(`/articles/?${params.toString()}`);
};
export const getAllArticles = () => api.get('/articles/?limit=500&offset=0');
export const getArticleCount = () => api.get('/articles/count');
export const getArticle = (id) => api.get(`/articles/${id}`);
export const uploadArticle = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/articles/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
export const scanArticles = () => api.post('/articles/scan');
export const fetchArxiv = () => api.post('/articles/fetch-arxiv');
export const summarizeArticle = (id, aiModel = null) => {
  const params = aiModel ? `?ai_model=${aiModel}` : '';
  return api.post(`/articles/${id}/summarize${params}`);
};
export const deleteArticle = (id) => api.delete(`/articles/${id}`);

// Blog
export const getBlogPosts = (language = null, limit = 50) => {
  const params = new URLSearchParams();
  if (language) params.append('language', language);
  params.append('limit', limit);
  return api.get(`/blog/?${params.toString()}`);
};
export const getBlogPost = (id) => api.get(`/blog/${id}`);
export const updateBlogStatus = (id, status) => api.put(`/blog/${id}/status`, { status });
export const deleteBlogPost = (id) => api.delete(`/blog/${id}`);
export const generateBlogFromTweet = (tweetDbId) => api.post(`/blog/generate-from-tweet/${tweetDbId}`);
export const generateBlogFromArticle = (articleId) => api.post(`/blog/generate-from-article/${articleId}`);
export const generateBlogFromTopic = (topic) => api.post('/blog/generate-from-topic', { topic });

// Research Lab
export const getLabAgents = () => api.get('/lab/agents');
export const getLabPhases = () => api.get('/lab/phases');
export const getLabProjects = () => api.get('/lab/projects');
export const createLabProject = (data) => api.post('/lab/projects', data);
export const getLabProject = (id) => api.get(`/lab/projects/${id}`);
export const runLabPhase = (id) => api.post(`/lab/projects/${id}/run-phase`);
export const runLabAllPhases = (id) => api.post(`/lab/projects/${id}/run-all`);
export const getLabChatboard = (id) => api.get(`/lab/projects/${id}/chatboard`);
export const getLabAgentWork = (id, agent) => api.get(`/lab/projects/${id}/agent/${agent}/work`);
export const getLabPaper = (id) => api.get(`/lab/projects/${id}/paper`);
export const getLabReferences = (id) => api.get(`/lab/projects/${id}/references`);
export const uploadLabDoc = (projectId, file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post(`/lab/projects/${projectId}/upload-doc`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
export const deleteLabProject = (id) => api.delete(`/lab/projects/${id}`);
export const publishLabPaper = (id) => api.post(`/lab/projects/${id}/paper/publish`);
export const unpublishLabPaper = (id) => api.post(`/lab/projects/${id}/paper/unpublish`);

// RL Environments
export const getRLEnvironments = () => api.get('/rl-envs/');
export const generateRLEnvironment = (data) => api.post('/rl-envs/generate', data);
export const createRLEnvironment = (data) => api.post('/rl-envs/create', data);
export const updateRLEnvironment = (id, data) => api.put(`/rl-envs/${id}`, data);
export const publishRLEnvironment = (id) => api.post(`/rl-envs/${id}/publish`);
export const unpublishRLEnvironment = (id) => api.post(`/rl-envs/${id}/unpublish`);
export const deleteRLEnvironment = (id) => api.delete(`/rl-envs/${id}`);

// Settings
export const getSettings = () => api.get('/settings/');
export const updateSettings = (data) => api.put('/settings/', data);
export const startScheduler = () => api.post('/settings/scheduler/start');
export const stopScheduler = () => api.post('/settings/scheduler/stop');
export const getSchedulerStatus = () => api.get('/settings/scheduler/status');
export const testTwitter = () => api.post('/settings/test/twitter');
export const testAI = (model) => api.post(`/settings/test/ai/${model}`);
export const getAvailableModels = () => api.get('/settings/models');
export const getReplies = (limit = 50) => api.get(`/settings/replies?limit=${limit}`);

export default api;
