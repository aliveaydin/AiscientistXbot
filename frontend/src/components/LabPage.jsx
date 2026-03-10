import React, { useState, useEffect, useRef } from 'react';
import {
  FlaskConical, Plus, Play, FastForward, Trash2, RefreshCw,
  MessageSquare, User, FileText, ChevronRight, Download, Copy,
  CheckCircle2, Circle, Loader2, AlertCircle, Upload
} from 'lucide-react';
import {
  getLabProjects, createLabProject, getLabProject, runLabPhase,
  runLabAllPhases, getLabChatboard, getLabAgentWork, getLabPaper,
  getLabReferences, uploadLabDoc, deleteLabProject
} from '../api';

const PHASES = ['brainstorm', 'discussion', 'decision', 'methodology', 'experiments', 'writing', 'review'];

const PHASE_LABELS = {
  brainstorm: 'Brainstorm', discussion: 'Discussion', decision: 'Decision',
  methodology: 'Methodology', experiments: 'Experiments', writing: 'Writing', review: 'Review',
};

const AGENTS = {
  aria: { name: 'Prof. Aria', role: 'Principal Investigator', color: '#f59e0b', initials: 'PA' },
  marcus: { name: 'Dr. Marcus', role: 'ML Engineer', color: '#3b82f6', initials: 'DM' },
  elena: { name: 'Dr. Elena', role: 'Academic Writer', color: '#10b981', initials: 'DE' },
};

function PhaseProgress({ currentPhase, status }) {
  const currentIdx = PHASES.indexOf(currentPhase);
  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-2">
      {PHASES.map((phase, idx) => {
        const isCompleted = status === 'completed' || idx < currentIdx;
        const isCurrent = idx === currentIdx && status !== 'completed';
        return (
          <React.Fragment key={phase}>
            <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap ${
              isCompleted ? 'bg-green-500/20 text-green-400' :
              isCurrent ? 'bg-blue-500/20 text-blue-400 border border-blue-500/40' :
              'bg-gray-800/50 text-gray-500'
            }`}>
              {isCompleted ? <CheckCircle2 className="w-3.5 h-3.5" /> :
               isCurrent ? <Loader2 className="w-3.5 h-3.5" /> :
               <Circle className="w-3.5 h-3.5" />}
              {PHASE_LABELS[phase]}
            </div>
            {idx < PHASES.length - 1 && <ChevronRight className="w-3.5 h-3.5 text-gray-600 flex-shrink-0" />}
          </React.Fragment>
        );
      })}
    </div>
  );
}

function ChatMessage({ msg }) {
  const agent = AGENTS[msg.agent_name] || { name: msg.agent_name, color: '#888', initials: '??' };
  return (
    <div className="flex gap-3 py-3">
      <div
        className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
        style={{ backgroundColor: agent.color }}
      >
        {agent.initials}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-sm" style={{ color: agent.color }}>{agent.name}</span>
          <span className="text-xs text-gray-500 bg-gray-800/60 px-1.5 py-0.5 rounded">{PHASE_LABELS[msg.phase] || msg.phase} R{msg.round_num}</span>
          <span className="text-xs text-gray-600">{new Date(msg.created_at).toLocaleTimeString()}</span>
        </div>
        <div className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">{msg.content}</div>
      </div>
    </div>
  );
}

function WorkItem({ work }) {
  const [expanded, setExpanded] = useState(false);
  const meta = work.metadata_json ? JSON.parse(work.metadata_json) : null;
  const figures = meta?.figures || [];

  return (
    <div className="border border-gray-800 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-medium">{work.work_type}</span>
          <span className="text-sm text-white font-medium">{work.title}</span>
        </div>
        <ChevronRight className={`w-4 h-4 text-gray-500 transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>
      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-800">
          <pre className="text-sm text-gray-300 whitespace-pre-wrap mt-3 leading-relaxed max-h-96 overflow-y-auto">{work.content}</pre>
          {figures.length > 0 && (
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
              {figures.map((fig, i) => (
                <div key={i} className="border border-gray-700 rounded-lg overflow-hidden bg-white p-2">
                  <img src={`data:image/png;base64,${fig.data}`} alt={fig.filename} className="w-full" />
                  <p className="text-xs text-gray-500 mt-1 text-center">{fig.filename}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PaperView({ paper }) {
  if (!paper) return <div className="text-gray-500 text-center py-12">Paper not generated yet. Complete the Writing phase first.</div>;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(paper.content);
    alert('Paper copied to clipboard (Markdown)');
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-white">{paper.title}</h3>
          <div className="flex items-center gap-2 mt-1">
            <span className={`text-xs px-2 py-0.5 rounded font-medium ${
              paper.status === 'final' ? 'bg-green-500/20 text-green-400' :
              paper.status === 'revision' ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-gray-500/20 text-gray-400'
            }`}>{paper.status} v{paper.version}</span>
          </div>
        </div>
        <button onClick={copyToClipboard} className="btn-secondary text-sm py-1.5 px-3">
          <Copy className="w-4 h-4" /> Copy Markdown
        </button>
      </div>
      {paper.abstract && (
        <div className="bg-gray-800/50 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-400 mb-2">Abstract</h4>
          <p className="text-sm text-gray-300 leading-relaxed">{paper.abstract}</p>
        </div>
      )}
      <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-5">
        <pre className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed max-h-[600px] overflow-y-auto">{paper.content}</pre>
      </div>
    </div>
  );
}

export default function LabPage() {
  const [projects, setProjects] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [project, setProject] = useState(null);
  const [activeTab, setActiveTab] = useState('board');
  const [chatboard, setChatboard] = useState([]);
  const [agentWork, setAgentWork] = useState([]);
  const [paper, setPaper] = useState(null);
  const [references, setReferences] = useState([]);
  const [loading, setLoading] = useState(true);
  const [phaseRunning, setPhaseRunning] = useState(false);
  const [allRunning, setAllRunning] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newTopic, setNewTopic] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [uploading, setUploading] = useState(false);
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => { loadProjects(); }, []);
  useEffect(() => { if (selectedId) loadProjectData(); }, [selectedId, activeTab]);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatboard]);

  const loadProjects = async () => {
    try {
      const res = await getLabProjects();
      setProjects(res.data);
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadProjectData = async () => {
    if (!selectedId) return;
    try {
      const projRes = await getLabProject(selectedId);
      setProject(projRes.data);

      if (activeTab === 'board') {
        const chatRes = await getLabChatboard(selectedId);
        setChatboard(chatRes.data);
      } else if (activeTab === 'paper') {
        try {
          const paperRes = await getLabPaper(selectedId);
          setPaper(paperRes.data);
        } catch { setPaper(null); }
      } else if (activeTab === 'refs') {
        const refsRes = await getLabReferences(selectedId);
        setReferences(refsRes.data);
      } else if (['aria', 'marcus', 'elena'].includes(activeTab)) {
        const workRes = await getLabAgentWork(selectedId, activeTab);
        setAgentWork(workRes.data);
      }
    } catch (err) {
      console.error('Failed to load project data:', err);
    }
  };

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      const res = await createLabProject({
        title: newTitle,
        description: newDesc || null,
        topic: newTopic || null,
      });
      setProjects([res.data, ...projects]);
      setSelectedId(res.data.id);
      setNewTitle('');
      setNewDesc('');
      setNewTopic('');
      setShowCreate(false);
    } catch (err) {
      alert('Failed to create project: ' + (err.response?.data?.detail || err.message));
    } finally {
      setCreating(false);
    }
  };

  const handleRunPhase = async () => {
    if (!selectedId) return;
    setPhaseRunning(true);
    try {
      await runLabPhase(selectedId);
      await loadProjectData();
      await loadProjects();
      setActiveTab('board');
    } catch (err) {
      alert('Phase failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setPhaseRunning(false);
    }
  };

  const handleRunAll = async () => {
    if (!selectedId) return;
    if (!confirm('Run all remaining phases? This may take several minutes.')) return;
    setAllRunning(true);
    try {
      await runLabAllPhases(selectedId);
      alert('All phases started in background. Refresh periodically to see progress.');
    } catch (err) {
      alert('Failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setAllRunning(false);
    }
  };

  const handleUploadDoc = async (e) => {
    const files = e.target.files;
    if (!files.length || !selectedId) return;
    setUploading(true);
    try {
      for (const file of files) {
        await uploadLabDoc(selectedId, file);
      }
      await loadProjectData();
      await loadProjects();
    } catch (err) {
      alert('Upload failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this project and all its data?')) return;
    try {
      await deleteLabProject(id);
      setProjects(projects.filter(p => p.id !== id));
      if (selectedId === id) { setSelectedId(null); setProject(null); }
    } catch (err) {
      alert('Failed to delete: ' + (err.response?.data?.detail || err.message));
    }
  };

  const tabs = [
    { id: 'board', label: 'Chatboard', icon: MessageSquare },
    { id: 'refs', label: `References${project?.reference_count ? ` (${project.reference_count})` : ''}`, icon: FileText },
    { id: 'aria', label: 'Prof. Aria', color: AGENTS.aria.color },
    { id: 'marcus', label: 'Dr. Marcus', color: AGENTS.marcus.color },
    { id: 'elena', label: 'Dr. Elena', color: AGENTS.elena.color },
    { id: 'paper', label: 'Paper', icon: FileText },
  ];

  return (
    <div className="flex gap-6 h-[calc(100vh-4rem)]">
      {/* Sidebar - Projects */}
      <div className="w-72 flex-shrink-0 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-purple-400" /> Research Lab
          </h2>
          <button onClick={() => setShowCreate(!showCreate)} className="btn-primary text-sm py-1.5 px-2.5">
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {showCreate && (
          <div className="card mb-4 space-y-3">
            <input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Project title..."
              className="input-field text-sm"
            />
            <textarea
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              placeholder="Description (optional)..."
              className="input-field text-sm resize-none h-16"
            />
            <textarea
              value={newTopic}
              onChange={(e) => setNewTopic(e.target.value)}
              placeholder="Research topic (optional). Can be keywords, a description, or even an abstract. ArXiv will be searched for related papers."
              className="input-field text-sm resize-none h-16"
            />
            {newTopic && (
              <p className="text-xs text-cyan-400">Topic specified: ArXiv'dan 10+ ilgili paper aranacak.</p>
            )}
            <button onClick={handleCreate} disabled={creating} className="btn-primary w-full text-sm justify-center">
              {creating ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Creating &amp; Searching Papers...</>
              ) : (
                <><FlaskConical className="w-4 h-4" /> Create Project</>
              )}
            </button>
          </div>
        )}

        <div className="flex-1 overflow-y-auto space-y-2">
          {loading ? (
            <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-gray-500" /></div>
          ) : projects.length === 0 ? (
            <p className="text-gray-500 text-sm text-center py-8">No projects yet</p>
          ) : (
            projects.map((p) => (
              <div
                key={p.id}
                onClick={() => { setSelectedId(p.id); setActiveTab('board'); }}
                className={`p-3 rounded-lg cursor-pointer transition-all border ${
                  selectedId === p.id
                    ? 'bg-purple-500/10 border-purple-500/40 text-white'
                    : 'bg-gray-900/50 border-gray-800 text-gray-400 hover:border-gray-700 hover:text-gray-300'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="font-medium text-sm truncate">{p.title}</p>
                    {p.topic && <p className="text-xs text-cyan-400/70 truncate mt-0.5">{p.topic}</p>}
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        p.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                        p.status === 'paused' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-blue-500/20 text-blue-400'
                      }`}>{p.status}</span>
                      <span className="text-xs text-gray-500">{PHASE_LABELS[p.current_phase]}</span>
                      {p.reference_count > 0 && (
                        <span className="text-xs text-gray-500">{p.reference_count} refs</span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(p.id); }}
                    className="text-gray-600 hover:text-red-400 p-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {!selectedId || !project ? (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <FlaskConical className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-lg">Select or create a research project</p>
              <p className="text-sm mt-1">Multi-agent AI lab for collaborative research</p>
            </div>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="text-lg font-bold text-white">{project.title}</h3>
                  {project.description && <p className="text-sm text-gray-400 mt-0.5">{project.description}</p>}
                  {project.topic && (
                    <p className="text-xs text-cyan-400 mt-1">Topic: {project.topic}</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleRunPhase}
                    disabled={phaseRunning || project.status === 'completed'}
                    className="btn-primary text-sm py-1.5 px-3"
                  >
                    {phaseRunning ? (
                      <><Loader2 className="w-4 h-4 animate-spin" /> Running {PHASE_LABELS[project.current_phase]}...</>
                    ) : project.status === 'completed' ? (
                      <><CheckCircle2 className="w-4 h-4" /> Completed</>
                    ) : (
                      <><Play className="w-4 h-4" /> Run: {PHASE_LABELS[project.current_phase]}</>
                    )}
                  </button>
                  <button
                    onClick={handleRunAll}
                    disabled={allRunning || project.status === 'completed'}
                    className="btn-secondary text-sm py-1.5 px-3"
                  >
                    {allRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <FastForward className="w-4 h-4" />}
                    Run All
                  </button>
                  <button onClick={loadProjectData} className="btn-secondary text-sm py-1.5 px-2.5">
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <PhaseProgress currentPhase={project.current_phase} status={project.status} />
            </div>

            {/* Tabs */}
            <div className="flex items-center gap-1 border-b border-gray-800 mb-4">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-all ${
                    activeTab === tab.id
                      ? 'border-purple-500 text-white'
                      : 'border-transparent text-gray-500 hover:text-gray-300'
                  }`}
                >
                  {tab.icon ? <tab.icon className="w-4 h-4" /> : (
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: tab.color }} />
                  )}
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto">
              {activeTab === 'board' && (
                <div className="space-y-0 divide-y divide-gray-800/50">
                  {chatboard.length === 0 ? (
                    <p className="text-gray-500 text-center py-12">No messages yet. Run the Brainstorm phase to start.</p>
                  ) : (
                    chatboard.map((msg) => <ChatMessage key={msg.id} msg={msg} />)
                  )}
                  <div ref={chatEndRef} />
                </div>
              )}

              {activeTab === 'refs' && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 mb-3">
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept=".pdf,.txt,.md,.docx,.doc"
                      onChange={handleUploadDoc}
                      className="hidden"
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploading}
                      className="btn-secondary text-sm py-1.5 px-3"
                    >
                      {uploading ? (
                        <><Loader2 className="w-4 h-4 animate-spin" /> Uploading...</>
                      ) : (
                        <><Upload className="w-4 h-4" /> Upload Document</>
                      )}
                    </button>
                    <span className="text-xs text-gray-500">{references.length} reference(s)</span>
                  </div>
                  {references.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No reference papers linked yet. Upload documents or specify a topic.</p>
                  ) : (
                    references.map((ref) => (
                      <div key={ref.id} className="flex items-center justify-between p-3 bg-gray-900/50 border border-gray-800 rounded-lg">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm text-white font-medium truncate">{ref.article_title}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={`text-xs px-1.5 py-0.5 rounded ${
                              ref.article_source === 'arxiv' ? 'bg-orange-500/20 text-orange-400' : 'bg-gray-500/20 text-gray-400'
                            }`}>{ref.article_source}</span>
                          </div>
                        </div>
                        {ref.arxiv_url && (
                          <a href={ref.arxiv_url} target="_blank" rel="noreferrer" className="text-xs text-blue-400 hover:underline ml-3 flex-shrink-0">
                            ArXiv
                          </a>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {['aria', 'marcus', 'elena'].includes(activeTab) && (
                <div className="space-y-3">
                  <div className="flex items-center gap-3 mb-4">
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white"
                      style={{ backgroundColor: AGENTS[activeTab].color }}
                    >
                      {AGENTS[activeTab].initials}
                    </div>
                    <div>
                      <p className="font-semibold text-white">{AGENTS[activeTab].name}</p>
                      <p className="text-xs text-gray-400">{AGENTS[activeTab].role}</p>
                    </div>
                  </div>
                  {agentWork.length === 0 ? (
                    <p className="text-gray-500 text-center py-12">No work items yet for this agent.</p>
                  ) : (
                    agentWork.map((w) => <WorkItem key={w.id} work={w} />)
                  )}
                </div>
              )}

              {activeTab === 'paper' && <PaperView paper={paper} />}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
