import React, { useState, useEffect } from 'react';
import {
  Send, Plus, RefreshCw, Trash2, Edit3, Check, X,
  Zap, BookOpen, GraduationCap, BarChart3, Image as ImageIcon, Eye
} from 'lucide-react';
import {
  getMarketingTweets, generateMarketingTweet, editMarketingTweet,
  postMarketingTweet, deleteMarketingTweet, generateVisualTweet, getVisualUrl,
  aiDesignVisual,
} from '../api';

const CONTENT_TYPES = [
  { id: 'product', label: 'Product', icon: Zap, color: 'blue' },
  { id: 'industry', label: 'Industry', icon: BarChart3, color: 'green' },
  { id: 'educational', label: 'Educational', icon: GraduationCap, color: 'yellow' },
  { id: 'showcase', label: 'Showcase', icon: BookOpen, color: 'purple' },
];

const STATUS_COLORS = {
  draft: 'text-gray-400 bg-gray-800',
  approved: 'text-blue-400 bg-blue-900/30',
  posted: 'text-green-400 bg-green-900/30',
  failed: 'text-red-400 bg-red-900/30',
};

const VISUAL_TEMPLATES = [
  { id: 'feature_card', label: 'Feature Card', fields: ['BADGE', 'TITLE', 'DESCRIPTION'] },
  { id: 'stats_card', label: 'Stats Card', fields: ['ENVS', 'AGENTS', 'PAPERS'] },
  { id: 'code_snippet', label: 'Code Snippet', fields: ['FILENAME', 'CODE'] },
  { id: 'training_result', label: 'Training Result', fields: ['ENV_NAME', 'DOMAIN', 'ALGORITHM', 'STEPS', 'MEAN_REWARD', 'SUCCESS_RATE', 'EPISODES', 'TRAIN_TIME'] },
];

const AI_VISUAL_TYPES = [
  { id: 'flow_diagram', label: 'Flow Diagram', desc: 'Step-by-step process with arrows' },
  { id: 'comparison', label: 'Comparison', desc: 'Side-by-side feature or approach comparison' },
  { id: 'training_curve', label: 'Training Curve', desc: 'Reward/loss chart with metrics' },
  { id: 'architecture', label: 'Architecture', desc: 'System/component diagram' },
  { id: 'step_guide', label: 'Step Guide', desc: 'Numbered tutorial steps' },
  { id: 'infographic', label: 'Infographic', desc: 'Data-driven visual with stats' },
  { id: 'tip_card', label: 'Tip Card', desc: 'Educational concept visual' },
];

export default function GTMTweetsPage() {
  const [tweets, setTweets] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterType, setFilterType] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editContent, setEditContent] = useState('');
  const [customTopic, setCustomTopic] = useState('');
  const [selectedType, setSelectedType] = useState('product');
  const [tab, setTab] = useState('all');

  // Visual generation state
  const [selectedTemplate, setSelectedTemplate] = useState('feature_card');
  const [templateData, setTemplateData] = useState({});
  const [generatingVisual, setGeneratingVisual] = useState(false);
  const [previewImage, setPreviewImage] = useState(null);

  // AI Design state
  const [aiVisualType, setAiVisualType] = useState('flow_diagram');
  const [aiConcept, setAiConcept] = useState('');
  const [aiWithTweet, setAiWithTweet] = useState(true);
  const [generatingAI, setGeneratingAI] = useState(false);

  const loadTweets = async () => {
    setLoading(true);
    try {
      const res = await getMarketingTweets(filterStatus || null, filterType || null, 50, 0);
      setTweets(res.data.tweets);
      setTotal(res.data.total);
    } catch (e) {
      console.error('Failed to load tweets:', e);
    }
    setLoading(false);
  };

  useEffect(() => { loadTweets(); }, [filterStatus, filterType]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await generateMarketingTweet(selectedType, customTopic || null);
      setCustomTopic('');
      await loadTweets();
    } catch (e) {
      console.error('Generate failed:', e);
    }
    setGenerating(false);
  };

  const handleGenerateVisualTweet = async () => {
    setGeneratingVisual(true);
    try {
      const res = await generateVisualTweet(selectedTemplate, { ...templateData, tweet_topic: templateData.TITLE || templateData.BADGE || '' });
      setTemplateData({});
      await loadTweets();
      alert(`Visual tweet created! ID: ${res.data.tweet_id}`);
    } catch (e) {
      alert(`Failed: ${e.response?.data?.detail || e.message}`);
    }
    setGeneratingVisual(false);
  };

  const handleAIDesign = async () => {
    if (!aiConcept.trim()) return alert('Describe what the visual should show.');
    setGeneratingAI(true);
    try {
      const res = await aiDesignVisual(aiConcept, aiVisualType, aiWithTweet);
      setAiConcept('');
      await loadTweets();
      const msg = res.data.tweet_id
        ? `AI visual + tweet created! Tweet #${res.data.tweet_id}`
        : `AI visual created: ${res.data.filename}`;
      alert(msg);
    } catch (e) {
      alert(`AI design failed: ${e.response?.data?.detail || e.message}`);
    }
    setGeneratingAI(false);
  };

  const handlePost = async (id) => {
    try {
      await postMarketingTweet(id);
      await loadTweets();
    } catch (e) {
      alert(`Post failed: ${e.response?.data?.detail || e.message}`);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this tweet?')) return;
    try {
      await deleteMarketingTweet(id);
      await loadTweets();
    } catch (e) { console.error(e); }
  };

  const handleSaveEdit = async (id) => {
    try {
      await editMarketingTweet(id, editContent);
      setEditingId(null);
      await loadTweets();
    } catch (e) { console.error(e); }
  };

  const typeInfo = (type) => CONTENT_TYPES.find(t => t.id === type) || CONTENT_TYPES[0];

  const visualTweets = tweets.filter(t => t.media_url);
  const displayTweets = tab === 'visual' ? visualTweets : tweets;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">GTM Tweets</h1>
          <p className="text-gray-400 text-sm mt-1">kualia.ai marketing tweets — {total} total</p>
        </div>
        <button onClick={loadTweets} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 mb-5 border-b border-gray-800 pb-1">
        {[
          { id: 'all', label: 'All Tweets', icon: Send },
          { id: 'visual', label: 'Visual Tweets', icon: ImageIcon },
          { id: 'generate', label: 'Generate', icon: Plus },
          { id: 'ai-design', label: 'AI Design', icon: Zap },
          { id: 'visual-gen', label: 'Templates', icon: ImageIcon },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-t-lg text-sm font-medium transition-all ${
              tab === t.id ? 'bg-gray-800 text-white' : 'text-gray-500 hover:text-gray-300'
            }`}>
            <t.icon className="w-4 h-4" /> {t.label}
            {t.id === 'visual' && visualTweets.length > 0 && (
              <span className="ml-1 text-[10px] bg-purple-900/30 text-purple-400 px-1.5 py-0.5 rounded">{visualTweets.length}</span>
            )}
          </button>
        ))}
      </div>

      {/* Generate Text Tweet */}
      {tab === 'generate' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
          <h3 className="text-white font-semibold mb-3">Generate Text Tweet</h3>
          <div className="flex gap-2 mb-3">
            {CONTENT_TYPES.map(ct => (
              <button key={ct.id} onClick={() => setSelectedType(ct.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedType === ct.id
                    ? `bg-${ct.color}-500/20 text-${ct.color}-400 border border-${ct.color}-500/30`
                    : 'bg-gray-800 text-gray-400 hover:text-white border border-transparent'
                }`}>
                <ct.icon className="w-4 h-4" />{ct.label}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <input type="text" value={customTopic} onChange={e => setCustomTopic(e.target.value)}
              placeholder="Custom topic (optional)..."
              className="flex-1 px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-blue-500" />
            <button onClick={handleGenerate} disabled={generating}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium disabled:opacity-50">
              {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              {generating ? 'Generating...' : 'Generate'}
            </button>
          </div>
        </div>
      )}

      {/* AI Design Visual */}
      {tab === 'ai-design' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
          <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" /> AI Visual Designer
          </h3>
          <p className="text-xs text-gray-500 mb-4">
            Describe what you want the visual to show. The AI will design custom HTML/CSS and render it to a professional image.
          </p>

          <div className="flex flex-wrap gap-2 mb-4">
            {AI_VISUAL_TYPES.map(vt => (
              <button key={vt.id} onClick={() => setAiVisualType(vt.id)}
                className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  aiVisualType === vt.id
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-gray-800 text-gray-400 hover:text-white border border-transparent'
                }`}
                title={vt.desc}>
                {vt.label}
              </button>
            ))}
          </div>

          <textarea
            value={aiConcept}
            onChange={e => setAiConcept(e.target.value)}
            placeholder="Describe the visual concept... e.g. 'How to generate an RL environment on kualia.ai in 3 steps: 1. Describe your environment 2. AI generates Gymnasium code 3. Train your agent with PPO/SAC'"
            rows={4}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus:border-amber-500 resize-none mb-3"
          />

          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
              <input type="checkbox" checked={aiWithTweet} onChange={e => setAiWithTweet(e.target.checked)}
                className="rounded border-gray-600" />
              Also generate a tweet for this visual
            </label>
            <button onClick={handleAIDesign} disabled={generatingAI || !aiConcept.trim()}
              className="flex items-center gap-2 px-5 py-2.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm font-medium disabled:opacity-50">
              {generatingAI ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              {generatingAI ? 'AI is designing...' : 'Design & Render'}
            </button>
          </div>
        </div>
      )}

      {/* Generate Visual Tweet (Static Templates) */}
      {tab === 'visual-gen' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
          <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
            <ImageIcon className="w-5 h-5 text-purple-400" /> Generate Visual Tweet
          </h3>
          <p className="text-xs text-gray-500 mb-4">Select a template, fill in the data, and generate a tweet with an attached visual card.</p>

          <div className="flex gap-2 mb-4">
            {VISUAL_TEMPLATES.map(vt => (
              <button key={vt.id} onClick={() => { setSelectedTemplate(vt.id); setTemplateData({}); }}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedTemplate === vt.id
                    ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                    : 'bg-gray-800 text-gray-400 hover:text-white border border-transparent'
                }`}>
                {vt.label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            {VISUAL_TEMPLATES.find(v => v.id === selectedTemplate)?.fields.map(field => (
              <div key={field}>
                <label className="text-xs text-gray-500 mb-1 block">{field}</label>
                {field === 'CODE' || field === 'DESCRIPTION' ? (
                  <textarea
                    value={templateData[field] || ''}
                    onChange={e => setTemplateData(prev => ({ ...prev, [field]: e.target.value }))}
                    placeholder={field}
                    rows={3}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus:border-purple-500 resize-none"
                  />
                ) : (
                  <input
                    type="text"
                    value={templateData[field] || ''}
                    onChange={e => setTemplateData(prev => ({ ...prev, [field]: e.target.value }))}
                    placeholder={field}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus:border-purple-500"
                  />
                )}
              </div>
            ))}
          </div>

          <button onClick={handleGenerateVisualTweet} disabled={generatingVisual}
            className="flex items-center gap-2 px-5 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-sm font-medium disabled:opacity-50">
            {generatingVisual ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ImageIcon className="w-4 h-4" />}
            {generatingVisual ? 'Generating...' : 'Generate Visual Tweet'}
          </button>
        </div>
      )}

      {/* Filters (for all & visual tabs) */}
      {(tab === 'all' || tab === 'visual') && (
        <div className="flex gap-3 mb-4">
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-300">
            <option value="">All Status</option>
            <option value="draft">Draft</option>
            <option value="posted">Posted</option>
            <option value="failed">Failed</option>
          </select>
          <select value={filterType} onChange={e => setFilterType(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-300">
            <option value="">All Types</option>
            {CONTENT_TYPES.map(ct => (<option key={ct.id} value={ct.id}>{ct.label}</option>))}
          </select>
        </div>
      )}

      {/* Tweet List */}
      {(tab === 'all' || tab === 'visual') && (
        loading ? (
          <div className="text-center py-12 text-gray-500">Loading...</div>
        ) : displayTweets.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            {tab === 'visual' ? 'No visual tweets yet. Generate one in the "Generate Visual Tweet" tab.' : 'No tweets yet.'}
          </div>
        ) : (
          <div className="space-y-3">
            {displayTweets.map(tweet => {
              const ti = typeInfo(tweet.content_type);
              const mediaFilename = tweet.media_url ? tweet.media_url.split('/').pop() : null;
              return (
                <div key={tweet.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[tweet.status] || ''}`}>
                          {tweet.status}
                        </span>
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-800 text-gray-400">{ti.label}</span>
                        {tweet.media_url && (
                          <span className="px-2 py-0.5 rounded text-xs font-medium bg-purple-900/30 text-purple-400 flex items-center gap-1">
                            <ImageIcon className="w-3 h-3" /> Visual
                          </span>
                        )}
                        {tweet.posted_at && (
                          <span className="text-xs text-gray-500">{new Date(tweet.posted_at).toLocaleDateString()}</span>
                        )}
                      </div>

                      {editingId === tweet.id ? (
                        <div className="flex gap-2">
                          <textarea value={editContent} onChange={e => setEditContent(e.target.value)}
                            className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm resize-none" rows={3} />
                          <div className="flex flex-col gap-1">
                            <button onClick={() => handleSaveEdit(tweet.id)} className="p-2 text-green-400 hover:bg-green-900/30 rounded"><Check className="w-4 h-4" /></button>
                            <button onClick={() => setEditingId(null)} className="p-2 text-gray-400 hover:bg-gray-800 rounded"><X className="w-4 h-4" /></button>
                          </div>
                        </div>
                      ) : (
                        <p className="text-gray-300 text-sm whitespace-pre-wrap">{tweet.content}</p>
                      )}

                      {mediaFilename && (
                        <div className="mt-3 relative group">
                          <img
                            src={`/api/marketing/visuals/${mediaFilename}`}
                            alt="Tweet visual"
                            className="rounded-lg border border-gray-700 max-h-48 object-cover"
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        </div>
                      )}

                      {tweet.status === 'posted' && (
                        <div className="flex gap-4 mt-2 text-xs text-gray-500">
                          <span>❤️ {tweet.likes}</span>
                          <span>🔁 {tweet.retweets}</span>
                          <span>💬 {tweet.replies_count}</span>
                          <span>👁 {tweet.impressions}</span>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-1">
                      {tweet.status !== 'posted' && (
                        <>
                          <button onClick={() => handlePost(tweet.id)} className="p-2 text-green-400 hover:bg-green-900/30 rounded-lg" title="Post"><Send className="w-4 h-4" /></button>
                          <button onClick={() => { setEditingId(tweet.id); setEditContent(tweet.content); }} className="p-2 text-blue-400 hover:bg-blue-900/30 rounded-lg" title="Edit"><Edit3 className="w-4 h-4" /></button>
                        </>
                      )}
                      <button onClick={() => handleDelete(tweet.id)} className="p-2 text-red-400 hover:bg-red-900/30 rounded-lg" title="Delete"><Trash2 className="w-4 h-4" /></button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )
      )}

      {/* Image Preview Modal */}
      {previewImage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70" onClick={() => setPreviewImage(null)}>
          <img src={previewImage} alt="Preview" className="max-w-3xl max-h-[80vh] rounded-xl shadow-2xl" />
        </div>
      )}
    </div>
  );
}
