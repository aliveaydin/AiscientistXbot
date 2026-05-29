import React, { useState, useEffect, useCallback } from 'react';
import {
  Mail, Send, BarChart3, FileText, Clock,
  CheckCircle, XCircle, Filter, RefreshCw, Eye,
  Loader2, AlertTriangle, Zap, Users, Bot,
  Lightbulb, UserX, TrendingUp, Play,
} from 'lucide-react';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL || '';

export default function EmailPage() {
  const [tab, setTab] = useState('stats');
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [logsTotal, setLogsTotal] = useState(0);
  const [templates, setTemplates] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [previewHtml, setPreviewHtml] = useState('');
  const [previewName, setPreviewName] = useState('');
  const [filterChannel, setFilterChannel] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState(null);
  const [evaluation, setEvaluation] = useState(null);

  // compose state
  const [composeTemplate, setComposeTemplate] = useState('');
  const [composeSubject, setComposeSubject] = useState('');
  const [composeBody, setComposeBody] = useState('');
  const [composeTarget, setComposeTarget] = useState('all');

  // agent actions
  const [agentLoading, setAgentLoading] = useState('');
  const [featureDesc, setFeatureDesc] = useState('');
  const [expandedCampaign, setExpandedCampaign] = useState(null);
  const [campaignPreviewHtml, setCampaignPreviewHtml] = useState('');

  const fetchStats = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/api/email/stats`);
      setStats(data);
    } catch (e) { console.error(e); }
  }, []);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterChannel) params.channel = filterChannel;
      if (filterStatus) params.status = filterStatus;
      const { data } = await axios.get(`${API}/api/email/logs`, { params });
      setLogs(data.logs || []);
      setLogsTotal(data.total || 0);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [filterChannel, filterStatus]);

  const fetchTemplates = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/api/email/templates`);
      setTemplates(data.templates || []);
    } catch (e) { console.error(e); }
  }, []);

  const fetchCampaigns = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/api/email/campaigns`);
      setCampaigns(data.campaigns || []);
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => {
    fetchStats();
    fetchTemplates();
    fetchCampaigns();
  }, [fetchStats, fetchTemplates, fetchCampaigns]);

  useEffect(() => {
    if (tab === 'logs') fetchLogs();
  }, [tab, fetchLogs]);

  const previewTemplate = async (name) => {
    try {
      const { data } = await axios.get(`${API}/api/email/templates/${name}/preview`);
      setPreviewHtml(data.html);
      setPreviewName(name);
    } catch (e) { console.error(e); }
  };

  const sendEmail = async () => {
    setSending(true);
    setSendResult(null);
    try {
      const payload = { target: composeTarget, channel: 'marketing' };
      if (composeTemplate) {
        payload.template = composeTemplate;
        payload.subject = composeSubject || undefined;
        payload.body_html = composeBody || undefined;
      } else {
        payload.subject = composeSubject;
        payload.body_html = composeBody;
      }
      const { data } = await axios.post(`${API}/api/email/send`, payload);
      setSendResult(data);
      fetchStats();
    } catch (e) {
      setSendResult({ error: e.response?.data?.detail || e.message });
    }
    setSending(false);
  };

  const agentAction = async (action, body = null) => {
    setAgentLoading(action);
    try {
      const url = `${API}/api/email/campaigns/${action}`;
      const { data } = body ? await axios.post(url, body) : (action === 'evaluate' ? await axios.get(url) : await axios.post(url));
      if (action === 'evaluate') setEvaluation(data);
      fetchCampaigns();
      fetchStats();
    } catch (e) {
      console.error(e);
    }
    setAgentLoading('');
  };

  const sendCampaign = async (id) => {
    setAgentLoading(`send-${id}`);
    try {
      await axios.post(`${API}/api/email/campaigns/${id}/send`);
      fetchCampaigns();
      fetchStats();
    } catch (e) { console.error(e); }
    setAgentLoading('');
  };

  const tabs = [
    { id: 'stats', label: 'Dashboard', icon: BarChart3 },
    { id: 'agent', label: 'Agent', icon: Bot },
    { id: 'campaigns', label: 'Campaigns', icon: Zap },
    { id: 'logs', label: 'Logs', icon: FileText },
    { id: 'compose', label: 'Compose', icon: Send },
    { id: 'templates', label: 'Templates', icon: Mail },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-500/20 rounded-xl flex items-center justify-center">
              <Mail className="w-5 h-5 text-purple-400" />
            </div>
            Email
          </h1>
          <p className="text-gray-500 mt-1 text-sm">AI-managed transactional & marketing emails</p>
        </div>
      </div>

      <div className="flex gap-1 border-b border-gray-800 overflow-x-auto">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors whitespace-nowrap ${
              tab === t.id ? 'border-purple-400 text-purple-400' : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Stats */}
      {tab === 'stats' && stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { label: 'Total Sent', value: stats.total_sent, icon: CheckCircle, color: 'text-green-400' },
            { label: 'Total Failed', value: stats.total_failed, icon: XCircle, color: 'text-red-400' },
            { label: 'Sent Today', value: stats.today_sent, icon: Clock, color: 'text-blue-400' },
            { label: 'Sent This Week', value: stats.week_sent, icon: BarChart3, color: 'text-purple-400' },
            { label: 'Transactional', value: stats.transactional, icon: Mail, color: 'text-cyan-400' },
            { label: 'Marketing', value: stats.marketing, icon: Send, color: 'text-amber-400' },
          ].map(s => (
            <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-2">
                <s.icon className={`w-4 h-4 ${s.color}`} />
                <span className="text-xs text-gray-500 uppercase tracking-wide">{s.label}</span>
              </div>
              <p className="text-2xl font-bold text-white">{s.value}</p>
            </div>
          ))}
        </div>
      )}
      {tab === 'stats' && !stats && (
        <div className="text-center py-12 text-gray-500"><Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />Loading...</div>
      )}

      {/* Agent */}
      {tab === 'agent' && (
        <div className="space-y-5">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-purple-500/20 rounded-xl flex items-center justify-center text-lg">📧</div>
              <div>
                <h3 className="text-white font-bold text-sm">Email Marketing Agent</h3>
                <p className="text-gray-500 text-xs">AI-driven campaign lifecycle management</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Lightbulb className="w-4 h-4 text-amber-400" />
                  <h4 className="text-white text-sm font-medium">Weekly RL Tip</h4>
                </div>
                <p className="text-xs text-gray-500 mb-4">AI generates an insightful RL tip and sends to all subscribers.</p>
                <button
                  onClick={() => agentAction('generate-tips')}
                  disabled={agentLoading === 'generate-tips'}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg"
                >
                  {agentLoading === 'generate-tips' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  Generate & Send
                </button>
              </div>

              <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <UserX className="w-4 h-4 text-red-400" />
                  <h4 className="text-white text-sm font-medium">Re-engagement</h4>
                </div>
                <p className="text-xs text-gray-500 mb-4">Find users inactive 7+ days and send friendly comeback emails.</p>
                <button
                  onClick={() => agentAction('reengagement')}
                  disabled={agentLoading === 'reengagement'}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg"
                >
                  {agentLoading === 'reengagement' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  Run Check
                </button>
              </div>

              <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-4 h-4 text-green-400" />
                  <h4 className="text-white text-sm font-medium">Performance Eval</h4>
                </div>
                <p className="text-xs text-gray-500 mb-4">AI analyzes metrics, recommends next campaigns.</p>
                <button
                  onClick={() => agentAction('evaluate')}
                  disabled={agentLoading === 'evaluate'}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg"
                >
                  {agentLoading === 'evaluate' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  Evaluate
                </button>
              </div>
            </div>
          </div>

          {/* Feature announcement generator */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="w-4 h-4 text-blue-400" />
              <h4 className="text-white text-sm font-medium">Feature Announcement</h4>
            </div>
            <p className="text-xs text-gray-500 mb-3">Describe a new feature and the AI writes + sends an announcement email.</p>
            <div className="flex gap-3">
              <input
                type="text"
                value={featureDesc}
                onChange={e => setFeatureDesc(e.target.value)}
                placeholder="e.g., Curriculum learning mode for progressive training difficulty"
                className="flex-1 bg-gray-800 border border-gray-700 text-white text-sm rounded-lg px-3 py-2"
              />
              <button
                onClick={() => { agentAction('generate-feature', { description: featureDesc }); setFeatureDesc(''); }}
                disabled={!featureDesc || agentLoading === 'generate-feature'}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg whitespace-nowrap"
              >
                {agentLoading === 'generate-feature' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Generate
              </button>
            </div>
          </div>

          {/* Evaluation results */}
          {evaluation && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h4 className="text-white text-sm font-medium mb-3">Latest Evaluation</h4>
              {evaluation.metrics && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  <div className="bg-gray-800 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500">Sent (7d)</p>
                    <p className="text-lg font-bold text-green-400">{evaluation.metrics.total_sent}</p>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500">Failed (7d)</p>
                    <p className="text-lg font-bold text-red-400">{evaluation.metrics.total_failed}</p>
                  </div>
                </div>
              )}
              {evaluation.action_plan && (
                <div className="bg-gray-800 rounded-lg p-4 text-sm">
                  <p className="text-gray-400 mb-1"><span className="text-white font-medium">Next campaign:</span> {evaluation.action_plan.next_campaign_type}</p>
                  <p className="text-gray-400 mb-1"><span className="text-white font-medium">Target:</span> {evaluation.action_plan.target}</p>
                  <p className="text-gray-400 mb-1"><span className="text-white font-medium">Topic:</span> {evaluation.action_plan.suggested_topic}</p>
                  <p className="text-gray-500 text-xs mt-2">{evaluation.action_plan.reason}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Campaigns */}
      {tab === 'campaigns' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-white font-medium text-sm">{campaigns.length} campaigns</h3>
            <button onClick={fetchCampaigns} className="p-2 text-gray-400 hover:text-white"><RefreshCw className="w-4 h-4" /></button>
          </div>
          <div className="space-y-3">
            {campaigns.map(c => {
              const isExpanded = expandedCampaign === c.id;
              return (
                <div key={c.id} className={`bg-gray-900 border rounded-xl overflow-hidden transition-colors ${isExpanded ? 'border-purple-500/50' : 'border-gray-800'}`}>
                  <div className="p-5">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-0.5 text-xs rounded ${
                          c.type === 'tips_tricks' ? 'bg-amber-500/20 text-amber-400' :
                          c.type === 'new_feature' ? 'bg-blue-500/20 text-blue-400' :
                          c.type === 'reengagement' ? 'bg-red-500/20 text-red-400' :
                          'bg-gray-700 text-gray-400'
                        }`}>{c.type}</span>
                        <h4 className="text-white text-sm font-medium">{c.name}</h4>
                        {c.ai_generated && <span className="text-[10px] bg-purple-500/20 text-purple-400 px-1.5 py-0.5 rounded">AI</span>}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs ${
                          c.status === 'sent' ? 'text-green-400' :
                          c.status === 'draft' ? 'text-yellow-400' :
                          c.status === 'sending' ? 'text-blue-400' : 'text-gray-500'
                        }`}>{c.status}</span>
                        <button
                          onClick={async () => {
                            if (isExpanded) { setExpandedCampaign(null); setCampaignPreviewHtml(''); return; }
                            setExpandedCampaign(c.id);
                            setCampaignPreviewHtml('');
                            try {
                              const { data } = await axios.get(`${API}/api/email/campaigns/${c.id}/preview`);
                              setCampaignPreviewHtml(data.html);
                            } catch(e) { console.error(e); }
                          }}
                          className="flex items-center gap-1 px-3 py-1 text-gray-400 hover:text-white text-xs rounded-lg border border-gray-700 hover:border-gray-500"
                        >
                          <Eye className="w-3 h-3" />
                          {isExpanded ? 'Close' : 'Preview'}
                        </button>
                        {c.status === 'draft' && (
                          <button
                            onClick={() => sendCampaign(c.id)}
                            disabled={agentLoading === `send-${c.id}`}
                            className="flex items-center gap-1 px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white text-xs rounded-lg disabled:opacity-50"
                          >
                            {agentLoading === `send-${c.id}` ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                            Send
                          </button>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mb-2">Subject: <span className="text-gray-300">{c.subject}</span></p>

                    {/* Content details */}
                    {c.headline && <p className="text-xs text-gray-500 mb-1">Headline: <span className="text-gray-300">{c.headline}</span></p>}
                    {c.body_html && (
                      <div className="mt-2 mb-2 bg-gray-800/50 border border-gray-700/50 rounded-lg p-3">
                        <p className="text-xs text-gray-500 mb-1 font-medium">Content:</p>
                        <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{c.body_html}</p>
                      </div>
                    )}
                    {c.cta_text && <p className="text-xs text-gray-500 mb-1">CTA: <span className="text-purple-400">{c.cta_text}</span> → <span className="text-gray-400 font-mono text-[11px]">{c.cta_url}</span></p>}

                    <div className="flex items-center gap-4 text-xs text-gray-600 mt-2">
                      <span>Target: {c.target}</span>
                      {c.sent_count > 0 && <span className="text-green-500">{c.sent_count} sent</span>}
                      {c.failed_count > 0 && <span className="text-red-500">{c.failed_count} failed</span>}
                      <span>{c.created_at ? new Date(c.created_at).toLocaleDateString() : ''}</span>
                    </div>
                    {c.ai_rationale && <p className="text-xs text-gray-600 mt-2 italic">{c.ai_rationale}</p>}
                  </div>

                  {/* Rendered email preview */}
                  {isExpanded && (
                    <div className="border-t border-gray-800">
                      <div className="px-4 py-2 bg-gray-800/30 flex items-center gap-2">
                        <Eye className="w-3 h-3 text-purple-400" />
                        <span className="text-xs text-purple-400 font-medium">Rendered Email Preview</span>
                      </div>
                      {campaignPreviewHtml ? (
                        <div className="bg-white">
                          <iframe
                            srcDoc={campaignPreviewHtml}
                            className="w-full border-0"
                            style={{ minHeight: '500px' }}
                            title="Campaign Preview"
                          />
                        </div>
                      ) : (
                        <div className="flex items-center justify-center py-8">
                          <Loader2 className="w-5 h-5 animate-spin text-gray-600" />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
            {campaigns.length === 0 && (
              <div className="text-center py-12 text-gray-600">No campaigns yet. Use the Agent tab to generate one.</div>
            )}
          </div>
        </div>
      )}

      {/* Logs */}
      {tab === 'logs' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Filter className="w-4 h-4 text-gray-500" />
            <select value={filterChannel} onChange={e => setFilterChannel(e.target.value)}
              className="bg-gray-900 border border-gray-700 text-white text-sm rounded-lg px-3 py-1.5">
              <option value="">All channels</option>
              <option value="transactional">Transactional</option>
              <option value="marketing">Marketing</option>
            </select>
            <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
              className="bg-gray-900 border border-gray-700 text-white text-sm rounded-lg px-3 py-1.5">
              <option value="">All statuses</option>
              <option value="sent">Sent</option>
              <option value="failed">Failed</option>
            </select>
            <button onClick={fetchLogs} className="p-2 text-gray-400 hover:text-white">
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <span className="text-xs text-gray-500 ml-auto">{logsTotal} total</span>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase">
                  <th className="px-4 py-3 text-left">To</th>
                  <th className="px-4 py-3 text-left">Subject</th>
                  <th className="px-4 py-3 text-left">Template</th>
                  <th className="px-4 py-3 text-left">Channel</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Date</th>
                </tr>
              </thead>
              <tbody>
                {logs.map(log => (
                  <tr key={log.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="px-4 py-3 text-white font-mono text-xs">{log.to_email}</td>
                    <td className="px-4 py-3 text-gray-300 max-w-[200px] truncate">{log.subject}</td>
                    <td className="px-4 py-3"><span className="px-2 py-0.5 text-xs bg-gray-800 text-gray-400 rounded">{log.template || '—'}</span></td>
                    <td className="px-4 py-3"><span className={`px-2 py-0.5 text-xs rounded ${log.channel === 'marketing' ? 'bg-amber-500/20 text-amber-400' : 'bg-cyan-500/20 text-cyan-400'}`}>{log.channel}</span></td>
                    <td className="px-4 py-3">{log.status === 'sent' ? <span className="flex items-center gap-1 text-green-400 text-xs"><CheckCircle className="w-3 h-3" />Sent</span> : <span className="flex items-center gap-1 text-red-400 text-xs" title={log.error}><XCircle className="w-3 h-3" />Failed</span>}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{log.created_at ? new Date(log.created_at).toLocaleString() : '—'}</td>
                  </tr>
                ))}
                {logs.length === 0 && <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-600">No email logs yet</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Compose */}
      {tab === 'compose' && (
        <div className="max-w-2xl space-y-5">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
            <h3 className="text-white font-semibold text-sm">Manual Campaign</h3>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Template (optional)</label>
              <select value={composeTemplate} onChange={e => setComposeTemplate(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white text-sm rounded-lg px-3 py-2">
                <option value="">Custom (no template)</option>
                {templates.filter(t => t.channel === 'marketing').map(t => (
                  <option key={t.name} value={t.name}>{t.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Subject</label>
              <input type="text" value={composeSubject} onChange={e => setComposeSubject(e.target.value)}
                placeholder="Email subject..." className="w-full bg-gray-800 border border-gray-700 text-white text-sm rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Body (HTML)</label>
              <textarea value={composeBody} onChange={e => setComposeBody(e.target.value)} placeholder="<p>Your content...</p>" rows={6}
                className="w-full bg-gray-800 border border-gray-700 text-white text-sm rounded-lg px-3 py-2 font-mono" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Target Audience</label>
              <select value={composeTarget} onChange={e => setComposeTarget(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white text-sm rounded-lg px-3 py-2">
                <option value="all">All Users</option>
                <option value="free">Free Plan</option>
                <option value="starter">Starter Plan</option>
                <option value="pro">Pro Plan</option>
                <option value="lab">Lab Plan</option>
                <option value="active">Active (last 7 days)</option>
                <option value="inactive">Inactive (7+ days)</option>
              </select>
            </div>
            <div className="flex items-center gap-3 pt-2">
              <button onClick={sendEmail} disabled={sending || (!composeTemplate && (!composeSubject || !composeBody))}
                className="flex items-center gap-2 px-5 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg">
                {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Send
              </button>
              {sendResult && !sendResult.error && <span className="text-sm text-green-400">Sent to {sendResult.sent}/{sendResult.total_recipients}</span>}
              {sendResult?.error && <span className="text-sm text-red-400 flex items-center gap-1"><AlertTriangle className="w-4 h-4" />{sendResult.error}</span>}
            </div>
          </div>
        </div>
      )}

      {/* Templates */}
      {tab === 'templates' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map(t => (
              <div key={t.name}
                className={`bg-gray-900 border rounded-xl p-5 cursor-pointer hover:border-gray-600 transition-colors ${previewName === t.name ? 'border-purple-500' : 'border-gray-800'}`}
                onClick={() => previewTemplate(t.name)}
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-white font-medium text-sm">{t.name}</h4>
                  <span className={`px-2 py-0.5 text-xs rounded ${t.channel === 'marketing' ? 'bg-amber-500/20 text-amber-400' : 'bg-cyan-500/20 text-cyan-400'}`}>{t.channel}</span>
                </div>
                <p className="text-xs text-gray-500">Click to preview</p>
              </div>
            ))}
          </div>
          {previewHtml && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
                <div className="flex items-center gap-2">
                  <Eye className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-white font-medium">Preview: {previewName}</span>
                </div>
                <button onClick={() => { setPreviewHtml(''); setPreviewName(''); }} className="text-gray-500 hover:text-white text-xs">Close</button>
              </div>
              <div className="bg-white rounded-b-xl">
                <iframe srcDoc={previewHtml} className="w-full border-0" style={{ minHeight: '500px' }} title="Email Preview" />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
