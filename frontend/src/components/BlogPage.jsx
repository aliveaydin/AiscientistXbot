import React, { useState, useEffect } from 'react';
import { 
  BookOpen, Globe, ChevronDown, ChevronUp, ExternalLink, 
  Trash2, CheckCircle, Clock, Send, Copy, Filter, Sparkles, RefreshCw
} from 'lucide-react';
import { getBlogPosts, updateBlogStatus, deleteBlogPost, getArticles, generateBlogFromArticle } from '../api';

export default function BlogPage() {
  const [posts, setPosts] = useState([]);
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [langFilter, setLangFilter] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  useEffect(() => {
    loadData();
  }, [langFilter]);

  const loadData = async () => {
    try {
      const [postsRes, articlesRes] = await Promise.all([
        getBlogPosts(langFilter),
        getArticles(),
      ]);
      setPosts(postsRes.data);
      setArticles(articlesRes.data);
    } catch (err) {
      console.error('Failed to load blog data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadPosts = async () => {
    try {
      const res = await getBlogPosts(langFilter);
      setPosts(res.data);
    } catch (err) {
      console.error('Failed to load blog posts:', err);
    }
  };

  const handleGenerate = async () => {
    if (!selectedArticle) {
      alert('Please select a source paper first.');
      return;
    }
    setGenerating(true);
    try {
      const res = await generateBlogFromArticle(parseInt(selectedArticle));
      const created = res.data.created;
      alert(`Blog articles generated!\n${created.map(c => `${c.language.toUpperCase()}: ${c.title}`).join('\n')}`);
      await loadPosts();
    } catch (err) {
      alert('Failed to generate blog: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGenerating(false);
    }
  };

  const handleStatusChange = async (id, newStatus) => {
    try {
      await updateBlogStatus(id, newStatus);
      await loadPosts();
    } catch (err) {
      alert('Failed to update status: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this blog post?')) return;
    try {
      await deleteBlogPost(id);
      await loadPosts();
    } catch (err) {
      alert('Delete failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleCopy = async (post) => {
    const text = `# ${post.title}\n\n${post.content}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(post.id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopiedId(post.id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const enPosts = posts.filter(p => p.language === 'en');
  const trPosts = posts.filter(p => p.language === 'tr');
  const displayPosts = langFilter ? posts : posts;

  const grouped = {};
  for (const p of posts) {
    const key = p.tweet_id || `standalone-${p.id}`;
    if (!grouped[key]) grouped[key] = {};
    grouped[key][p.language] = p;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Blog Articles</h2>
        <p className="text-gray-400 text-sm mt-1">
          AI-generated articles for each tweet. Copy and publish on X Articles manually.
        </p>
      </div>

      {/* Generate Section */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-400" />
          Generate Blog Article
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select
            value={selectedArticle}
            onChange={(e) => setSelectedArticle(e.target.value)}
            className="select-field md:col-span-2"
          >
            <option value="">Select a source paper...</option>
            {articles.map((a) => (
              <option key={a.id} value={a.id}>{a.title || a.filename}</option>
            ))}
          </select>

          <button
            onClick={handleGenerate}
            disabled={generating || !selectedArticle}
            className="btn-primary justify-center"
          >
            {generating ? (
              <><RefreshCw className="w-4 h-4 animate-spin" /> Generating...</>
            ) : (
              <><Sparkles className="w-4 h-4" /> Generate EN + TR</>
            )}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Generates both English and Turkish blog articles using Kimi K2.5
        </p>
      </div>

      {/* Stats + Filter */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 bg-gray-800/50 rounded-lg p-1">
          <button
            onClick={() => setLangFilter(null)}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
              !langFilter ? 'bg-blue-500/20 text-blue-400' : 'text-gray-400 hover:text-white'
            }`}
          >
            All ({posts.length})
          </button>
          <button
            onClick={() => setLangFilter('en')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
              langFilter === 'en' ? 'bg-blue-500/20 text-blue-400' : 'text-gray-400 hover:text-white'
            }`}
          >
            English ({enPosts.length})
          </button>
          <button
            onClick={() => setLangFilter('tr')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
              langFilter === 'tr' ? 'bg-blue-500/20 text-blue-400' : 'text-gray-400 hover:text-white'
            }`}
          >
            Turkish ({trPosts.length})
          </button>
        </div>
        <span className="text-sm text-gray-500 ml-auto">
          {Object.keys(grouped).length} article pairs
        </span>
      </div>

      {/* Info Box */}
      <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
        <p className="text-sm text-purple-300">
          <strong>How it works:</strong> For each tweet the bot generates, it also writes an in-depth blog article (EN + TR). 
          Click "Copy" to copy the markdown content, then paste it into X Articles to publish.
        </p>
      </div>

      {/* Posts */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : posts.length > 0 ? (
        <div className="space-y-4">
          {posts.map((post) => (
            <div key={post.id} className="card hover:border-gray-700 transition-all">
              <div className="flex items-start gap-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  post.language === 'en' 
                    ? 'bg-blue-500/10 text-blue-400' 
                    : 'bg-red-500/10 text-red-400'
                }`}>
                  <Globe className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="text-white font-semibold truncate">{post.title}</h4>
                    <span className={`text-xs font-mono px-1.5 py-0.5 rounded ${
                      post.language === 'en'
                        ? 'bg-blue-500/20 text-blue-400'
                        : 'bg-red-500/20 text-red-400'
                    }`}>
                      {post.language.toUpperCase()}
                    </span>
                    {post.status === 'published' ? (
                      <span className="badge-success flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" /> Published
                      </span>
                    ) : (
                      <span className="badge-warning flex items-center gap-1">
                        <Clock className="w-3 h-3" /> Draft
                      </span>
                    )}
                  </div>
                  {post.tweet_content && (
                    <p className="text-xs text-gray-500 mt-1 truncate">
                      <Send className="w-3 h-3 inline mr-1" />
                      Tweet: {post.tweet_content.substring(0, 100)}...
                    </p>
                  )}
                  {post.article_title && (
                    <p className="text-xs text-gray-500 mt-0.5 truncate">
                      <BookOpen className="w-3 h-3 inline mr-1" />
                      Source: {post.article_title}
                    </p>
                  )}
                  <p className="text-xs text-gray-600 mt-1">
                    {post.ai_model_used} · {new Date(post.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleCopy(post)}
                    className={`btn-secondary text-sm py-1.5 px-3 ${copiedId === post.id ? 'text-green-400' : ''}`}
                    title="Copy markdown to clipboard"
                  >
                    <Copy className="w-4 h-4" />
                    {copiedId === post.id ? 'Copied!' : 'Copy'}
                  </button>
                  {post.status === 'draft' ? (
                    <button
                      onClick={() => handleStatusChange(post.id, 'published')}
                      className="btn-primary text-sm py-1.5 px-3"
                      title="Mark as published"
                    >
                      <CheckCircle className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      onClick={() => handleStatusChange(post.id, 'draft')}
                      className="btn-secondary text-sm py-1.5 px-3"
                      title="Mark as draft"
                    >
                      <Clock className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => setExpandedId(expandedId === post.id ? null : post.id)}
                    className="btn-secondary text-sm py-1.5 px-3"
                  >
                    {expandedId === post.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                  <button
                    onClick={() => handleDelete(post.id)}
                    className="btn-danger text-sm py-1.5 px-3"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Expanded content */}
              {expandedId === post.id && (
                <div className="mt-4 pt-4 border-t border-gray-800">
                  <div 
                    className="prose prose-invert prose-sm max-w-none text-gray-300"
                    style={{ lineHeight: '1.7' }}
                  >
                    {post.content.split('\n').map((line, i) => {
                      if (line.startsWith('## ')) {
                        return <h3 key={i} className="text-lg font-bold text-white mt-4 mb-2">{line.replace('## ', '')}</h3>;
                      }
                      if (line.startsWith('### ')) {
                        return <h4 key={i} className="text-base font-semibold text-gray-200 mt-3 mb-1">{line.replace('### ', '')}</h4>;
                      }
                      if (line.startsWith('- ')) {
                        return <li key={i} className="ml-4 text-gray-300">{line.replace('- ', '')}</li>;
                      }
                      if (line.trim() === '') {
                        return <br key={i} />;
                      }
                      return <p key={i} className="text-gray-300 mb-2">{line}</p>;
                    })}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="card flex items-center justify-center h-48 text-gray-500">
          <div className="text-center">
            <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No blog articles yet. They will be generated automatically with each tweet.</p>
          </div>
        </div>
      )}
    </div>
  );
}
