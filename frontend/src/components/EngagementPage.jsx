import React, { useState, useEffect } from 'react';
import {
  Heart, Search, MessageCircle, RefreshCw, Target,
  UserPlus, Check, X, ExternalLink, Zap,
} from 'lucide-react';
import {
  getMarketingEngagementLog, marketingSearchAndLike, getMarketingEngagementStats,
  getProspects, getProspectFunnel, discoverProspects, approveReply, rejectReply,
  updateProspectStage,
} from '../api';

const STAGE_COLORS = {
  detected: 'text-gray-400 bg-gray-800',
  engaged: 'text-blue-400 bg-blue-900/30',
  warm: 'text-yellow-400 bg-yellow-900/30',
  converted: 'text-green-400 bg-green-900/30',
  disqualified: 'text-red-400 bg-red-900/30',
};

export default function EngagementPage() {
  const [tab, setTab] = useState('overview');
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [prospects, setProspects] = useState([]);
  const [funnel, setFunnel] = useState(null);
  const [pendingReplies, setPendingReplies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [logsRes, statsRes, prospectsRes, funnelRes] = await Promise.all([
        getMarketingEngagementLog(null, 30),
        getMarketingEngagementStats(7),
        getProspects(null, 0, 50),
        getProspectFunnel(),
      ]);
      setLogs(logsRes.data.logs);
      setStats(statsRes.data);
      setProspects(prospectsRes.data.prospects);
      setFunnel(funnelRes.data);
      setPendingReplies(logsRes.data.logs.filter(l => l.action_type === 'reply_suggestion' && l.status === 'pending_approval'));
    } catch (e) {
      console.error('Failed to load:', e);
    }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const handleEngage = async () => {
    setActing(true);
    try {
      const res = await marketingSearchAndLike(15);
      const d = res.data;
      alert(`Liked ${d.liked} tweets, ${d.reply_suggestions || 0} reply suggestions (query: "${d.query}")`);
      await loadData();
    } catch (e) {
      alert(`Failed: ${e.response?.data?.detail || e.message}`);
    }
    setActing(false);
  };

  const handleDiscover = async () => {
    setActing(true);
    try {
      const res = await discoverProspects(20);
      alert(`Discovered ${res.data.discovered} new prospects (query: "${res.data.query}")`);
      await loadData();
    } catch (e) {
      alert(`Failed: ${e.response?.data?.detail || e.message}`);
    }
    setActing(false);
  };

  const handleApprove = async (id) => {
    try {
      await approveReply(id);
      await loadData();
    } catch (e) {
      alert(`Approve failed: ${e.response?.data?.detail || e.message}`);
    }
  };

  const handleReject = async (id) => {
    try {
      await rejectReply(id);
      await loadData();
    } catch (e) {
      alert(`Reject failed: ${e.response?.data?.detail || e.message}`);
    }
  };

  const handleStageChange = async (id, stage) => {
    try {
      await updateProspectStage(id, stage);
      await loadData();
    } catch (e) {
      console.error('Stage update failed:', e);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'replies', label: `Replies${pendingReplies.length ? ` (${pendingReplies.length})` : ''}` },
    { id: 'prospects', label: 'Prospects' },
    { id: 'activity', label: 'Activity Log' },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">GTM Engagement</h1>
          <p className="text-gray-400 text-sm mt-1">User acquisition engine — prospects, replies, strategic engagement</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleDiscover} disabled={acting}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-sm font-medium disabled:opacity-50">
            {acting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
            Discover
          </button>
          <button onClick={handleEngage} disabled={acting}
            className="flex items-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 text-white rounded-lg text-sm font-medium disabled:opacity-50">
            {acting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            Engage
          </button>
          <button onClick={loadData} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-gray-800 pb-1">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-all ${
              tab === t.id ? 'bg-gray-800 text-white' : 'text-gray-500 hover:text-gray-300'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : tab === 'overview' ? (
        <OverviewTab stats={stats} funnel={funnel} pendingReplies={pendingReplies} />
      ) : tab === 'replies' ? (
        <RepliesTab replies={pendingReplies} onApprove={handleApprove} onReject={handleReject} />
      ) : tab === 'prospects' ? (
        <ProspectsTab prospects={prospects} onStageChange={handleStageChange} />
      ) : (
        <ActivityTab logs={logs} />
      )}
    </div>
  );
}

function OverviewTab({ stats, funnel, pendingReplies }) {
  if (!stats) return null;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatBox label="Likes (7d)" value={stats.total_likes} icon={Heart} color="pink" />
        <StatBox label="Replies Sent" value={stats.total_replies} icon={MessageCircle} color="blue" />
        <StatBox label="Pending Replies" value={stats.pending_replies || pendingReplies?.length || 0} icon={MessageCircle} color="yellow" />
        <StatBox label="New Prospects" value={stats.new_prospects} icon={UserPlus} color="purple" />
        <StatBox label="Reply Suggestions" value={stats.total_reply_suggestions} icon={Target} color="cyan" />
      </div>

      {funnel && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wider">Prospect Funnel</h3>
          <div className="flex items-end gap-3">
            {Object.entries(funnel.funnel).map(([stage, count]) => {
              const max = Math.max(...Object.values(funnel.funnel), 1);
              const pct = (count / max) * 100;
              const colors = { detected: 'bg-gray-600', engaged: 'bg-blue-500', warm: 'bg-yellow-500', converted: 'bg-green-500', disqualified: 'bg-red-500/40' };
              return (
                <div key={stage} className="flex-1 text-center">
                  <div className="text-lg font-bold text-white">{count}</div>
                  <div className={`h-20 rounded-t-lg ${colors[stage] || 'bg-gray-700'} transition-all`}
                    style={{ height: `${Math.max(pct, 8)}%`, minHeight: '8px' }} />
                  <div className="text-xs text-gray-500 mt-1 capitalize">{stage}</div>
                </div>
              );
            })}
          </div>
          <div className="mt-4 pt-3 border-t border-gray-800 flex justify-between text-xs text-gray-500">
            <span>Total: {funnel.total_prospects}</span>
            <span>Avg Score: {funnel.avg_score}</span>
            <span>High Value (70+): {funnel.high_value_count}</span>
          </div>
        </div>
      )}

      {stats.daily_breakdown && stats.daily_breakdown.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">Daily Activity (7d)</h3>
          <div className="flex items-end gap-2 h-24">
            {stats.daily_breakdown.map((day, i) => {
              const maxVal = Math.max(...stats.daily_breakdown.map(d => d.likes + (d.replies || 0)), 1);
              const total = day.likes + (day.replies || 0);
              const pct = (total / maxVal) * 100;
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-xs text-gray-500">{total}</span>
                  <div className="w-full flex flex-col rounded-t overflow-hidden"
                    style={{ height: `${Math.max(pct, 4)}%` }}>
                    <div className="flex-1 bg-pink-500/40" />
                    {day.replies > 0 && <div className="bg-blue-500/60" style={{ height: `${(day.replies / total) * 100}%` }} />}
                  </div>
                  <span className="text-[10px] text-gray-600">{day.date.slice(5)}</span>
                </div>
              );
            })}
          </div>
          <div className="flex gap-4 mt-2 text-xs text-gray-600">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-pink-500/40" /> Likes</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-blue-500/60" /> Replies</span>
          </div>
        </div>
      )}
    </div>
  );
}

function RepliesTab({ replies, onApprove, onReject }) {
  if (!replies || replies.length === 0) {
    return <div className="text-center py-12 text-gray-500">No pending reply suggestions. Run "Engage" to generate some.</div>;
  }
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-400 mb-2">{replies.length} replies awaiting your approval. Approve to post, reject to discard.</p>
      {replies.map(r => (
        <div key={r.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs text-blue-400 font-medium">@{r.target_username}</span>
            {r.target_tweet_id && (
              <a href={`https://twitter.com/i/web/status/${r.target_tweet_id}`} target="_blank" rel="noreferrer"
                className="text-gray-600 hover:text-gray-400"><ExternalLink className="w-3 h-3" /></a>
            )}
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3 mb-3">
            <p className="text-sm text-gray-400 italic">"{r.target_text}"</p>
          </div>
          <div className="bg-blue-950/20 border border-blue-900/30 rounded-lg p-3 mb-3">
            <p className="text-sm text-white">{r.reply_suggestion}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => onApprove(r.id)}
              className="flex items-center gap-1 px-3 py-1.5 bg-green-600 hover:bg-green-500 text-white rounded-lg text-xs font-medium">
              <Check className="w-3 h-3" /> Approve & Post
            </button>
            <button onClick={() => onReject(r.id)}
              className="flex items-center gap-1 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-xs font-medium">
              <X className="w-3 h-3" /> Reject
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function ProspectsTab({ prospects, onStageChange }) {
  const [stageFilter, setStageFilter] = useState('');
  const filtered = stageFilter ? prospects.filter(p => p.stage === stageFilter) : prospects;

  return (
    <div>
      <div className="flex gap-2 mb-4">
        {['', 'detected', 'engaged', 'warm', 'converted'].map(s => (
          <button key={s} onClick={() => setStageFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
              stageFilter === s ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}>
            {s || 'All'}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-12 text-gray-500">No prospects found. Click "Discover" to find potential users.</div>
      ) : (
        <div className="space-y-2">
          {filtered.map(p => (
            <div key={p.id} className="bg-gray-900 border border-gray-800 rounded-lg p-3 flex items-start gap-3">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center">
                <span className={`text-sm font-bold ${p.score >= 70 ? 'text-green-400' : p.score >= 50 ? 'text-yellow-400' : 'text-gray-500'}`}>
                  {p.score}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <a href={`https://twitter.com/${p.twitter_username}`} target="_blank" rel="noreferrer"
                    className="text-sm font-medium text-blue-400 hover:underline">@{p.twitter_username}</a>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${STAGE_COLORS[p.stage] || ''}`}>{p.stage}</span>
                  {p.tags && p.tags.split(',').map(t => (
                    <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-500">{t.trim()}</span>
                  ))}
                </div>
                {p.first_seen_tweet && (
                  <p className="text-xs text-gray-500 mt-1 truncate">{p.first_seen_tweet}</p>
                )}
                {p.notes && (
                  <p className="text-xs text-gray-600 mt-0.5 italic">{p.notes}</p>
                )}
                <div className="flex items-center gap-3 mt-1 text-[10px] text-gray-600">
                  <span>{p.total_interactions} interactions</span>
                  {p.last_interaction_at && <span>Last: {new Date(p.last_interaction_at).toLocaleDateString()}</span>}
                </div>
              </div>
              <select value={p.stage} onChange={e => onStageChange(p.id, e.target.value)}
                className="text-xs bg-gray-800 border border-gray-700 rounded px-2 py-1 text-gray-300">
                <option value="detected">Detected</option>
                <option value="engaged">Engaged</option>
                <option value="warm">Warm</option>
                <option value="converted">Converted</option>
                <option value="disqualified">Disqualified</option>
              </select>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ActivityTab({ logs }) {
  if (!logs || logs.length === 0) {
    return <div className="text-center py-12 text-gray-500">No activity yet.</div>;
  }
  return (
    <div className="space-y-2">
      {logs.map(log => (
        <div key={log.id} className="bg-gray-900 border border-gray-800 rounded-lg p-3 flex items-start gap-3">
          <div className={`p-1.5 rounded-lg ${
            log.action_type === 'like' ? 'bg-pink-500/10' :
            log.action_type === 'reply' ? 'bg-green-500/10' :
            log.action_type === 'reply_suggestion' ? 'bg-blue-500/10' :
            log.action_type === 'prospect_detect' ? 'bg-purple-500/10' : 'bg-gray-800'
          }`}>
            {log.action_type === 'like' ? <Heart className="w-4 h-4 text-pink-400" /> :
             log.action_type === 'reply' || log.action_type === 'reply_suggestion' ? <MessageCircle className="w-4 h-4 text-blue-400" /> :
             log.action_type === 'prospect_detect' ? <UserPlus className="w-4 h-4 text-purple-400" /> :
             <Search className="w-4 h-4 text-gray-400" />}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-gray-400 uppercase">{log.action_type.replace(/_/g, ' ')}</span>
              {log.target_username && <span className="text-xs text-blue-400">@{log.target_username}</span>}
              <span className={`text-xs px-1.5 py-0.5 rounded ${
                log.status === 'completed' ? 'text-green-400 bg-green-900/20' :
                log.status === 'failed' ? 'text-red-400 bg-red-900/20' :
                log.status === 'pending_approval' ? 'text-yellow-400 bg-yellow-900/20' :
                log.status === 'rejected' ? 'text-red-400 bg-red-900/10' :
                'text-gray-400 bg-gray-800'
              }`}>{log.status}</span>
            </div>
            {log.target_text && <p className="text-sm text-gray-300 mt-1 truncate">{log.target_text}</p>}
            {log.reply_suggestion && <p className="text-sm text-blue-300 mt-1 italic truncate">Reply: {log.reply_suggestion}</p>}
            <p className="text-xs text-gray-600 mt-1">
              {log.created_at ? new Date(log.created_at).toLocaleString() : ''}
              {log.search_query && ` · "${log.search_query}"`}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

function StatBox({ label, value, icon: Icon, color }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 bg-${color}-500/10 rounded-lg`}>
          <Icon className={`w-5 h-5 text-${color}-400`} />
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{value ?? 0}</p>
          <p className="text-xs text-gray-500">{label}</p>
        </div>
      </div>
    </div>
  );
}
