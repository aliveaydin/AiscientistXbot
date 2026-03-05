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
export const getTweets = (status = null, limit = 50) => {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('limit', limit);
  return api.get(`/tweets/?${params.toString()}`);
};
export const generateTweet = (data) => api.post('/tweets/generate', data);
export const postTweet = (tweetId) => api.post(`/tweets/${tweetId}/post`);
export const regenerateTweet = (tweetId, aiModel = null) => {
  const params = aiModel ? `?ai_model=${aiModel}` : '';
  return api.post(`/tweets/${tweetId}/regenerate${params}`);
};
export const updateTweet = (tweetId, data) => api.put(`/tweets/${tweetId}`, data);
export const deleteTweet = (tweetId) => api.delete(`/tweets/${tweetId}`);

// Articles
export const getArticles = () => api.get('/articles/');
export const getArticle = (id) => api.get(`/articles/${id}`);
export const uploadArticle = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/articles/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
export const scanArticles = () => api.post('/articles/scan');
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
