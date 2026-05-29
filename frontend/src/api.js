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
export const publishAllDrafts = () => api.post('/blog/publish-all-drafts');
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

// Admin CRM
export const getAdminStats = () => api.get('/admin/stats');
export const getAdminUsers = (search = '', limit = 50, offset = 0) => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  params.append('limit', limit);
  params.append('offset', offset);
  return api.get(`/admin/users?${params.toString()}`);
};
export const getAdminUserDetail = (userId) => api.get(`/admin/users/${userId}`);
export const getAdminEnvironments = (search = '', category = '', status = '', limit = 50, offset = 0) => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (category) params.append('category', category);
  if (status) params.append('status', status);
  params.append('limit', limit);
  params.append('offset', offset);
  return api.get(`/admin/environments?${params.toString()}`);
};
export const getAdminPapers = (search = '', status = '', limit = 50, offset = 0) => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (status) params.append('status', status);
  params.append('limit', limit);
  params.append('offset', offset);
  return api.get(`/admin/papers?${params.toString()}`);
};

// Admin credit management
export const adminAddCredits = (userId, amount, reason = '') => api.post(`/admin/users/${userId}/add-credits`, { amount, reason });
export const adminSetPlan = (userId, plan) => api.post(`/admin/users/${userId}/set-plan`, { plan });

// Marketing / GTM
export const getMarketingTweets = (status = null, contentType = null, limit = 50, offset = 0) => {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (contentType) params.append('content_type', contentType);
  params.append('limit', limit);
  params.append('offset', offset);
  return api.get(`/marketing/tweets?${params.toString()}`);
};
export const generateMarketingTweet = (contentType, customTopic = null) =>
  api.post('/marketing/tweets/generate', { content_type: contentType, custom_topic: customTopic });
export const editMarketingTweet = (id, content) => api.put(`/marketing/tweets/${id}`, { content });
export const postMarketingTweet = (id) => api.post(`/marketing/tweets/${id}/post`);
export const deleteMarketingTweet = (id) => api.delete(`/marketing/tweets/${id}`);
export const getMarketingEngagementLog = (actionType = null, limit = 50) => {
  const params = new URLSearchParams();
  if (actionType) params.append('action_type', actionType);
  params.append('limit', limit);
  return api.get(`/marketing/engagement/log?${params.toString()}`);
};
export const marketingSearchAndLike = (maxLikes = 10) =>
  api.post(`/marketing/engagement/search-and-like?max_likes=${maxLikes}`);
export const getMarketingEngagementStats = (days = 7) =>
  api.get(`/marketing/engagement/stats?days=${days}`);
export const getMarketingCalendar = (days = 7) => api.get(`/marketing/calendar?days=${days}`);
export const getMarketingStats = () => api.get('/marketing/stats');

// Prospect pipeline
export const getProspects = (stage = null, minScore = 0, limit = 50) => {
  const params = new URLSearchParams();
  if (stage) params.append('stage', stage);
  if (minScore > 0) params.append('min_score', minScore);
  params.append('limit', limit);
  return api.get(`/marketing/prospects?${params.toString()}`);
};
export const getProspectFunnel = () => api.get('/marketing/prospects/funnel');
export const discoverProspects = (maxResults = 20) =>
  api.post(`/marketing/prospects/discover?max_results=${maxResults}`);
export const updateProspectStage = (id, stage) =>
  api.put(`/marketing/prospects/${id}/stage`, { stage });

// Reply management
export const approveReply = (logId) => api.post(`/marketing/engagement/reply/${logId}/approve`);
export const rejectReply = (logId) => api.post(`/marketing/engagement/reply/${logId}/reject`);

// Visual Content
export const generateVisual = (template, data) =>
  api.post('/marketing/visual/generate', { template, data });
export const generateVisualTweet = (template, data) =>
  api.post('/marketing/visual/generate-tweet', { template, data });
export const aiDesignVisual = (concept, visual_type, generate_tweet = false) =>
  api.post('/marketing/visual/ai-design', { concept, visual_type, generate_tweet });
export const screenshotPage = (path, selector) =>
  api.post(`/marketing/visual/screenshot?path=${encodeURIComponent(path)}${selector ? '&selector=' + encodeURIComponent(selector) : ''}`);
export const listVisuals = () => api.get('/marketing/visuals');
export const getVisualUrl = (filename) => `/api/marketing/visuals/${filename}`;

// GTM Strategy Engine
export const getActiveStrategy = () => api.get('/marketing/strategy');
export const createStrategy = () => api.post('/marketing/strategy/create');
export const reviewStrategy = () => api.post('/marketing/strategy/review');
export const getKPIDashboard = () => api.get('/marketing/strategy/kpis');
export const getDecisionLog = (type = null, limit = 30) => {
  const params = new URLSearchParams();
  if (type) params.append('decision_type', type);
  params.append('limit', limit);
  return api.get(`/marketing/strategy/decisions?${params.toString()}`);
};
export const getStrategyHistory = (limit = 10) => api.get(`/marketing/strategy/history?limit=${limit}`);

// GTM Evaluation & Reports
export const runGTMEvaluation = (days = 7) => api.post(`/marketing/evaluate?days=${days}`);
export const getGTMReports = (limit = 10) => api.get(`/marketing/reports?limit=${limit}`);

// Agents
export const getAgents = () => api.get('/agents');
export const getAgent = (id) => api.get(`/agents/${id}`);
export const updateAgentParam = (id, key, value) => api.put(`/agents/${id}/param`, { key, value });
export const updateAgentStatus = (id, status) => api.put(`/agents/${id}/status`, { status });

export default api;
