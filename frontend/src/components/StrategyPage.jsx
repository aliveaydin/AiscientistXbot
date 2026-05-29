import React, { useState, useEffect } from 'react';
import {
  Brain, Target, TrendingUp, ArrowUp, ArrowDown, Minus,
  RefreshCw, Users, MessageCircle, Lightbulb,
  Zap, BarChart3, History, CheckCircle2, X,
} from 'lucide-react';
import {
  getActiveStrategy, createStrategy, reviewStrategy,
  getKPIDashboard, getDecisionLog, getStrategyHistory, getGTMReports,
} from '../api';

export default function StrategyPage() {
  const [strategy, setStrategy] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const [reports, setReports] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [tab, setTab] = useState('board');
  const [selectedCard, setSelectedCard] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [stratRes, kpiRes, decRes, repRes, histRes] = await Promise.all([
        getActiveStrategy(),
        getKPIDashboard(),
        getDecisionLog(null, 20),
        getGTMReports(5),
        getStrategyHistory(10),
      ]);
      setStrategy(stratRes.data.active ? stratRes.data.strategy : null);
      setKpis(kpiRes.data);
      setDecisions(decRes.data.decisions || []);
      setReports(repRes.data.reports || []);
      setHistory(histRes.data.strategies || []);
    } catch (e) {
      console.error('Load failed:', e);
    }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const handleCreate = async () => {
    setActing(true);
    try {
      await createStrategy();
      await loadData();
    } catch (e) {
      alert(`Failed: ${e.response?.data?.detail || e.message}`);
    }
    setActing(false);
  };

  const handleReview = async () => {
    setActing(true);
    try {
      await reviewStrategy();
      await loadData();
    } catch (e) {
      alert(`Review failed: ${e.response?.data?.detail || e.message}`);
    }
    setActing(false);
  };

  if (loading) return <div className="text-center py-20 text-gray-500">Loading strategy...</div>;

  if (!strategy && history.length === 0) {
    return (
      <div className="max-w-xl mx-auto text-center py-20">
        <Brain className="w-16 h-16 text-gray-700 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">No Strategy Yet</h2>
        <p className="text-gray-400 mb-6">
          The GTM agent needs a strategy to operate autonomously. It will analyze your platform,
          define a mission, set KPIs, plan content, and start making decisions on its own.
        </p>
        <button onClick={handleCreate} disabled={acting}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium disabled:opacity-50 flex items-center gap-2 mx-auto">
          {acting ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Brain className="w-5 h-5" />}
          Create First Strategy
        </button>
      </div>
    );
  }

  const tabs = [
    { id: 'board', label: 'Board', icon: Brain },
    { id: 'kpis', label: 'KPIs', icon: Target },
    { id: 'decisions', label: 'Decisions', icon: Lightbulb },
    { id: 'reports', label: 'Reviews', icon: BarChart3 },
  ];

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Brain className="w-6 h-6 text-blue-400" /> GTM Strategy
          </h1>
          {strategy && <p className="text-gray-500 text-sm mt-1">{strategy.mission}</p>}
        </div>
        <div className="flex gap-2">
          <button onClick={handleReview} disabled={acting}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm font-medium disabled:opacity-50">
            {acting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <BarChart3 className="w-4 h-4" />}
            Review & Adjust
          </button>
          <button onClick={handleCreate} disabled={acting}
            className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm font-medium disabled:opacity-50">
            <Zap className="w-4 h-4" /> New Strategy
          </button>
          <button onClick={loadData} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-5 border-b border-gray-800 pb-1">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-t-lg text-sm font-medium transition-all ${
              tab === t.id ? 'bg-gray-800 text-white' : 'text-gray-500 hover:text-gray-300'
            }`}>
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      {tab === 'board' ? <KanbanBoard strategies={history} active={strategy} onSelect={setSelectedCard} /> :
       tab === 'kpis' ? <KPITab kpis={kpis} /> :
       tab === 'decisions' ? <DecisionsTab decisions={decisions} /> :
       <ReportsTab reports={reports} />}

      {/* Strategy Detail Modal */}
      {selectedCard && (
        <StrategyModal strategy={selectedCard} onClose={() => setSelectedCard(null)} />
      )}
    </div>
  );
}


// ─────────────────────────────────────
// KANBAN BOARD
// ─────────────────────────────────────

function KanbanBoard({ strategies, active, onSelect }) {
  const columns = [
    { status: 'active', label: 'Active', color: 'border-green-500/40', headerColor: 'text-green-400 bg-green-500/10' },
    { status: 'archived', label: 'Archived', color: 'border-gray-700', headerColor: 'text-gray-400 bg-gray-800' },
  ];

  const grouped = {
    active: strategies.filter(s => s.status === 'active'),
    archived: strategies.filter(s => s.status === 'archived'),
  };

  return (
    <div className="grid grid-cols-2 gap-4 min-h-[400px]">
      {columns.map(col => (
        <div key={col.status} className={`border rounded-xl p-3 ${col.color} bg-gray-900/50`}>
          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider mb-3 ${col.headerColor}`}>
            {col.status === 'active' ? <Zap className="w-3.5 h-3.5" /> : <History className="w-3.5 h-3.5" />}
            {col.label}
            <span className="ml-1 opacity-60">{grouped[col.status]?.length || 0}</span>
          </div>
          <div className="space-y-2">
            {(grouped[col.status] || []).map(s => (
              <StrategyCard key={s.id} strategy={s} isActive={s.status === 'active'} onClick={() => onSelect(s)} />
            ))}
            {(grouped[col.status] || []).length === 0 && (
              <p className="text-xs text-gray-600 text-center py-8">No strategies</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function StrategyCard({ strategy, isActive, onClick }) {
  const contentStrat = strategy.content_strategy || {};
  const kpis = strategy.kpis || [];

  return (
    <div onClick={onClick}
      className={`rounded-lg p-3.5 cursor-pointer transition-all hover:scale-[1.01] ${
        isActive
          ? 'bg-gradient-to-br from-gray-800 to-gray-800/80 border border-green-600/30 hover:border-green-500/50 shadow-lg shadow-green-900/10'
          : 'bg-gray-800/60 border border-gray-700/50 hover:border-gray-600'
      }`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-white">v{strategy.version}</span>
        <span className="text-[10px] text-gray-500">
          {strategy.created_at ? new Date(strategy.created_at).toLocaleDateString() : ''}
        </span>
      </div>
      <p className="text-sm text-gray-200 mb-2 line-clamp-2">{strategy.mission}</p>

      {contentStrat.current_focus && (
        <p className="text-xs text-gray-500 mb-2 line-clamp-1">
          Focus: {contentStrat.current_focus}
        </p>
      )}

      {contentStrat.mix_percent && (
        <div className="flex gap-1 mb-2">
          {Object.entries(contentStrat.mix_percent).map(([type, pct]) => (
            <div key={type} className="flex-1 h-1.5 rounded-full overflow-hidden bg-gray-700">
              <div className={`h-full rounded-full ${
                type === 'educational' ? 'bg-yellow-500' :
                type === 'product' ? 'bg-blue-500' :
                type === 'industry' ? 'bg-green-500' : 'bg-purple-500'
              }`} style={{ width: `${pct}%` }} />
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {kpis.slice(0, 3).map((k, i) => (
            <span key={i} className="text-[10px] bg-gray-700/50 text-gray-500 px-1.5 py-0.5 rounded">
              {(k.name || '').split(' ').slice(0, 2).join(' ')}
            </span>
          ))}
        </div>
        <span className="text-[10px] text-gray-600">Click for details</span>
      </div>
    </div>
  );
}


// ─────────────────────────────────────
// STRATEGY DETAIL MODAL
// ─────────────────────────────────────

function StrategyModal({ strategy, onClose }) {
  const audiences = strategy.target_audiences || [];
  const contentStrat = strategy.content_strategy || {};
  const engStrat = strategy.engagement_strategy || {};
  const weeklyGoals = strategy.weekly_goals || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-3xl max-h-[85vh] overflow-y-auto shadow-2xl"
        onClick={e => e.stopPropagation()}>

        {/* Modal Header */}
        <div className="sticky top-0 bg-gray-900 border-b border-gray-800 p-5 flex items-center justify-between z-10">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-white">Strategy v{strategy.version}</span>
              <span className={`text-xs px-2 py-0.5 rounded ${
                strategy.status === 'active' ? 'bg-green-900/30 text-green-400' : 'bg-gray-800 text-gray-500'
              }`}>{strategy.status}</span>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              Created {strategy.created_at ? new Date(strategy.created_at).toLocaleString() : ''}
            </p>
          </div>
          <button onClick={onClose} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-5">
          {/* Mission */}
          <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border border-blue-800/20 rounded-xl p-4">
            <span className="text-[10px] font-semibold text-blue-400 uppercase tracking-wider">Mission</span>
            <p className="text-base text-white font-medium mt-1">{strategy.mission}</p>
          </div>

          {/* Audiences */}
          {audiences.length > 0 && (
            <Section title="Target Audiences">
              {audiences.map((a, i) => (
                <div key={i} className="flex items-start gap-2 mb-2 last:mb-0">
                  <Users className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                    a.priority === 'high' ? 'text-red-400' : a.priority === 'medium' ? 'text-yellow-400' : 'text-gray-500'
                  }`} />
                  <div>
                    <span className="text-sm text-white">{a.segment}</span>
                    <span className={`ml-2 text-[10px] px-1 py-0.5 rounded ${
                      a.priority === 'high' ? 'bg-red-900/30 text-red-400' : a.priority === 'medium' ? 'bg-yellow-900/30 text-yellow-400' : 'bg-gray-800 text-gray-500'
                    }`}>{a.priority}</span>
                    {a.pain_point && <p className="text-xs text-gray-500 mt-0.5">{a.pain_point}</p>}
                  </div>
                </div>
              ))}
            </Section>
          )}

          {/* Content Strategy */}
          <Section title="Content Strategy">
            {contentStrat.current_focus && (
              <div className="bg-blue-950/20 border border-blue-900/20 rounded-lg p-3 mb-3">
                <span className="text-[10px] text-blue-400 font-semibold uppercase">Current Focus</span>
                <p className="text-sm text-white mt-0.5">{contentStrat.current_focus}</p>
              </div>
            )}
            {contentStrat.mix_percent && (
              <div className="flex gap-2 mb-3">
                {Object.entries(contentStrat.mix_percent).map(([type, pct]) => (
                  <div key={type} className="flex-1 bg-gray-800 rounded-lg p-2 text-center">
                    <div className="text-base font-bold text-white">{pct}%</div>
                    <div className="text-[10px] text-gray-500 capitalize">{type}</div>
                  </div>
                ))}
              </div>
            )}
            {contentStrat.topic_priorities && (
              <div className="flex flex-wrap gap-1">
                {contentStrat.topic_priorities.map((t, i) => (
                  <span key={i} className="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded">{t}</span>
                ))}
              </div>
            )}
            {contentStrat.tone && <p className="text-xs text-gray-500 mt-2">Tone: {contentStrat.tone}</p>}
          </Section>

          {/* Engagement Strategy */}
          <Section title="Engagement Strategy">
            {engStrat.reply_philosophy && <Field label="Reply Philosophy" value={engStrat.reply_philosophy} />}
            {engStrat.like_strategy && <Field label="Like Strategy" value={engStrat.like_strategy} />}
            {engStrat.community_approach && <Field label="Community" value={engStrat.community_approach} />}
            {engStrat.search_queries && (
              <div className="mt-2 flex flex-wrap gap-1">
                {engStrat.search_queries.map((q, i) => (
                  <span key={i} className="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded font-mono">{q}</span>
                ))}
              </div>
            )}
          </Section>

          {/* Weekly Goals */}
          {weeklyGoals.length > 0 && (
            <Section title="Weekly Goals">
              {weeklyGoals.map((g, i) => (
                <div key={i} className="flex items-start gap-1.5 mb-1 last:mb-0">
                  <CheckCircle2 className="w-3.5 h-3.5 text-gray-600 mt-0.5 flex-shrink-0" />
                  <span className="text-xs text-gray-300">{g}</span>
                </div>
              ))}
            </Section>
          )}

          {/* AI Reasoning */}
          {strategy.ai_reasoning && (
            <Section title="AI Reasoning">
              <p className="text-xs text-gray-400 whitespace-pre-line leading-relaxed">{strategy.ai_reasoning}</p>
            </Section>
          )}
        </div>
      </div>
    </div>
  );
}


// ─────────────────────────────────────
// KPI TAB
// ─────────────────────────────────────

function KPITab({ kpis }) {
  if (!kpis || !kpis.strategy_active) {
    return <div className="text-center py-12 text-gray-500">No active strategy.</div>;
  }
  return (
    <div className="space-y-3">
      {(kpis.kpis || []).map((kpi, i) => {
        const pct = kpi.progress_pct || 0;
        const isGood = pct >= 80;
        const isWarn = pct >= 40 && pct < 80;
        return (
          <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-white">{kpi.name}</span>
                <span className={`flex items-center gap-0.5 text-xs ${
                  kpi.trend === 'up' ? 'text-green-400' : kpi.trend === 'down' ? 'text-red-400' : 'text-gray-500'
                }`}>
                  {kpi.trend === 'up' ? <ArrowUp className="w-3 h-3" /> :
                   kpi.trend === 'down' ? <ArrowDown className="w-3 h-3" /> :
                   <Minus className="w-3 h-3" />}
                  {kpi.trend}
                </span>
              </div>
              <div className="text-right">
                <span className={`text-lg font-bold ${isGood ? 'text-green-400' : isWarn ? 'text-yellow-400' : 'text-red-400'}`}>
                  {kpi.actual}
                </span>
                <span className="text-xs text-gray-600"> / {kpi.target} {kpi.unit !== 'count' ? kpi.unit : ''}</span>
              </div>
            </div>
            <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all ${
                isGood ? 'bg-green-500' : isWarn ? 'bg-yellow-500' : 'bg-red-500'
              }`} style={{ width: `${Math.min(pct, 100)}%` }} />
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-xs text-gray-600">{kpi.why}</span>
              <span className={`text-xs font-medium ${isGood ? 'text-green-400' : isWarn ? 'text-yellow-400' : 'text-red-400'}`}>
                {Math.round(pct)}%
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}


// ─────────────────────────────────────
// DECISIONS TAB
// ─────────────────────────────────────

function DecisionsTab({ decisions }) {
  if (!decisions || decisions.length === 0) {
    return <div className="text-center py-12 text-gray-500">No decisions yet.</div>;
  }
  const typeIcons = {
    content_choice: { icon: MessageCircle, color: 'text-blue-400 bg-blue-500/10' },
    engagement_target: { icon: Target, color: 'text-pink-400 bg-pink-500/10' },
    strategy_review: { icon: BarChart3, color: 'text-amber-400 bg-amber-500/10' },
    strategy_created: { icon: Brain, color: 'text-green-400 bg-green-500/10' },
  };
  return (
    <div className="space-y-2">
      {decisions.map(d => {
        const cfg = typeIcons[d.decision_type] || { icon: Lightbulb, color: 'text-gray-400 bg-gray-800' };
        const Icon = cfg.icon;
        let parsed = d.decision;
        try { parsed = JSON.parse(d.decision); } catch {}
        return (
          <div key={d.id} className="bg-gray-900 border border-gray-800 rounded-lg p-3 flex items-start gap-3">
            <div className={`p-1.5 rounded-lg ${cfg.color} flex-shrink-0`}><Icon className="w-4 h-4" /></div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium text-gray-400 uppercase">{d.decision_type.replace(/_/g, ' ')}</span>
                <span className="text-xs text-gray-600">{d.created_at ? new Date(d.created_at).toLocaleString() : ''}</span>
              </div>
              {typeof parsed === 'object' && parsed !== null ? (
                <div className="flex flex-wrap gap-1.5 mb-1">
                  {parsed.content_type && <span className="text-xs bg-blue-900/30 text-blue-400 px-1.5 py-0.5 rounded">{parsed.content_type}</span>}
                  {parsed.specific_topic && <span className="text-xs text-white">{parsed.specific_topic}</span>}
                  {parsed.focus && <span className="text-xs bg-pink-900/30 text-pink-400 px-1.5 py-0.5 rounded">{parsed.focus}</span>}
                </div>
              ) : (
                <p className="text-sm text-white mb-1">{d.decision}</p>
              )}
              {d.reasoning && <p className="text-xs text-gray-500 italic">{d.reasoning}</p>}
            </div>
          </div>
        );
      })}
    </div>
  );
}


// ─────────────────────────────────────
// REPORTS TAB
// ─────────────────────────────────────

function ReportsTab({ reports }) {
  if (!reports || reports.length === 0) {
    return <div className="text-center py-12 text-gray-500">No reviews yet.</div>;
  }
  return (
    <div className="space-y-4">
      {reports.map(r => (
        <div key={r.id} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="p-4 flex items-center justify-between border-b border-gray-800">
            <div className="flex items-center gap-3">
              <div className={`w-11 h-11 rounded-xl flex items-center justify-center font-bold text-base ${
                r.score >= 70 ? 'bg-green-500/20 text-green-400' : r.score >= 40 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'
              }`}>{r.score}</div>
              <div>
                <p className="text-sm font-medium text-white capitalize">{r.report_type}</p>
                <p className="text-xs text-gray-500">{r.period}</p>
              </div>
            </div>
          </div>
          {r.analysis && <div className="p-4 border-b border-gray-800"><p className="text-sm text-gray-300 whitespace-pre-line">{r.analysis}</p></div>}
          {r.recommendations?.length > 0 && (
            <div className="p-4 space-y-1.5">
              {r.recommendations.map((rec, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded mt-0.5 ${
                    rec.priority === 'high' ? 'bg-red-900/30 text-red-400' : rec.priority === 'medium' ? 'bg-yellow-900/30 text-yellow-400' : 'bg-blue-900/30 text-blue-400'
                  }`}>{rec.priority}</span>
                  <span className="text-gray-300">{rec.action || rec.change}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}


// ─────────────────────────────────────
// SHARED
// ─────────────────────────────────────

function Section({ title, children }) {
  return (
    <div className="bg-gray-800/40 border border-gray-800 rounded-xl p-4">
      <h4 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2">{title}</h4>
      {children}
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div className="mb-2 last:mb-0">
      <span className="text-[10px] text-gray-500 font-semibold uppercase">{label}</span>
      <p className="text-xs text-gray-300 mt-0.5">{value}</p>
    </div>
  );
}
