import React, { useState, useEffect } from 'react';
import {
  MessageSquareText, Bug, Lightbulb, HelpCircle, RefreshCw,
  ChevronDown, ChevronRight, Bot, AlertTriangle, CheckCircle,
  Clock, ArrowUpRight, Filter, Search,
} from 'lucide-react';
import axios from 'axios';

const typeIcons = {
  bug: Bug,
  feature: Lightbulb,
  question: HelpCircle,
  general: MessageSquareText,
};
const typeColors = {
  bug: 'text-red-400 bg-red-500/10',
  feature: 'text-yellow-400 bg-yellow-500/10',
  question: 'text-blue-400 bg-blue-500/10',
  general: 'text-gray-400 bg-gray-500/10',
};
const priorityColors = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};
const statusOptions = ['new', 'reviewed', 'in_progress', 'resolved', 'wont_fix'];
const statusColors = {
  new: 'bg-blue-500/20 text-blue-400',
  reviewed: 'bg-purple-500/20 text-purple-400',
  in_progress: 'bg-yellow-500/20 text-yellow-400',
  resolved: 'bg-green-500/20 text-green-400',
  wont_fix: 'bg-gray-700 text-gray-400',
};
const sentimentEmoji = {
  positive: '😊',
  neutral: '😐',
  negative: '😕',
  frustrated: '😤',
};

export default function FeedbackPage() {
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState({});
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => { load(); }, [filterStatus, filterType, filterPriority]);

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterStatus) params.set('status', filterStatus);
      if (filterType) params.set('type', filterType);
      if (filterPriority) params.set('priority', filterPriority);
      params.set('limit', '100');
      const { data } = await axios.get(`/api/feedback/all?${params}`);
      setItems(data.items || []);
      setStats(data.stats || {});
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to load feedback:', err);
    }
    setLoading(false);
  };

  const updateFeedback = async (id, updates) => {
    try {
      await axios.put(`/api/feedback/${id}`, updates);
      load();
    } catch (err) {
      console.error('Update failed:', err);
    }
  };

  const reanalyze = async (id) => {
    try {
      await axios.post(`/api/feedback/${id}/reanalyze`);
      load();
    } catch (err) {
      console.error('Reanalyze failed:', err);
    }
  };

  const filtered = searchTerm
    ? items.filter(i =>
        i.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        i.body.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (i.user_email || '').toLowerCase().includes(searchTerm.toLowerCase())
      )
    : items;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">User Feedback</h1>
          <p className="text-sm text-gray-400 mt-1">AI-analyzed feedback from platform users</p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 px-3 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 text-sm"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        {[
          { label: 'Total', value: stats.total || 0, color: 'text-white' },
          { label: 'New', value: stats.new || 0, color: 'text-blue-400' },
          { label: 'Reviewed', value: stats.reviewed || 0, color: 'text-purple-400' },
          { label: 'In Progress', value: stats.in_progress || 0, color: 'text-yellow-400' },
          { label: 'Resolved', value: stats.resolved || 0, color: 'text-green-400' },
        ].map(s => (
          <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-lg p-3 text-center">
            <div className={`text-xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-[10px] text-gray-500 uppercase">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search feedback..."
            className="w-full bg-gray-900 border border-gray-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-gray-600"
          />
        </div>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-300">
          <option value="">All Status</option>
          {statusOptions.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
        </select>
        <select value={filterType} onChange={e => setFilterType(e.target.value)} className="bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-300">
          <option value="">All Types</option>
          <option value="bug">Bug</option>
          <option value="feature">Feature</option>
          <option value="question">Question</option>
          <option value="general">General</option>
        </select>
        <select value={filterPriority} onChange={e => setFilterPriority(e.target.value)} className="bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-300">
          <option value="">All Priority</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* List */}
      {loading ? (
        <div className="text-center py-20 text-gray-500">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20">
          <MessageSquareText className="w-10 h-10 text-gray-700 mx-auto mb-3" />
          <p className="text-gray-500">No feedback yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map(item => {
            const expanded = expandedId === item.id;
            const TypeIcon = typeIcons[item.type] || MessageSquareText;
            return (
              <div key={item.id} className="border border-gray-800 rounded-lg bg-gray-900 overflow-hidden">
                <button
                  onClick={() => setExpandedId(expanded ? null : item.id)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-800/50 transition-colors"
                >
                  <div className={`p-1.5 rounded ${typeColors[item.type] || typeColors.general}`}>
                    <TypeIcon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white truncate">{item.title}</span>
                      {item.ai_sentiment && (
                        <span className="text-xs" title={item.ai_sentiment}>
                          {sentimentEmoji[item.ai_sentiment] || ''}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] text-gray-500">{item.user_email || 'Anonymous'}</span>
                      <span className="text-[10px] text-gray-600">·</span>
                      <span className="text-[10px] text-gray-600">{new Date(item.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {item.priority && (
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border ${priorityColors[item.priority] || ''}`}>
                        {item.priority}
                      </span>
                    )}
                    <span className={`text-[10px] px-2 py-0.5 rounded-full ${statusColors[item.status] || statusColors.new}`}>
                      {item.status.replace('_', ' ')}
                    </span>
                    {expanded ? <ChevronDown className="w-4 h-4 text-gray-500" /> : <ChevronRight className="w-4 h-4 text-gray-500" />}
                  </div>
                </button>

                {expanded && (
                  <div className="px-4 pb-4 border-t border-gray-800 pt-3 space-y-4">
                    {/* User message */}
                    <div>
                      <p className="text-xs text-gray-500 uppercase mb-1">User Feedback</p>
                      <p className="text-sm text-gray-300 whitespace-pre-wrap">{item.body}</p>
                      {item.page_url && (
                        <p className="text-[10px] text-gray-600 mt-1">Page: {item.page_url}</p>
                      )}
                    </div>

                    {/* AI Analysis */}
                    {(item.ai_summary || item.ai_suggested_action || item.ai_category) && (
                      <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <Bot className="w-4 h-4 text-amber-400" />
                          <span className="text-xs font-medium text-amber-400">AI Analysis</span>
                        </div>
                        {item.ai_category && (
                          <div className="text-[10px] text-gray-400 mb-1">
                            Category: <span className="text-gray-300">{item.ai_category.replace('_', ' ')}</span>
                          </div>
                        )}
                        {item.ai_summary && (
                          <p className="text-xs text-gray-300 mb-2">{item.ai_summary}</p>
                        )}
                        {item.ai_suggested_action && (
                          <div className="flex items-start gap-2 bg-gray-900/50 rounded p-2">
                            <ArrowUpRight className="w-3 h-3 text-emerald-400 mt-0.5 shrink-0" />
                            <p className="text-xs text-emerald-300">{item.ai_suggested_action}</p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Admin controls */}
                    <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-gray-800">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-gray-500">Status:</span>
                        <select
                          value={item.status}
                          onChange={e => updateFeedback(item.id, { status: e.target.value })}
                          className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-300"
                        >
                          {statusOptions.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
                        </select>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-gray-500">Priority:</span>
                        <select
                          value={item.priority || ''}
                          onChange={e => updateFeedback(item.id, { priority: e.target.value })}
                          className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-300"
                        >
                          <option value="">None</option>
                          <option value="critical">Critical</option>
                          <option value="high">High</option>
                          <option value="medium">Medium</option>
                          <option value="low">Low</option>
                        </select>
                      </div>
                      <button
                        onClick={() => reanalyze(item.id)}
                        className="flex items-center gap-1 px-2 py-1 text-[10px] text-amber-400 border border-amber-500/30 rounded hover:bg-amber-500/10"
                      >
                        <RefreshCw className="w-3 h-3" /> Re-analyze
                      </button>
                    </div>

                    {/* Admin notes */}
                    <div>
                      <p className="text-[10px] text-gray-500 uppercase mb-1">Admin Notes</p>
                      <textarea
                        defaultValue={item.admin_notes || ''}
                        onBlur={e => {
                          if (e.target.value !== (item.admin_notes || '')) {
                            updateFeedback(item.id, { admin_notes: e.target.value });
                          }
                        }}
                        rows={2}
                        placeholder="Add internal notes..."
                        className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-xs text-gray-300 placeholder:text-gray-600 resize-none focus:outline-none focus:border-gray-500"
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
