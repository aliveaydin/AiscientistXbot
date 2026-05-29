import React, { useState, useEffect } from 'react';
import {
  Bot, RefreshCw, X, Zap, Shield, Pause, Play, ChevronRight,
  Cpu, Wrench, Clock, Brain, Sliders, Activity
} from 'lucide-react';
import { getAgents, getAgent, updateAgentParam, updateAgentStatus } from '../api';

const STATUS_CONFIG = {
  active: { label: 'Active', color: 'bg-green-500', text: 'text-green-400', bg: 'bg-green-500/10', ring: 'ring-green-500/30' },
  paused: { label: 'Paused', color: 'bg-yellow-500', text: 'text-yellow-400', bg: 'bg-yellow-500/10', ring: 'ring-yellow-500/30' },
  disabled: { label: 'Disabled', color: 'bg-red-500', text: 'text-red-400', bg: 'bg-red-500/10', ring: 'ring-red-500/30' },
};

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await getAgents();
      setAgents(res.data.agents || []);
    } catch (e) {
      console.error('Failed to load agents:', e);
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const openDetail = async (agentId) => {
    setSelected(agentId);
    setDetailLoading(true);
    try {
      const res = await getAgent(agentId);
      setDetailData(res.data);
    } catch (e) {
      console.error(e);
    }
    setDetailLoading(false);
  };

  const closeDetail = () => { setSelected(null); setDetailData(null); };

  const handleParamUpdate = async (agentId, key, value) => {
    try {
      await updateAgentParam(agentId, key, value);
      const res = await getAgent(agentId);
      setDetailData(res.data);
      load();
    } catch (e) {
      alert(`Update failed: ${e.message}`);
    }
  };

  const handleStatusToggle = async (agentId, currentStatus) => {
    const newStatus = currentStatus === 'active' ? 'paused' : 'active';
    try {
      await updateAgentStatus(agentId, newStatus);
      load();
      if (detailData && detailData.id === agentId) {
        setDetailData({ ...detailData, status: newStatus });
      }
    } catch (e) {
      alert(`Status update failed: ${e.message}`);
    }
  };

  if (loading) return <div className="text-center py-20 text-gray-500">Loading agents...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Bot className="w-6 h-6 text-blue-400" /> Agent Fleet
          </h1>
          <p className="text-gray-500 text-sm mt-1">{agents.length} agents powering kualia.ai</p>
        </div>
        <button onClick={load} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map(agent => (
          <AgentCard key={agent.id} agent={agent} onClick={() => openDetail(agent.id)} onToggle={handleStatusToggle} />
        ))}
      </div>

      {/* Detail Modal */}
      {selected && (
        <AgentDetailModal
          agent={detailData}
          loading={detailLoading}
          onClose={closeDetail}
          onParamUpdate={handleParamUpdate}
          onStatusToggle={handleStatusToggle}
        />
      )}
    </div>
  );
}


function AgentCard({ agent, onClick, onToggle }) {
  const sc = STATUS_CONFIG[agent.status] || STATUS_CONFIG.active;

  return (
    <div
      onClick={onClick}
      className="bg-gray-900 border border-gray-800 rounded-2xl p-5 cursor-pointer hover:border-gray-600 transition-all group relative overflow-hidden"
    >
      {/* Status indicator pulse */}
      <div className={`absolute top-4 right-4 w-2.5 h-2.5 rounded-full ${sc.color} ${agent.status === 'active' ? 'animate-pulse' : ''}`} />

      {/* Avatar */}
      <div className="flex items-start gap-4 mb-4">
        <div
          className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl shadow-lg ring-2 ring-offset-2 ring-offset-gray-900"
          style={{ background: `${agent.color}20`, ringColor: `${agent.color}40` }}
        >
          {agent.avatar_emoji}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-bold text-white group-hover:text-blue-400 transition-colors">{agent.name}</h3>
          <p className="text-xs text-gray-500 mt-0.5">{agent.role}</p>
        </div>
      </div>

      {/* Description */}
      <p className="text-xs text-gray-400 mb-4 line-clamp-2 leading-relaxed">{agent.description}</p>

      {/* Skills Preview */}
      <div className="flex flex-wrap gap-1 mb-3">
        {agent.skills.slice(0, 3).map((s, i) => (
          <span key={i} className="text-[10px] bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">{s}</span>
        ))}
        {agent.skills.length > 3 && (
          <span className="text-[10px] text-gray-600">+{agent.skills.length - 3} more</span>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-800">
        <div className="flex items-center gap-2">
          {agent.models.length > 0 && (
            <span className="flex items-center gap-1 text-[10px] text-gray-500">
              <Cpu className="w-3 h-3" /> {agent.models.length} models
            </span>
          )}
          {agent.tools.length > 0 && (
            <span className="flex items-center gap-1 text-[10px] text-gray-500">
              <Wrench className="w-3 h-3" /> {agent.tools.length} tools
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`text-[10px] px-2 py-0.5 rounded-full ${sc.bg} ${sc.text}`}>{sc.label}</span>
          <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-gray-400 transition-colors" />
        </div>
      </div>
    </div>
  );
}


function AgentDetailModal({ agent, loading, onClose, onParamUpdate, onStatusToggle }) {
  const [activeTab, setActiveTab] = useState('overview');

  if (loading || !agent) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
        <div className="text-gray-400">Loading agent profile...</div>
      </div>
    );
  }

  const sc = STATUS_CONFIG[agent.status] || STATUS_CONFIG.active;

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Bot },
    { id: 'skills', label: 'Skills & Tools', icon: Wrench },
    { id: 'config', label: 'Configuration', icon: Sliders },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto shadow-2xl"
        onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="sticky top-0 bg-gray-900 z-10 border-b border-gray-800 p-5">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl shadow-lg"
                style={{ background: `${agent.color}20` }}
              >
                {agent.avatar_emoji}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-white">{agent.name}</h2>
                  <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${sc.bg} ${sc.text}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${sc.color}`} />
                    {sc.label}
                  </div>
                </div>
                <p className="text-sm text-gray-400 mt-0.5">{agent.role}</p>
                {agent.service_file && (
                  <p className="text-[10px] text-gray-600 font-mono mt-1">{agent.service_file}</p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={(e) => { e.stopPropagation(); onStatusToggle(agent.id, agent.status); }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${
                  agent.status === 'active'
                    ? 'bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20'
                    : 'bg-green-500/10 text-green-400 hover:bg-green-500/20'
                }`}
              >
                {agent.status === 'active' ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                {agent.status === 'active' ? 'Pause' : 'Activate'}
              </button>
              <button onClick={onClose} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mt-4">
            {tabs.map(t => (
              <button key={t.id} onClick={() => setActiveTab(t.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTab === t.id ? 'bg-gray-800 text-white' : 'text-gray-500 hover:text-gray-300'
                }`}>
                <t.icon className="w-3.5 h-3.5" /> {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Body */}
        <div className="p-5">
          {activeTab === 'overview' && <OverviewPanel agent={agent} />}
          {activeTab === 'skills' && <SkillsPanel agent={agent} />}
          {activeTab === 'config' && <ConfigPanel agent={agent} onParamUpdate={onParamUpdate} />}
        </div>
      </div>
    </div>
  );
}


function OverviewPanel({ agent }) {
  return (
    <div className="space-y-5">
      {/* Description */}
      <div className="bg-gray-800/40 rounded-xl p-4">
        <p className="text-sm text-gray-300 leading-relaxed">{agent.description}</p>
      </div>

      {/* Models */}
      {agent.models.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5" /> AI Models
          </h4>
          <div className="flex flex-wrap gap-2">
            {agent.models.map((m, i) => (
              <div key={i} className="flex items-center gap-2 bg-gray-800 rounded-lg px-3 py-2">
                <div className={`w-2 h-2 rounded-full ${i === 0 ? 'bg-green-500' : i === 1 ? 'bg-yellow-500' : 'bg-gray-500'}`} />
                <span className="text-sm text-gray-300">{m}</span>
                {i === 0 && <span className="text-[9px] bg-green-900/30 text-green-400 px-1.5 py-0.5 rounded">Primary</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scheduled Jobs */}
      {agent.scheduled_jobs.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" /> Scheduled Jobs
          </h4>
          <div className="space-y-1.5">
            {agent.scheduled_jobs.map((j, i) => (
              <div key={i} className="flex items-center gap-2 bg-gray-800/50 rounded-lg px-3 py-2">
                <Activity className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-sm text-gray-300">{j}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Prompts */}
      {agent.prompts && Object.keys(agent.prompts).length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Brain className="w-3.5 h-3.5" /> System Prompts
          </h4>
          <div className="space-y-1.5">
            {Object.entries(agent.prompts).map(([key, val]) => (
              <div key={key} className="bg-gray-800/50 rounded-lg px-3 py-2">
                <span className="text-xs text-gray-400 font-mono">{key}</span>
                <p className="text-[11px] text-gray-500 mt-0.5">{val}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


function SkillsPanel({ agent }) {
  return (
    <div className="space-y-5">
      {/* Skills */}
      <div>
        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <Zap className="w-3.5 h-3.5" /> Capabilities
        </h4>
        <div className="grid grid-cols-1 gap-2">
          {agent.skills.map((skill, i) => (
            <div key={i} className="flex items-center gap-3 bg-gray-800/40 rounded-xl px-4 py-3">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center text-lg" style={{ background: `${agent.color}15` }}>
                <Zap className="w-4 h-4" style={{ color: agent.color }} />
              </div>
              <span className="text-sm text-gray-300">{skill}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Tools */}
      <div>
        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <Wrench className="w-3.5 h-3.5" /> Tools & Integrations
        </h4>
        <div className="flex flex-wrap gap-2">
          {agent.tools.map((tool, i) => (
            <div key={i} className="flex items-center gap-2 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2">
              <Shield className="w-3.5 h-3.5 text-gray-500" />
              <span className="text-sm text-gray-300">{tool}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


function ConfigPanel({ agent, onParamUpdate }) {
  const [editValues, setEditValues] = useState({});

  const getValue = (param) => editValues[param.key] !== undefined ? editValues[param.key] : param.value;

  const handleChange = (key, val) => {
    setEditValues(prev => ({ ...prev, [key]: val }));
  };

  const handleSave = (key) => {
    const val = editValues[key];
    if (val !== undefined) {
      onParamUpdate(agent.id, key, val);
      setEditValues(prev => { const n = { ...prev }; delete n[key]; return n; });
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-xs text-gray-500 mb-2">Adjust agent parameters. Changes take effect on next execution cycle.</p>

      {agent.params.map(param => {
        const currentVal = getValue(param);
        const isDirty = editValues[param.key] !== undefined && editValues[param.key] !== param.value;

        return (
          <div key={param.key} className="bg-gray-800/40 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-sm font-medium text-white">{param.label}</label>
              {isDirty && (
                <button onClick={() => handleSave(param.key)}
                  className="text-xs bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded-lg">
                  Save
                </button>
              )}
            </div>
            {param.description && <p className="text-xs text-gray-500 mb-2">{param.description}</p>}

            {param.type === 'toggle' ? (
              <button
                onClick={() => {
                  const newVal = !currentVal;
                  handleChange(param.key, newVal);
                  onParamUpdate(agent.id, param.key, newVal);
                }}
                className={`relative w-12 h-6 rounded-full transition-all ${
                  currentVal ? 'bg-green-500' : 'bg-gray-700'
                }`}
              >
                <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-all ${
                  currentVal ? 'left-[26px]' : 'left-0.5'
                }`} />
              </button>
            ) : param.type === 'number' ? (
              <input
                type="number"
                value={currentVal}
                onChange={e => handleChange(param.key, parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
              />
            ) : param.type === 'select' ? (
              <select
                value={currentVal}
                onChange={e => handleChange(param.key, e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm"
              >
                {param.options?.map(opt => <option key={opt} value={opt}>{opt}</option>)}
              </select>
            ) : (
              <input
                type="text"
                value={currentVal}
                onChange={e => handleChange(param.key, e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
              />
            )}
          </div>
        );
      })}

      {agent.params.length === 0 && (
        <div className="text-center py-8 text-gray-500">No configurable parameters for this agent.</div>
      )}
    </div>
  );
}
