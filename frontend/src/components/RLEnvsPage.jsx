import React, { useState, useEffect } from 'react';
import {
  Joystick, Sparkles, RefreshCw, Trash2, ChevronDown, ChevronUp,
  Globe, Eye, Trophy, Cpu, Plus, CheckCircle, Clock, Code
} from 'lucide-react';
import {
  getRLEnvironments, generateRLEnvironment, createRLEnvironment,
  updateRLEnvironment, publishRLEnvironment, unpublishRLEnvironment,
  deleteRLEnvironment
} from '../api';

const CATEGORIES = ['robotics', 'locomotion', 'manipulation', 'navigation', 'custom'];
const DIFFICULTIES = ['easy', 'medium', 'hard', 'expert'];

const diffColors = {
  easy: 'text-green-400 bg-green-500/10',
  medium: 'text-yellow-400 bg-yellow-500/10',
  hard: 'text-orange-400 bg-orange-500/10',
  expert: 'text-red-400 bg-red-500/10',
};

export default function RLEnvsPage() {
  const [envs, setEnvs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [showCreate, setShowCreate] = useState(false);

  const [genTopic, setGenTopic] = useState('');
  const [genCategory, setGenCategory] = useState('custom');
  const [genDifficulty, setGenDifficulty] = useState('medium');

  useEffect(() => { loadEnvs(); }, []);

  const loadEnvs = async () => {
    try {
      const res = await getRLEnvironments();
      setEnvs(res.data);
    } catch (err) {
      console.error('Failed to load RL environments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!genTopic.trim()) return alert('Enter a topic or task description.');
    setGenerating(true);
    try {
      await generateRLEnvironment({ topic: genTopic, category: genCategory, difficulty: genDifficulty });
      setGenTopic('');
      await loadEnvs();
    } catch (err) {
      alert('Generation failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGenerating(false);
    }
  };

  const handlePublish = async (id, isPublished) => {
    try {
      if (isPublished) {
        await unpublishRLEnvironment(id);
      } else {
        await publishRLEnvironment(id);
      }
      await loadEnvs();
    } catch (err) {
      alert('Failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this environment?')) return;
    try {
      await deleteRLEnvironment(id);
      await loadEnvs();
    } catch (err) {
      alert('Delete failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const published = envs.filter(e => e.status === 'published').length;
  const drafts = envs.filter(e => e.status === 'draft').length;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">RL Environments</h2>
        <p className="text-gray-400 text-sm mt-1">
          Design and manage reinforcement learning environments. Published environments appear on kualia.ai.
        </p>
      </div>

      {/* Generate */}
      <div className="card space-y-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-400" />
          Generate RL Environment
        </h3>
        <div className="space-y-3">
          <textarea
            value={genTopic}
            onChange={(e) => setGenTopic(e.target.value)}
            placeholder="Describe the task or environment you want, e.g. 'A bipedal robot learning to walk on uneven terrain with wind disturbances'"
            className="input-field resize-none h-20 text-sm"
          />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <select value={genCategory} onChange={(e) => setGenCategory(e.target.value)} className="select-field">
              {CATEGORIES.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
            </select>
            <select value={genDifficulty} onChange={(e) => setGenDifficulty(e.target.value)} className="select-field">
              {DIFFICULTIES.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
            </select>
            <button
              onClick={handleGenerate}
              disabled={generating || !genTopic.trim()}
              className="btn-primary justify-center md:col-span-2"
            >
              {generating ? (
                <><RefreshCw className="w-4 h-4 animate-spin" /> Generating...</>
              ) : (
                <><Sparkles className="w-4 h-4" /> Generate Environment</>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-400">
          {envs.length} total &middot; {published} published &middot; {drafts} drafts
        </span>
      </div>

      {/* List */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : envs.length > 0 ? (
        <div className="space-y-4">
          {envs.map((env) => (
            <div key={env.id} className="card hover:border-gray-700 transition-all">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center flex-shrink-0">
                  <Joystick className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="text-white font-semibold">{env.name}</h4>
                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">
                      {env.category}
                    </span>
                    <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded ${diffColors[env.difficulty] || 'text-gray-400 bg-gray-800'}`}>
                      {env.difficulty}
                    </span>
                    {env.status === 'published' ? (
                      <span className="badge-success flex items-center gap-1 text-xs">
                        <Globe className="w-3 h-3" /> Live
                      </span>
                    ) : (
                      <span className="badge-warning flex items-center gap-1 text-xs">
                        <Clock className="w-3 h-3" /> Draft
                      </span>
                    )}
                  </div>
                  {env.description && (
                    <p className="text-sm text-gray-400 mt-1 line-clamp-2">{env.description}</p>
                  )}
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-600">
                    {env.observation_space && <span><Eye className="w-3 h-3 inline mr-1" />Obs: {env.observation_space.substring(0, 40)}</span>}
                    {env.action_space && <span><Joystick className="w-3 h-3 inline mr-1" />Act: {env.action_space.substring(0, 40)}</span>}
                  </div>
                  {env.topic && (
                    <p className="text-xs text-gray-600 mt-1">Topic: {env.topic}</p>
                  )}
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {env.status === 'published' ? (
                    <button onClick={() => handlePublish(env.id, true)} className="btn-secondary text-sm py-1.5 px-3" title="Unpublish">
                      <Clock className="w-4 h-4" />
                    </button>
                  ) : (
                    <button onClick={() => handlePublish(env.id, false)} className="btn-primary text-sm py-1.5 px-3" title="Publish to kualia.ai">
                      <Globe className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => setExpandedId(expandedId === env.id ? null : env.id)}
                    className="btn-secondary text-sm py-1.5 px-3"
                  >
                    {expandedId === env.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                  <button onClick={() => handleDelete(env.id)} className="btn-danger text-sm py-1.5 px-3">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {expandedId === env.id && (
                <div className="mt-4 pt-4 border-t border-gray-800 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <SpecBox icon={<Eye className="w-4 h-4" />} label="Observation Space" value={env.observation_space} />
                    <SpecBox icon={<Joystick className="w-4 h-4" />} label="Action Space" value={env.action_space} />
                    <SpecBox icon={<Trophy className="w-4 h-4" />} label="Reward" value={env.reward_description} />
                  </div>
                  {env.code && (
                    <div>
                      <h5 className="text-sm font-semibold text-gray-300 mb-2 flex items-center gap-1">
                        <Code className="w-4 h-4" /> Environment Code
                      </h5>
                      <pre className="bg-gray-900 border border-gray-800 rounded-lg p-4 overflow-x-auto text-xs text-gray-300 font-mono leading-relaxed max-h-96 overflow-y-auto">
                        {env.code}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="card flex items-center justify-center h-48 text-gray-500">
          <div className="text-center">
            <Joystick className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No RL environments yet. Generate one above or create manually.</p>
          </div>
        </div>
      )}
    </div>
  );
}

function SpecBox({ icon, label, value }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
      <div className="flex items-center gap-1.5 text-gray-500 mb-1.5">
        {icon}
        <span className="text-[10px] uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-sm text-gray-300">{value || 'Not specified'}</p>
    </div>
  );
}
