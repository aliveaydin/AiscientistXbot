import React, { useState, useEffect } from 'react';
import { 
  Send, RefreshCw, Trash2, Edit3, Sparkles, Heart, 
  Repeat2, MessageCircle, Eye, Bookmark, Check, X,
  ChevronDown, Wand2, BookOpen
} from 'lucide-react';
import { getTweets, generateTweet, postTweet, regenerateTweet, deleteTweet, updateTweet, getArticles, generateBlogFromTweet } from '../api';

function TweetCard({ tweet, onPost, onRegenerate, onDelete, onEdit, onGenerateBlog }) {
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState(tweet.content);
  const [blogLoading, setBlogLoading] = useState(false);

  const handleSave = () => {
    onEdit(tweet.id, editContent);
    setEditing(false);
  };

  return (
    <div className="card hover:border-gray-700 transition-all">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          {editing ? (
            <div className="space-y-2">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="input-field resize-none h-24"
                maxLength={500}
              />
              <div className="flex items-center gap-2">
                <button onClick={handleSave} className="btn-success text-sm py-1.5 px-3">
                  <Check className="w-4 h-4" /> Save
                </button>
                <button onClick={() => setEditing(false)} className="btn-secondary text-sm py-1.5 px-3">
                  <X className="w-4 h-4" /> Cancel
                </button>
                <span className={`text-xs ${editContent.length > 500 ? 'text-red-400' : 'text-gray-500'}`}>
                  {editContent.length}/500
                </span>
              </div>
            </div>
          ) : (
            <p className="text-white leading-relaxed">{tweet.content}</p>
          )}

          <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
            <span className="badge-info">{tweet.ai_model_used}</span>
            <span className={
              tweet.status === 'posted' ? 'badge-success' :
              tweet.status === 'failed' ? 'badge-error' : 'badge-warning'
            }>
              {tweet.status}
            </span>
            <span>{new Date(tweet.created_at).toLocaleString()}</span>
          </div>

          {tweet.status === 'posted' && (
            <div className="flex items-center gap-5 mt-3 text-sm text-gray-400">
              <span className="flex items-center gap-1.5"><Heart className="w-4 h-4 text-rose-400" /> {tweet.likes}</span>
              <span className="flex items-center gap-1.5"><Repeat2 className="w-4 h-4 text-emerald-400" /> {tweet.retweets}</span>
              <span className="flex items-center gap-1.5"><MessageCircle className="w-4 h-4 text-blue-400" /> {tweet.replies_count}</span>
              <span className="flex items-center gap-1.5"><Eye className="w-4 h-4 text-purple-400" /> {tweet.impressions}</span>
              <span className="flex items-center gap-1.5"><Bookmark className="w-4 h-4 text-amber-400" /> {tweet.bookmarks}</span>
            </div>
          )}

          {tweet.article_id && (
            <div className="mt-3">
              <button
                onClick={async () => {
                  setBlogLoading(true);
                  try {
                    await onGenerateBlog(tweet.id);
                  } finally {
                    setBlogLoading(false);
                  }
                }}
                disabled={blogLoading}
                className="btn-secondary text-sm py-1.5 px-3"
              >
                {blogLoading ? (
                  <><RefreshCw className="w-4 h-4 animate-spin" /> Generating Blog...</>
                ) : (
                  <><BookOpen className="w-4 h-4" /> Generate Blog Article</>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Actions */}
        {tweet.status !== 'posted' && (
          <div className="flex flex-col gap-2">
            <button onClick={() => onPost(tweet.id)} className="btn-primary text-sm py-1.5 px-3">
              <Send className="w-4 h-4" /> Post
            </button>
            <button onClick={() => onRegenerate(tweet.id)} className="btn-secondary text-sm py-1.5 px-3">
              <RefreshCw className="w-4 h-4" /> Regen
            </button>
            <button onClick={() => setEditing(true)} className="btn-secondary text-sm py-1.5 px-3">
              <Edit3 className="w-4 h-4" /> Edit
            </button>
            <button onClick={() => onDelete(tweet.id)} className="btn-danger text-sm py-1.5 px-3">
              <Trash2 className="w-4 h-4" /> Del
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function TweetsPage() {
  const [tweets, setTweets] = useState([]);
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [filter, setFilter] = useState('');
  const [selectedArticle, setSelectedArticle] = useState('');
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-20250514');

  useEffect(() => {
    loadData();
  }, [filter]);

  const loadData = async () => {
    try {
      const [tweetsRes, articlesRes] = await Promise.all([
        getTweets(filter || null),
        getArticles(),
      ]);
      setTweets(tweetsRes.data);
      setArticles(articlesRes.data);
    } catch (err) {
      console.error('Failed to load tweets:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const data = {
        ai_model: selectedModel,
      };
      if (selectedArticle) data.article_id = parseInt(selectedArticle);
      await generateTweet(data);
      await loadData();
    } catch (err) {
      alert('Failed to generate tweet: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGenerating(false);
    }
  };

  const handlePost = async (id) => {
    try {
      await postTweet(id);
      await loadData();
    } catch (err) {
      alert('Failed to post: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleRegenerate = async (id) => {
    try {
      await regenerateTweet(id, selectedModel);
      await loadData();
    } catch (err) {
      alert('Failed to regenerate: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this tweet?')) return;
    try {
      await deleteTweet(id);
      await loadData();
    } catch (err) {
      alert('Failed to delete: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleEdit = async (id, content) => {
    try {
      await updateTweet(id, { content, ai_model: selectedModel });
      await loadData();
    } catch (err) {
      alert('Failed to update: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleGenerateBlog = async (tweetId) => {
    try {
      const res = await generateBlogFromTweet(tweetId);
      const created = res.data.created;
      alert(`Blog articles generated!\n${created.map(c => `${c.language.toUpperCase()}: ${c.title} (${c.model})`).join('\n')}`);
    } catch (err) {
      alert('Failed to generate blog: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Tweets</h2>
        <p className="text-gray-400 text-sm mt-1">Generate, edit and post AI-powered tweets</p>
      </div>

      {/* Generate Section */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Wand2 className="w-5 h-5 text-blue-400" />
          Generate New Tweet
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select
            value={selectedArticle}
            onChange={(e) => setSelectedArticle(e.target.value)}
            className="select-field"
          >
            <option value="">Random Article</option>
            {articles.map((a) => (
              <option key={a.id} value={a.id}>{a.title || a.filename}</option>
            ))}
          </select>

          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="select-field"
          >
            <optgroup label="Anthropic (Recommended)">
              <option value="claude-sonnet-4-20250514">Claude Sonnet 4 ⭐</option>
              <option value="claude-3-5-haiku-20241022">Claude 3.5 Haiku (Fast)</option>
              <option value="claude-3-opus-20240229">Claude 3 Opus</option>
            </optgroup>
            <optgroup label="OpenAI">
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-4o-mini">GPT-4o Mini (Cheap)</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
              <option value="gpt-4">GPT-4</option>
            </optgroup>
          </select>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="btn-primary justify-center"
          >
            {generating ? (
              <><RefreshCw className="w-4 h-4 animate-spin" /> Generating...</>
            ) : (
              <><Sparkles className="w-4 h-4" /> Generate Tweet</>
            )}
          </button>
        </div>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-400">Filter:</span>
        {['', 'draft', 'posted', 'failed'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`text-sm px-3 py-1.5 rounded-lg transition-all ${
              filter === f
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'text-gray-400 hover:text-white bg-gray-800/50'
            }`}
          >
            {f || 'All'}
          </button>
        ))}
        <span className="text-sm text-gray-500 ml-auto">{tweets.length} tweets</span>
      </div>

      {/* Tweet List */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : tweets.length > 0 ? (
        <div className="space-y-4">
          {tweets.map((tweet) => (
            <TweetCard
              key={tweet.id}
              tweet={tweet}
              onPost={handlePost}
              onRegenerate={handleRegenerate}
              onDelete={handleDelete}
              onEdit={handleEdit}
              onGenerateBlog={handleGenerateBlog}
            />
          ))}
        </div>
      ) : (
        <div className="card flex items-center justify-center h-48 text-gray-500">
          <div className="text-center">
            <Send className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No tweets yet. Generate your first one above!</p>
          </div>
        </div>
      )}
    </div>
  );
}
