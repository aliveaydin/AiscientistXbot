"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import {
  ArrowLeft, Send, Loader2, CheckCircle, XCircle,
  Download, RotateCcw, ChevronDown, Play, Pause,
  Activity, Code2, Cpu, Eye, Zap,
  Target, Layers, Settings2, Bot,
  Clock, FileText, RefreshCw, BarChart3, FileDown,
  FlaskConical, GitBranch,
} from "lucide-react";
import {
  getEnvById, getBuilderHistory, getEnvVersions,
  builderChat, builderRollback, exportZip,
  startTraining, getTrainingStatus, getTrainingCurve,
  getTrainingReplay, getTrainingHistory, getTrainingReport,
} from "@/lib/api";

interface Message { id: number; role: string; content: string; version_snapshot: number | null; created_at: string | null; }
type RightTab = "dashboard" | "code" | "agent" | "history" | "docs";

export default function BuilderPage() {
  const { id } = useParams();
  const { getToken } = useAuth();
  const envId = Number(id);
  const [env, setEnv] = useState<any>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showVersions, setShowVersions] = useState(false);
  const [versions, setVersions] = useState<any[]>([]);
  const [rightTab, setRightTab] = useState<RightTab>("dashboard");
  const [trainStatus, setTrainStatus] = useState<any>(null);
  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => { fetchEnv(); fetchHistory(); fetchVersions(); checkTraining(); }, [envId]);
  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function fetchEnv() { try { setEnv(await getEnvById(envId)); } catch {} }
  async function fetchHistory() { try { setMessages(await getBuilderHistory(envId)); } catch {} }
  async function fetchVersions() { try { setVersions(await getEnvVersions(envId)); } catch {} }
  async function checkTraining() { try { setTrainStatus(await getTrainingStatus(envId)); } catch {} }

  async function sendMessage() {
    if (!input.trim() || loading) return;
    const msg = input.trim(); setInput(""); setLoading(true);
    setMessages(p => [...p, { id: Date.now(), role: "user", content: msg, version_snapshot: null, created_at: new Date().toISOString() }]);
    try {
      const token = await getToken();
      const data = await builderChat(envId, msg, token);
      const isQuestion = data.mode === "question";
      setMessages(p => [...p, { id: Date.now()+1, role: "assistant", content: JSON.stringify({ mode: data.mode, change_summary: data.change_summary, breaking_changes: data.breaking_changes, test_results: data.test_results }), version_snapshot: data.version, created_at: new Date().toISOString() }]);
      if (!isQuestion) { await fetchEnv(); await fetchVersions(); }
    } catch (e: any) {
      setMessages(p => [...p, { id: Date.now()+1, role: "system", content: `Error: ${e.message}`, version_snapshot: null, created_at: new Date().toISOString() }]);
    } finally { setLoading(false); }
  }

  async function handleRollback(v: number) { try { await builderRollback(envId, v); await fetchEnv(); await fetchHistory(); await fetchVersions(); } catch {} }
  async function handleExportZip() {
    try { const b = await exportZip(envId); const u = URL.createObjectURL(b); const a = document.createElement("a"); a.href = u; a.download = `${env?.slug||"env"}.zip`; a.click(); URL.revokeObjectURL(u); } catch {}
  }

  function renderAssistantContent(content: string) {
    try {
      const d = JSON.parse(content);
      if (d.mode === "question") {
        return <p className="text-sm text-[#bbb] leading-relaxed">{d.change_summary}</p>;
      }
      return (<div className="space-y-2"><p className="text-sm">{d.change_summary}</p>
        {d.breaking_changes?.length > 0 && <div className="text-xs text-orange-400 border border-orange-900 rounded p-2">Breaking: {d.breaking_changes.join(", ")}</div>}
        {d.test_results && <div className="flex flex-wrap gap-1">{d.test_results.tests?.map((t:any)=>(<span key={t.name} className={`text-[10px] px-1.5 py-0.5 rounded ${t.status==="pass"?"bg-green-950 text-green-400":"bg-red-950 text-red-400"}`}>{t.name}</span>))}</div>}
      </div>);
    } catch { return <p className="text-sm">{content}</p>; }
  }

  const isTraining = trainStatus?.status === "running";
  const hasCompletedTraining = trainStatus?.status === "completed";

  const TABS: { key: RightTab; icon: any; label: string }[] = [
    { key: "dashboard", icon: Activity, label: "Dashboard" },
    { key: "code", icon: Code2, label: "Code" },
    { key: "agent", icon: Bot, label: "Agent" },
    { key: "history", icon: Clock, label: "History" },
    { key: "docs", icon: FileText, label: "Docs" },
  ];

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      {/* Top bar */}
      <div className="border-b border-[#1a1a1a] px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="text-[#555] hover:text-white"><ArrowLeft size={16} /></Link>
          <span className="font-semibold">{env?.name || "Loading..."}</span>
          <span className="text-xs text-[#555] font-mono">v{env?.version || 1}</span>
          {env?.domain && <span className="text-[10px] px-2 py-0.5 bg-[#1a1a1a] rounded-full text-[#888]">{env.domain}</span>}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleExportZip} className="flex items-center gap-1 px-3 py-1.5 text-xs border border-[#1a1a1a] rounded hover:border-[#333] transition-colors">
            <Download size={12} /> ZIP
          </button>
          {hasCompletedTraining && (
            <button onClick={() => setRightTab("agent")} className="flex items-center gap-1 px-3 py-1.5 text-xs border border-blue-900 text-blue-400 rounded hover:border-blue-700 transition-colors">
              <RefreshCw size={12} /> Continue Training
            </button>
          )}
          <button
            onClick={() => setRightTab("agent")}
            className={`flex items-center gap-1 px-3 py-1.5 text-xs rounded transition-colors ${
              isTraining ? "bg-blue-900 text-blue-300 animate-pulse" : "bg-white text-black hover:bg-[#e5e5e5]"
            }`}
          >
            {isTraining ? <><Loader2 size={12} className="animate-spin" /> Training...</> : <><Play size={12} /> Train Agent</>}
          </button>
        </div>
      </div>

      {/* Main split */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat */}
        <div className="w-[40%] border-r border-[#1a1a1a] flex flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && <p className="text-[#555] text-sm text-center py-8">Ask questions or describe changes to iterate on your environment.</p>}
            {messages.map(m => (
              <div key={m.id} className={m.role === "user" ? "ml-8" : "mr-8"}>
                <div className={`rounded-lg p-3 text-sm ${m.role === "user" ? "bg-[#1a1a1a] text-white" : m.role === "system" ? "bg-red-950/30 text-red-400" : "bg-[#0a0a0a] border border-[#1a1a1a]"}`}>
                  {m.role === "assistant" ? renderAssistantContent(m.content) : m.content}
                </div>
                {m.version_snapshot && <p className="text-[10px] text-[#555] mt-1">v{m.version_snapshot}</p>}
              </div>
            ))}
            <div ref={chatEnd} />
          </div>
          <div className="border-t border-[#1a1a1a] p-3 flex gap-2">
            <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendMessage()} placeholder="Ask a question or describe changes..." className="flex-1 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-3 py-2 text-sm text-white placeholder:text-[#555] focus:outline-none focus:border-[#333]" disabled={loading} />
            <button onClick={sendMessage} disabled={loading || !input.trim()} className="px-3 py-2 bg-white text-black rounded-lg hover:bg-[#e5e5e5] disabled:opacity-50 transition-colors">
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </div>
        </div>

        {/* Right panel */}
        <div className="w-[60%] flex flex-col overflow-hidden">
          <div className="border-b border-[#1a1a1a] px-4 flex items-center shrink-0 overflow-x-auto">
            {TABS.map(({ key, icon: Icon, label }) => (
              <button key={key} onClick={() => setRightTab(key)}
                className={`flex items-center gap-1.5 px-3 py-2.5 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${rightTab === key ? "border-white text-white" : "border-transparent text-[#555] hover:text-[#888]"}`}>
                <Icon size={12} /> {label}
              </button>
            ))}
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {rightTab === "dashboard" && <DashboardView env={env} spec={env?.env_spec || {}} tests={env?.test_results?.tests || []} />}
            {rightTab === "code" && <CodeView env={env} versions={versions} showVersions={showVersions} setShowVersions={setShowVersions} handleRollback={handleRollback} />}
            {rightTab === "agent" && <AgentView envId={envId} env={env} onStatusChange={setTrainStatus} />}
            {rightTab === "history" && <HistoryView envId={envId} />}
            {rightTab === "docs" && <DocsView env={env} />}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Agent View ──────────────────────────────────

function formatDuration(sec: number): string {
  if (sec < 60) return `${Math.round(sec)}s`;
  if (sec < 3600) return `${Math.floor(sec/60)}m ${Math.round(sec%60)}s`;
  return `${Math.floor(sec/3600)}h ${Math.floor((sec%3600)/60)}m`;
}

function formatSteps(n: number): string {
  if (n >= 1_000_000) return `${(n/1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n/1_000).toFixed(n >= 10_000 ? 0 : 1)}K`;
  return String(n);
}

function AgentView({ envId, env, onStatusChange }: { envId: number; env: any; onStatusChange: (s: any) => void }) {
  const { getToken } = useAuth();
  const [config, setConfig] = useState({ algorithm: "auto", total_timesteps: 10000, learning_rate: "" });
  const [status, setStatus] = useState<any>(null);
  const [curve, setCurve] = useState<any[]>([]);
  const [replay, setReplay] = useState<any[]>([]);
  const [report, setReport] = useState<any>(null);
  const [trainLoading, setTrainLoading] = useState(false);
  const [replayEp, setReplayEp] = useState(0);
  const [replayStep, setReplayStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const playRef = useRef<NodeJS.Timeout | null>(null);
  const reportRef = useRef<HTMLDivElement>(null);

  useEffect(() => { loadExisting(); }, [envId]);

  useEffect(() => {
    if (!status || status.status !== "running") return;
    const iv = setInterval(async () => {
      try {
        const [s, c] = await Promise.all([getTrainingStatus(envId), getTrainingCurve(envId)]);
        setStatus(s); onStatusChange(s); setCurve(c);
        if (s.status !== "running") { clearInterval(iv); loadReplay(); loadReport(s.id); }
      } catch {}
    }, 2000);
    return () => clearInterval(iv);
  }, [status?.status, envId]);

  async function loadExisting() {
    try {
      const s = await getTrainingStatus(envId); setStatus(s); onStatusChange(s);
      const c = await getTrainingCurve(envId); setCurve(c);
      if (s.status === "completed") { loadReplay(); loadReport(s.id); }
    } catch {}
  }
  async function loadReplay() { try { setReplay(await getTrainingReplay(envId)); } catch {} }
  async function loadReport(runId: number) { try { setReport(await getTrainingReport(envId, runId)); } catch {} }

  async function handleStart(isContinue = false) {
    setTrainLoading(true); setReport(null); setShowReport(false);
    try {
      const cfg: any = { total_timesteps: config.total_timesteps };
      if (config.algorithm !== "auto") cfg.algorithm = config.algorithm;
      if (config.learning_rate) cfg.learning_rate = parseFloat(config.learning_rate);
      if (isContinue) cfg.continue_from = true;
      const token = await getToken();
      const r = await startTraining(envId, cfg, token);
      setStatus(r); onStatusChange(r); setCurve([]); setReplay([]);
    } catch (e: any) { setStatus({ status: "failed", error: e.message }); } finally { setTrainLoading(false); }
  }

  function startReplay() {
    setPlaying(true); setReplayStep(0);
    if (playRef.current) clearInterval(playRef.current);
    playRef.current = setInterval(() => {
      setReplayStep(prev => { const ep = replay[replayEp]; if (!ep || prev >= ep.steps.length - 1) { setPlaying(false); clearInterval(playRef.current!); return prev; } return prev + 1; });
    }, 100);
  }
  function stopReplay() { setPlaying(false); if (playRef.current) clearInterval(playRef.current); }

  function exportReportPDF() {
    if (!reportRef.current) return;
    const win = window.open("", "_blank");
    if (!win) return;
    win.document.write(`<!DOCTYPE html><html><head><title>Training Report - Run #${status?.id}</title>
      <style>body{font-family:system-ui,-apple-system,sans-serif;background:#fff;color:#111;padding:40px;max-width:800px;margin:0 auto;font-size:13px}
      h1{font-size:20px;margin-bottom:4px}h2{font-size:15px;margin-top:24px;border-bottom:1px solid #ddd;padding-bottom:4px}
      table{width:100%;border-collapse:collapse;margin:8px 0}td,th{text-align:left;padding:4px 8px;border-bottom:1px solid #eee;font-size:12px}
      th{font-weight:600;color:#666}.metric{display:inline-block;text-align:center;padding:8px 16px;border:1px solid #eee;border-radius:8px;margin:4px}
      .metric .value{font-size:20px;font-weight:700}.metric .label{font-size:10px;color:#888;margin-top:2px}
      .badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600}
      .green{background:#dcfce7;color:#166534}.gray{color:#666}
      @media print{body{padding:20px}}</style></head><body>`);
    win.document.write(reportRef.current.innerHTML);
    win.document.write(`</body></html>`);
    win.document.close();
    setTimeout(() => { win.print(); }, 500);
  }

  const isRunning = status?.status === "running";
  const isCompleted = status?.status === "completed";
  const currentEp = replay[replayEp];

  const totalSteps = status?.total_timesteps || config.total_timesteps;
  const currentSteps = curve.length > 0 ? curve[curve.length-1].step : (status?.progress_steps || 0);
  const progressPct = totalSteps > 0 ? Math.min(100, (currentSteps / totalSteps) * 100) : 0;
  const isEvaluating = curve.length > 0 && curve[curve.length-1].phase === "evaluating";

  return (
    <div className="space-y-6">
      {/* Progress Bar (visible during training) */}
      {isRunning && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-[11px]">
            {isEvaluating ? (
              <span className="text-[#888] flex items-center gap-1.5"><Loader2 size={11} className="animate-spin text-green-400" /> Evaluating trained agent...</span>
            ) : (
              <span className="text-[#888] flex items-center gap-1.5"><Loader2 size={11} className="animate-spin text-blue-400" /> Training in progress</span>
            )}
            <span className="font-mono text-white">{isEvaluating ? "Eval" : `${progressPct.toFixed(1)}%`}</span>
          </div>
          <div className="relative h-2 bg-[#1a1a1a] rounded-full overflow-hidden">
            {isEvaluating ? (
              <div className="absolute inset-0 bg-gradient-to-r from-green-600 via-green-400 to-green-600 rounded-full animate-pulse" />
            ) : (<>
              <div className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-600 to-blue-400 rounded-full transition-all duration-1000 ease-out" style={{ width: `${progressPct}%` }} />
              <div className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-400/30 to-transparent rounded-full animate-pulse" style={{ width: `${Math.min(progressPct + 5, 100)}%` }} />
            </>)}
          </div>
          {!isEvaluating && (
            <div className="flex justify-between text-[10px] text-[#555] font-mono">
              <span>0</span>
              <span>{formatSteps(currentSteps)} / {formatSteps(totalSteps)}</span>
              <span>{formatSteps(totalSteps)}</span>
            </div>
          )}
          {isEvaluating && <p className="text-[10px] text-[#555]">Training complete. Running evaluation episodes and saving results...</p>}
          {!isEvaluating && curve.length > 0 && (
            <div className="flex gap-4 text-[10px] text-[#555]">
              <span>Episodes: {curve[curve.length-1].episodes}</span>
              <span>FPS: {curve[curve.length-1].fps}</span>
              {curve[curve.length-1].elapsed_sec && <span>Elapsed: {formatDuration(curve[curve.length-1].elapsed_sec)}</span>}
              {curve[curve.length-1].fps > 0 && progressPct < 100 && <span>ETA: {formatDuration((totalSteps - currentSteps) / curve[curve.length-1].fps)}</span>}
            </div>
          )}
        </div>
      )}

      {/* Config & Start */}
      <div className="border border-[#1a1a1a] rounded-lg p-4 space-y-4">
        <h3 className="text-sm font-medium flex items-center gap-2"><Cpu size={14} /> Train an Agent</h3>
        <p className="text-[11px] text-[#555]">Platform automatically creates and trains an RL agent using the best algorithm for your environment&apos;s action space.</p>
        <div className="grid grid-cols-3 gap-3">
          <div><label className="text-[10px] text-[#555] block mb-1">Algorithm</label>
            <select value={config.algorithm} onChange={e => setConfig(p => ({...p, algorithm: e.target.value}))} className="w-full bg-[#0a0a0a] border border-[#1a1a1a] rounded px-2 py-1.5 text-xs text-white">
              <option value="auto">Auto-detect</option><option value="PPO">PPO</option><option value="DQN">DQN</option><option value="SAC">SAC</option>
            </select></div>
          <div><label className="text-[10px] text-[#555] block mb-1">Timesteps</label>
            <div className="flex gap-1">
              <select value={[5000,10000,50000,100000,500000,1000000].includes(config.total_timesteps) ? config.total_timesteps : "custom"} onChange={e => { if (e.target.value === "custom") setConfig(p => ({...p, total_timesteps: 25000})); else setConfig(p => ({...p, total_timesteps: Number(e.target.value)})); }} className="flex-1 bg-[#0a0a0a] border border-[#1a1a1a] rounded px-2 py-1.5 text-xs text-white">
                <option value={5000}>5K</option><option value={10000}>10K</option><option value={50000}>50K</option><option value={100000}>100K</option><option value={500000}>500K</option><option value={1000000}>1M</option><option value="custom">Custom</option>
              </select>
              {![5000,10000,50000,100000,500000,1000000].includes(config.total_timesteps) && (
                <input type="number" value={config.total_timesteps} onChange={e => setConfig(p => ({...p, total_timesteps: Math.max(1000, Number(e.target.value))}))} min={1000} step={1000} className="w-20 bg-[#0a0a0a] border border-[#1a1a1a] rounded px-2 py-1.5 text-xs text-white" />
              )}
            </div></div>
          <div><label className="text-[10px] text-[#555] block mb-1">Learning Rate</label>
            <input value={config.learning_rate} onChange={e => setConfig(p => ({...p, learning_rate: e.target.value}))} placeholder="auto" className="w-full bg-[#0a0a0a] border border-[#1a1a1a] rounded px-2 py-1.5 text-xs text-white placeholder:text-[#555]" /></div>
        </div>
        <div className="flex gap-2">
          <button onClick={() => handleStart(false)} disabled={trainLoading || isRunning} className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50 transition-colors">
            {trainLoading || isRunning ? <><Loader2 size={12} className="animate-spin" /> Training...</> : <><Play size={12} /> Start Training</>}
          </button>
          {isCompleted && (
            <button onClick={() => handleStart(true)} disabled={trainLoading} className="flex items-center gap-2 px-4 py-2 border border-blue-800 text-blue-400 text-xs rounded hover:border-blue-600 transition-colors">
              <RefreshCw size={12} /> Continue Training
            </button>
          )}
        </div>
      </div>

      {/* Live Training Charts */}
      {(isRunning || isCompleted) && curve.length > 0 && (
        <div className="border border-[#1a1a1a] rounded-lg p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Training Curves</h3>
            <span className={`text-[10px] px-2 py-0.5 rounded ${isRunning ? "bg-blue-950 text-blue-400 animate-pulse" : "bg-green-950 text-green-400"}`}>{status?.status}</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <MiniChart data={curve} dataKey="mean_reward" label="Episode Reward" color="#22c55e" status={status?.status} />
            <MiniChart data={curve} dataKey="mean_ep_length" label="Episode Length" color="#3b82f6" status={status?.status} />
            <MiniChart data={curve} dataKey="success_rate" label="Success Rate" color="#eab308" format="percent" status={status?.status} />
            <MiniChart data={curve} dataKey="loss" label="Policy Loss" color="#ef4444" status={status?.status} />
          </div>
          {!isRunning && curve.length > 0 && (
            <div className="flex gap-4 text-[10px] text-[#555]">
              <span>Final Step: {curve[curve.length-1].step?.toLocaleString()}</span>
              <span>Episodes: {curve[curve.length-1].episodes}</span>
              {curve[curve.length-1].elapsed_sec && <span>Duration: {formatDuration(curve[curve.length-1].elapsed_sec)}</span>}
            </div>
          )}
        </div>
      )}

      {/* Final Results */}
      {isCompleted && status?.results && (
        <div className="border border-[#1a1a1a] rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Results</h3>
            <div className="flex gap-2">
              <button onClick={() => setShowReport(!showReport)} className="flex items-center gap-1 px-2.5 py-1 text-[10px] border border-[#1a1a1a] rounded hover:border-[#333] transition-colors text-[#888] hover:text-white">
                <BarChart3 size={10} /> {showReport ? "Hide" : "View"} Report
              </button>
              <button onClick={exportReportPDF} className="flex items-center gap-1 px-2.5 py-1 text-[10px] border border-[#1a1a1a] rounded hover:border-[#333] transition-colors text-[#888] hover:text-white">
                <FileDown size={10} /> Export PDF
              </button>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-3">
            <MetricCard label="Mean Reward" value={status.results.mean_reward} color="green" />
            <MetricCard label="Success Rate" value={`${Math.round((status.results.success_rate||0)*100)}%`} color="yellow" />
            <MetricCard label="Avg Length" value={status.results.mean_ep_length} color="blue" />
            <MetricCard label="Train Time" value={formatDuration(status.results.training_time_sec || 0)} color="gray" />
          </div>
          <a href={`${process.env.NEXT_PUBLIC_BACKEND_URL||""}/api/rlforge/train/${envId}/model`} className="inline-flex items-center gap-1 px-3 py-1.5 text-xs bg-white text-black rounded hover:bg-[#e5e5e5] transition-colors">
            <Download size={12} /> Download Model (.zip)
          </a>
        </div>
      )}

      {/* Training Report (expandable) */}
      {showReport && report && (
        <div className="border border-[#1a1a1a] rounded-lg overflow-hidden">
          <div ref={reportRef}>
            <TrainingReportView report={report} curve={curve} envName={env?.name} />
          </div>
        </div>
      )}

      {/* Error */}
      {status?.status === "failed" && (
        <div className="border border-red-900 rounded-lg p-4">
          <p className="text-xs text-red-400">{status.results?.error || status.error || "Training failed"}</p>
          {status.results?.traceback && <details className="mt-2"><summary className="text-[10px] text-[#555] cursor-pointer">Traceback</summary><pre className="text-[10px] text-[#555] mt-1 whitespace-pre-wrap">{status.results.traceback}</pre></details>}
        </div>
      )}

      {/* Replay */}
      {isCompleted && replay.length > 0 && (
        <div className="border border-[#1a1a1a] rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Agent Replay</h3>
            <div className="flex items-center gap-2">
              {replay.map((ep, i) => (
                <button key={i} onClick={() => { setReplayEp(i); setReplayStep(0); stopReplay(); }} className={`text-[10px] px-2 py-0.5 rounded ${replayEp === i ? "bg-white text-black" : "bg-[#1a1a1a] text-[#888] hover:text-white"}`}>
                  Ep {i+1} {ep.success ? "✓" : "✗"}
                </button>
              ))}
            </div>
          </div>
          {currentEp && (<>
            <div className="flex items-center gap-3">
              <button onClick={playing ? stopReplay : startReplay} className="flex items-center gap-1 px-3 py-1.5 text-xs bg-[#1a1a1a] rounded hover:bg-[#333] transition-colors">
                {playing ? <><Pause size={10} /> Stop</> : <><Play size={10} /> Play</>}
              </button>
              <input type="range" min={0} max={Math.max(0, currentEp.steps.length-1)} value={replayStep} onChange={e => { stopReplay(); setReplayStep(Number(e.target.value)); }} className="flex-1 h-1 accent-white" />
              <span className="text-[10px] text-[#555] font-mono w-16 text-right">{replayStep+1}/{currentEp.steps.length}</span>
            </div>
            <div className="bg-[#0a0a0a] rounded-lg p-3 font-mono text-[10px] space-y-1.5">
              <div className="flex justify-between text-[#555]"><span>Step {replayStep+1}</span><span>Reward: <span className={currentEp.steps[replayStep]?.reward >= 0 ? "text-green-400" : "text-red-400"}>{currentEp.steps[replayStep]?.reward?.toFixed(4)}</span></span></div>
              <div><span className="text-[#555]">Action: </span><span className="text-purple-400">{JSON.stringify(currentEp.steps[replayStep]?.action)}</span></div>
              <div><span className="text-[#555]">Obs: </span><span className="text-blue-400">[{currentEp.steps[replayStep]?.obs?.map((v:number)=>v.toFixed(2)).join(", ")}]</span></div>
              <div className="mt-2"><div className="flex justify-between text-[#555] mb-0.5"><span>Cumulative Reward</span><span>{currentEp.steps.slice(0,replayStep+1).reduce((s:number,st:any)=>s+(st.reward||0),0).toFixed(2)}</span></div>
                <div className="h-1.5 bg-[#1a1a1a] rounded-full overflow-hidden"><div className="h-full bg-green-500 transition-all duration-100" style={{width:`${Math.min(100,((replayStep+1)/currentEp.steps.length)*100)}%`}} /></div>
              </div>
            </div>
            <div className="flex gap-4 text-[10px] text-[#555]"><span>Total Reward: {currentEp.reward}</span><span>Length: {currentEp.length}</span><span>Success: {currentEp.success?"Yes":"No"}</span></div>
          </>)}
        </div>
      )}

      {!status && <div className="text-center py-8 text-[#555]"><Bot size={32} className="mx-auto mb-3 opacity-30" /><p className="text-sm">No agent trained yet.</p><p className="text-xs mt-1">Configure and start training above.</p></div>}
    </div>
  );
}

// ── Training Report ─────────────────────────────

function TrainingReportView({ report, curve, envName }: { report: any; curve: any[]; envName?: string }) {
  const res = report.results || {};
  const hp = res.hyperparameters || report.hyperparameters || {};
  const repro = report.reproducibility || {};

  return (
    <div className="p-5 space-y-5 bg-[#0a0a0a]">
      <div>
        <h2 className="text-base font-bold flex items-center gap-2"><BarChart3 size={16} /> Training Report</h2>
        <p className="text-[11px] text-[#555] mt-0.5">Run #{report.run_id} &middot; {envName || report.env_name} &middot; Env v{report.env_version}</p>
      </div>

      {/* Summary */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold text-[#888] uppercase tracking-wider">Summary</h3>
        <div className="grid grid-cols-3 gap-3">
          {[
            ["Algorithm", report.algorithm],
            ["Total Timesteps", res.total_timesteps?.toLocaleString()],
            ["Episodes Trained", res.episodes_trained?.toLocaleString()],
            ["Training Duration", res.training_time_sec ? formatDuration(res.training_time_sec) : "—"],
            ["Mean Reward", res.mean_reward != null ? `${res.mean_reward} (±${res.std_reward})` : "—"],
            ["Success Rate", res.success_rate != null ? `${Math.round(res.success_rate*100)}%` : "—"],
            ["Avg Episode Length", res.mean_ep_length],
            ["Eval Episodes", res.eval_episodes],
            ["Env Version", `v${report.env_version}`],
          ].map(([l, v]) => (
            <div key={String(l)} className="flex justify-between text-[11px] border-b border-[#1a1a1a] pb-1">
              <span className="text-[#555]">{l}</span>
              <span className="font-mono text-white">{v ?? "—"}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Eval Rewards per Episode */}
      {res.eval_rewards?.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-[#888] uppercase tracking-wider">Evaluation Episodes</h3>
          <div className="flex gap-2">
            {res.eval_rewards.map((r: number, i: number) => (
              <div key={i} className="flex-1 border border-[#1a1a1a] rounded p-2 text-center">
                <p className={`text-sm font-mono font-bold ${r > 0 ? "text-green-400" : "text-red-400"}`}>{r}</p>
                <p className="text-[9px] text-[#555]">Ep {i+1}{res.eval_lengths?.[i] ? ` (${res.eval_lengths[i]} steps)` : ""}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hyperparameters */}
      {Object.keys(hp).length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-[#888] uppercase tracking-wider">Hyperparameters</h3>
          <div className="grid grid-cols-2 gap-x-6 gap-y-1">
            {Object.entries(hp).map(([k, v]) => (
              <div key={k} className="flex justify-between text-[11px] border-b border-[#1a1a1a] pb-1">
                <span className="text-[#555]">{k}</span>
                <span className="font-mono text-[#bbb]">{typeof v === "number" ? (Number.isInteger(v) ? v : (v as number).toFixed(6)) : String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reproducibility */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold text-[#888] uppercase tracking-wider">Reproducibility</h3>
        <div className="grid grid-cols-2 gap-x-6 gap-y-1">
          {[
            ["Random Seed", repro.random_seed ?? "None (stochastic)"],
            ["SB3 Version", repro.sb3_version],
            ["Gymnasium Version", repro.gymnasium_version],
            ["Env Version", `v${repro.env_version}`],
          ].map(([l, v]) => (
            <div key={String(l)} className="flex justify-between text-[11px] border-b border-[#1a1a1a] pb-1">
              <span className="text-[#555]">{l}</span>
              <span className="font-mono text-[#bbb]">{v ?? "—"}</span>
            </div>
          ))}
        </div>
      </div>

      {report.started_at && (
        <p className="text-[10px] text-[#444] text-right">
          {new Date(report.started_at).toLocaleString()} — {report.completed_at ? new Date(report.completed_at).toLocaleString() : "In progress"}
        </p>
      )}
    </div>
  );
}

// ── History View (Experiment Tracking) ──────────

function HistoryView({ envId }: { envId: number }) {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [compareIds, setCompareIds] = useState<Set<number>>(new Set());
  const [showCompare, setShowCompare] = useState(false);
  const [expandedReport, setExpandedReport] = useState<number | null>(null);
  const [reports, setReports] = useState<Record<number, any>>({});
  const [curves, setCurves] = useState<Record<number, any[]>>({});

  useEffect(() => {
    (async () => {
      try { setRuns(await getTrainingHistory(envId)); } catch {}
      finally { setLoading(false); }
    })();
  }, [envId]);

  async function loadReport(runId: number) {
    if (reports[runId]) { setExpandedReport(expandedReport === runId ? null : runId); return; }
    try {
      const r = await getTrainingReport(envId, runId);
      setReports(p => ({ ...p, [runId]: r }));
      if (r.curve) setCurves(p => ({ ...p, [runId]: r.curve }));
      setExpandedReport(runId);
    } catch {}
  }

  function toggleCompare(id: number) {
    setCompareIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  const completedRuns = runs.filter(r => r.status === "completed");
  const compareRuns = completedRuns.filter(r => compareIds.has(r.id));

  const envVersionGroups = runs.reduce<Record<string, any[]>>((acc, r) => {
    const v = `v${r.env_version || "?"}`;
    if (!acc[v]) acc[v] = [];
    acc[v].push(r);
    return acc;
  }, {});

  if (loading) return <div className="flex justify-center py-12"><Loader2 size={20} className="animate-spin text-[#555]" /></div>;
  if (runs.length === 0) return <div className="text-center py-12 text-[#555]"><FlaskConical size={32} className="mx-auto mb-3 opacity-30" /><p className="text-sm">No experiments yet.</p><p className="text-xs mt-1">Train an agent to create your first experiment.</p></div>;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium flex items-center gap-2"><FlaskConical size={14} /> Experiments</h3>
        {completedRuns.length >= 2 && (
          <button onClick={() => setShowCompare(!showCompare)} className={`text-[10px] px-2.5 py-1 rounded border transition-colors ${showCompare ? "border-blue-800 text-blue-400" : "border-[#1a1a1a] text-[#888] hover:text-white"}`}>
            {showCompare ? "Done Comparing" : "Compare Runs"}
          </button>
        )}
      </div>

      {/* Comparison Table */}
      {showCompare && compareRuns.length >= 2 && (
        <div className="border border-blue-900/50 rounded-lg overflow-hidden">
          <div className="bg-blue-950/20 px-4 py-2 text-xs font-medium text-blue-400">Comparing {compareRuns.length} Runs</div>
          <div className="overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead><tr className="border-b border-[#1a1a1a]">
                <th className="px-3 py-2 text-left text-[#555] font-medium">Metric</th>
                {compareRuns.map(r => <th key={r.id} className="px-3 py-2 text-center font-mono text-[#888]">Run #{r.id}<br/><span className="text-[9px] text-[#555]">{r.algorithm} &middot; v{r.env_version}</span></th>)}
              </tr></thead>
              <tbody>
                {[
                  ["Timesteps", (r: any) => r.total_timesteps?.toLocaleString()],
                  ["Mean Reward", (r: any) => r.mean_reward != null ? <span className="text-green-400">{r.mean_reward}</span> : "—"],
                  ["Success Rate", (r: any) => r.success_rate != null ? <span className="text-yellow-400">{Math.round(r.success_rate*100)}%</span> : "—"],
                  ["Duration", (r: any) => r.training_time_sec ? formatDuration(r.training_time_sec) : "—"],
                ].map(([label, getter]: any) => (
                  <tr key={String(label)} className="border-b border-[#1a1a1a]/50">
                    <td className="px-3 py-1.5 text-[#555]">{label}</td>
                    {compareRuns.map(r => <td key={r.id} className="px-3 py-1.5 text-center font-mono">{getter(r.results || r)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Grouped by Env Version */}
      {Object.entries(envVersionGroups).map(([version, vRuns]) => (
        <div key={version} className="space-y-2">
          <div className="flex items-center gap-2 text-[11px] text-[#555]">
            <GitBranch size={11} />
            <span className="font-mono font-medium text-[#888]">{version}</span>
            <span>&middot; {vRuns.length} run{vRuns.length > 1 ? "s" : ""}</span>
          </div>
          {vRuns.map(r => {
            const isExpanded = expandedReport === r.id;
            return (
              <div key={r.id} className="border border-[#1a1a1a] rounded-lg overflow-hidden">
                <div className="p-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {showCompare && r.status === "completed" && (
                      <input type="checkbox" checked={compareIds.has(r.id)} onChange={() => toggleCompare(r.id)} className="accent-blue-500" />
                    )}
                    <span className="text-xs font-mono text-[#888]">#{r.id}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded ${r.status==="completed"?"bg-green-950 text-green-400":r.status==="running"?"bg-blue-950 text-blue-400 animate-pulse":"bg-red-950 text-red-400"}`}>{r.status}</span>
                    <span className="text-[10px] text-[#555] font-mono">{r.algorithm}</span>
                    <span className="text-[10px] text-[#555]">{r.total_timesteps ? formatSteps(r.total_timesteps) + " steps" : ""}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    {r.mean_reward != null && <span className="text-[10px] font-mono text-green-400">R: {r.mean_reward}</span>}
                    {r.success_rate != null && <span className="text-[10px] font-mono text-yellow-400">{Math.round(r.success_rate*100)}%</span>}
                    {r.training_time_sec != null && <span className="text-[10px] text-[#555]">{formatDuration(r.training_time_sec)}</span>}
                    {r.status === "completed" && (
                      <button onClick={() => loadReport(r.id)} className="text-[10px] text-[#555] hover:text-white transition-colors">
                        <BarChart3 size={12} />
                      </button>
                    )}
                    <span className="text-[10px] text-[#444]">{r.started_at ? new Date(r.started_at).toLocaleDateString() : ""}</span>
                  </div>
                </div>
                {r.results?.error && <div className="px-3 pb-2"><p className="text-[10px] text-red-400 truncate">{r.results.error}</p></div>}
                {isExpanded && reports[r.id] && (
                  <div className="border-t border-[#1a1a1a]">
                    {curves[r.id] && curves[r.id].length > 0 && (
                      <div className="p-4 border-b border-[#1a1a1a]">
                        <h4 className="text-xs font-medium text-[#888] mb-3">Training Curves</h4>
                        <div className="grid grid-cols-2 gap-3">
                          <MiniChart data={curves[r.id]} dataKey="mean_reward" label="Episode Reward" color="#22c55e" status="completed" />
                          <MiniChart data={curves[r.id]} dataKey="mean_ep_length" label="Episode Length" color="#3b82f6" status="completed" />
                          <MiniChart data={curves[r.id]} dataKey="success_rate" label="Success Rate" color="#eab308" format="percent" status="completed" />
                          <MiniChart data={curves[r.id]} dataKey="loss" label="Policy Loss" color="#ef4444" status="completed" />
                        </div>
                      </div>
                    )}
                    <TrainingReportView report={reports[r.id]} curve={curves[r.id] || []} envName={undefined} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}

// ── Docs View ───────────────────────────────────

function DocsView({ env }: { env: any }) {
  const [trainingData, setTrainingData] = useState<any[]>([]);
  const [latestReport, setLatestReport] = useState<any>(null);

  useEffect(() => {
    if (!env) return;
    (async () => {
      try {
        const history = await getTrainingHistory(env.id);
        setTrainingData(history);
        const completed = history.filter((r: any) => r.status === "completed");
        if (completed.length > 0) {
          const best = completed[0];
          try { setLatestReport(await getTrainingReport(env.id, best.id)); } catch {}
        }
      } catch {}
    })();
  }, [env?.id]);

  if (!env) return <div className="flex justify-center py-12"><Loader2 size={20} className="animate-spin text-[#555]" /></div>;

  const spec = env.env_spec || {};
  const obs = spec.observation_space || {};
  const act = spec.action_space || {};
  const reward = spec.reward_function || {};
  const episode = spec.episode || {};
  const completedRuns = trainingData.filter((r: any) => r.status === "completed");
  const latestRes = latestReport?.results || {};
  const hp = latestRes.hyperparameters || latestReport?.hyperparameters || {};

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold mb-1">{env.name}</h2>
        <div className="flex flex-wrap gap-2 mt-2">
          {env.domain && <span className="text-[10px] px-2 py-0.5 bg-[#1a1a1a] rounded-full text-[#888]">{env.domain}</span>}
          {env.difficulty && <span className="text-[10px] px-2 py-0.5 bg-[#1a1a1a] rounded-full text-[#888]">{env.difficulty}</span>}
          <span className="text-[10px] px-2 py-0.5 bg-[#1a1a1a] rounded-full text-[#888]">v{env.version}</span>
          <span className={`text-[10px] px-2 py-0.5 rounded-full ${env.status === "published" ? "bg-green-950 text-green-400" : "bg-[#1a1a1a] text-[#888]"}`}>{env.status}</span>
        </div>
      </div>

      {/* Overview */}
      <section className="space-y-2">
        <h3 className="text-sm font-semibold border-b border-[#1a1a1a] pb-1">Overview</h3>
        <p className="text-[13px] text-[#bbb] leading-relaxed">{env.description || "No description available."}</p>
        <div className="grid grid-cols-2 gap-x-6 gap-y-1 mt-3">
          {[
            ["Domain", env.domain],
            ["Difficulty", env.difficulty],
            ["Max Steps", episode.max_steps || env.max_steps || 1000],
            ["Version", `v${env.version}`],
            ["Status", env.status],
            ["Created", env.created_at ? new Date(env.created_at).toLocaleDateString() : "—"],
          ].map(([l, v]) => (
            <div key={String(l)} className="flex justify-between text-[11px] py-0.5">
              <span className="text-[#555]">{l}</span>
              <span className="font-mono text-[#bbb]">{v ?? "—"}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Observation Space */}
      <section className="space-y-2">
        <h3 className="text-sm font-semibold border-b border-[#1a1a1a] pb-1">Observation Space</h3>
        <div className="grid grid-cols-2 gap-x-6 gap-y-1">
          <div className="flex justify-between text-[11px]"><span className="text-[#555]">Type</span><span className="font-mono text-blue-400">{obs.type || env.observation_space || "Box"}</span></div>
          {obs.shape && <div className="flex justify-between text-[11px]"><span className="text-[#555]">Shape</span><span className="font-mono text-blue-400">[{Array.isArray(obs.shape) ? obs.shape.join(", ") : obs.shape}]</span></div>}
          {obs.low !== undefined && <div className="flex justify-between text-[11px]"><span className="text-[#555]">Range</span><span className="font-mono">[{obs.low}, {obs.high}]</span></div>}
        </div>
        {obs.components?.length > 0 && (
          <div className="mt-2">
            <p className="text-[10px] text-[#555] mb-1.5">Components ({obs.components.length})</p>
            <div className="flex flex-wrap gap-1">{obs.components.map((c: string, i: number) => <span key={i} className="text-[10px] px-2 py-0.5 bg-blue-950/30 text-blue-400 rounded">{c}</span>)}</div>
          </div>
        )}
        <p className="text-[12px] text-[#888] leading-relaxed mt-1">
          The agent receives a {obs.type || "Box"} observation at each step.
          {obs.shape && <> The observation vector has {Array.isArray(obs.shape) ? obs.shape.reduce((a: number, b: number) => a * b, 1) : obs.shape} dimensions.</>}
          {obs.components?.length > 0 && <> Each component encodes different aspects of the environment state: {obs.components.slice(0, 5).join(", ")}{obs.components.length > 5 ? `, and ${obs.components.length - 5} more` : ""}.</>}
        </p>
      </section>

      {/* Action Space */}
      <section className="space-y-2">
        <h3 className="text-sm font-semibold border-b border-[#1a1a1a] pb-1">Action Space</h3>
        <div className="grid grid-cols-2 gap-x-6 gap-y-1">
          <div className="flex justify-between text-[11px]"><span className="text-[#555]">Type</span><span className="font-mono text-purple-400">{act.type || env.action_space || "Discrete"}</span></div>
          {act.shape && <div className="flex justify-between text-[11px]"><span className="text-[#555]">Shape</span><span className="font-mono text-purple-400">[{Array.isArray(act.shape) ? act.shape.join(", ") : act.shape}]</span></div>}
          {act.n !== undefined && <div className="flex justify-between text-[11px]"><span className="text-[#555]">N Actions</span><span className="font-mono text-purple-400">{act.n}</span></div>}
        </div>
        {act.components?.length > 0 && (
          <div className="mt-2">
            <p className="text-[10px] text-[#555] mb-1.5">Actions</p>
            <div className="flex flex-wrap gap-1">{act.components.map((c: string, i: number) => <span key={i} className="text-[10px] px-2 py-0.5 bg-purple-950/30 text-purple-400 rounded">{c}</span>)}</div>
          </div>
        )}
        <p className="text-[12px] text-[#888] leading-relaxed mt-1">
          {act.type === "Discrete" ? "The agent selects one discrete action per timestep. This is suitable for grid-based, turn-based, or categorical decision environments." : act.type === "Box" ? "The agent outputs continuous control values per timestep. This is suitable for robotics, continuous control, and fine-grained manipulation tasks." : "The agent selects an action from the defined action space at each timestep."}
        </p>
      </section>

      {/* Reward Function */}
      <section className="space-y-2">
        <h3 className="text-sm font-semibold border-b border-[#1a1a1a] pb-1">Reward Function</h3>
        <p className="text-[13px] text-[#bbb] leading-relaxed">
          {reward.type || env.reward_description || "Reward function details not available."}
        </p>
        {reward.range && (
          <div className="flex justify-between text-[11px] mt-1"><span className="text-[#555]">Range</span><span className="font-mono">[{Array.isArray(reward.range) ? reward.range.join(", ") : reward.range}]</span></div>
        )}
        {reward.components?.length > 0 && (
          <div className="mt-2">
            <p className="text-[10px] text-[#555] mb-1.5">Reward Components</p>
            <div className="flex flex-wrap gap-1">{reward.components.map((c: string, i: number) => <span key={i} className="text-[10px] px-2 py-0.5 bg-yellow-950/30 text-yellow-400 rounded">{c}</span>)}</div>
          </div>
        )}
      </section>

      {/* Episode & Termination */}
      <section className="space-y-2">
        <h3 className="text-sm font-semibold border-b border-[#1a1a1a] pb-1">Episode Configuration</h3>
        <div className="grid grid-cols-2 gap-x-6 gap-y-1">
          <div className="flex justify-between text-[11px]"><span className="text-[#555]">Max Steps</span><span className="font-mono">{episode.max_steps || env.max_steps || 1000}</span></div>
        </div>
        {episode.termination_conditions?.length > 0 && (
          <div className="mt-2">
            <p className="text-[10px] text-[#555] mb-1">Termination Conditions (episode ends)</p>
            <ul className="space-y-0.5">{episode.termination_conditions.map((c: string, i: number) => <li key={i} className="text-[11px] text-[#bbb] flex items-start gap-1.5"><span className="text-red-400 mt-0.5">&#x2022;</span>{c}</li>)}</ul>
          </div>
        )}
        {episode.truncation_conditions?.length > 0 && (
          <div className="mt-2">
            <p className="text-[10px] text-[#555] mb-1">Truncation Conditions (time limit)</p>
            <ul className="space-y-0.5">{episode.truncation_conditions.map((c: string, i: number) => <li key={i} className="text-[11px] text-[#bbb] flex items-start gap-1.5"><span className="text-yellow-400 mt-0.5">&#x2022;</span>{c}</li>)}</ul>
          </div>
        )}
      </section>

      {/* Training Results (if any) */}
      {completedRuns.length > 0 && (
        <section className="space-y-3">
          <h3 className="text-sm font-semibold border-b border-[#1a1a1a] pb-1">Training Results</h3>
          <p className="text-[12px] text-[#888]">{completedRuns.length} completed training run{completedRuns.length > 1 ? "s" : ""} recorded for this environment.</p>

          {latestRes.mean_reward !== undefined && (
            <div className="grid grid-cols-4 gap-3">
              <div className="border border-[#1a1a1a] rounded-lg p-3 text-center">
                <p className="text-base font-mono font-bold text-green-400">{latestRes.mean_reward}</p>
                <p className="text-[9px] text-[#555] mt-0.5">Mean Reward</p>
              </div>
              <div className="border border-[#1a1a1a] rounded-lg p-3 text-center">
                <p className="text-base font-mono font-bold text-yellow-400">{Math.round((latestRes.success_rate || 0) * 100)}%</p>
                <p className="text-[9px] text-[#555] mt-0.5">Success Rate</p>
              </div>
              <div className="border border-[#1a1a1a] rounded-lg p-3 text-center">
                <p className="text-base font-mono font-bold text-blue-400">{latestRes.mean_ep_length}</p>
                <p className="text-[9px] text-[#555] mt-0.5">Avg Length</p>
              </div>
              <div className="border border-[#1a1a1a] rounded-lg p-3 text-center">
                <p className="text-base font-mono font-bold text-[#888]">{latestRes.training_time_sec ? formatDuration(latestRes.training_time_sec) : "—"}</p>
                <p className="text-[9px] text-[#555] mt-0.5">Train Time</p>
              </div>
            </div>
          )}

          {/* Best run details */}
          <div className="grid grid-cols-2 gap-x-6 gap-y-1">
            {[
              ["Algorithm", latestReport?.algorithm],
              ["Total Timesteps", latestRes.total_timesteps?.toLocaleString()],
              ["Episodes Trained", latestRes.episodes_trained?.toLocaleString()],
              ["Eval Episodes", latestRes.eval_episodes],
              ["Reward StdDev", latestRes.std_reward],
              ["Env Version", `v${latestReport?.env_version || "?"}`],
            ].map(([l, v]) => (
              <div key={String(l)} className="flex justify-between text-[11px] py-0.5">
                <span className="text-[#555]">{l}</span>
                <span className="font-mono text-[#bbb]">{v ?? "—"}</span>
              </div>
            ))}
          </div>

          {/* Hyperparameters */}
          {Object.keys(hp).length > 0 && (
            <div className="mt-3">
              <p className="text-[10px] text-[#555] mb-1.5 font-medium uppercase tracking-wider">Hyperparameters</p>
              <div className="grid grid-cols-2 gap-x-6 gap-y-1">
                {Object.entries(hp).map(([k, v]) => (
                  <div key={k} className="flex justify-between text-[11px] py-0.5">
                    <span className="text-[#555]">{k}</span>
                    <span className="font-mono text-[#bbb]">{typeof v === "number" ? (Number.isInteger(v) ? v : (v as number).toFixed(6)) : String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* All runs summary */}
          {completedRuns.length > 1 && (
            <div className="mt-3">
              <p className="text-[10px] text-[#555] mb-1.5 font-medium uppercase tracking-wider">All Completed Runs</p>
              <div className="border border-[#1a1a1a] rounded-lg overflow-hidden">
                <table className="w-full text-[11px]">
                  <thead><tr className="border-b border-[#1a1a1a]">
                    <th className="px-3 py-1.5 text-left text-[#555] font-medium">Run</th>
                    <th className="px-3 py-1.5 text-left text-[#555] font-medium">Algo</th>
                    <th className="px-3 py-1.5 text-right text-[#555] font-medium">Steps</th>
                    <th className="px-3 py-1.5 text-right text-[#555] font-medium">Reward</th>
                    <th className="px-3 py-1.5 text-right text-[#555] font-medium">Success</th>
                  </tr></thead>
                  <tbody>{completedRuns.slice(0, 10).map((r: any) => (
                    <tr key={r.id} className="border-b border-[#1a1a1a]/30">
                      <td className="px-3 py-1 font-mono text-[#888]">#{r.id}</td>
                      <td className="px-3 py-1 text-[#bbb]">{r.algorithm}</td>
                      <td className="px-3 py-1 text-right font-mono text-[#bbb]">{r.total_timesteps ? formatSteps(r.total_timesteps) : "—"}</td>
                      <td className="px-3 py-1 text-right font-mono text-green-400">{r.mean_reward ?? "—"}</td>
                      <td className="px-3 py-1 text-right font-mono text-yellow-400">{r.success_rate != null ? `${Math.round(r.success_rate * 100)}%` : "—"}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Training Guide */}
      <section className="space-y-2">
        <h3 className="text-sm font-semibold border-b border-[#1a1a1a] pb-1">Training Guide</h3>
        <div className="space-y-3 text-[12px] text-[#888] leading-relaxed">
          <div>
            <p className="text-white text-[11px] font-medium mb-1">Algorithm Selection</p>
            <p>The platform auto-selects the best algorithm based on the action space. {act.type === "Discrete" ? "Discrete spaces use PPO (general) or DQN (sample-efficient). PPO is recommended for most cases." : act.type === "Box" ? "Continuous spaces use SAC (off-policy, sample-efficient) which handles continuous control well." : "PPO is used as the general-purpose default."}</p>
          </div>
          <div>
            <p className="text-white text-[11px] font-medium mb-1">Recommended Timesteps</p>
            <p><span className="text-[#bbb]">Quick test:</span> 5K-10K steps (1-3 min). <span className="text-[#bbb]">Meaningful results:</span> 50K-100K steps (5-15 min). <span className="text-[#bbb]">Strong performance:</span> 500K-1M steps (20-60 min). Complex environments with high-dimensional observations or sparse rewards need more steps.</p>
          </div>
          <div>
            <p className="text-white text-[11px] font-medium mb-1">Continue Training</p>
            <p>After a run completes, use <span className="text-white">Continue Training</span> to load the saved model weights and train further. This is useful for incrementally improving performance without starting from scratch. Each continuation is recorded as a separate experiment in History.</p>
          </div>
          <div>
            <p className="text-white text-[11px] font-medium mb-1">Experiment Workflow</p>
            <p>Each training run is an experiment linked to the environment version. To improve results: (1) Continue Training for more timesteps, (2) modify the environment via chat to create a new version, then retrain. The History tab tracks all runs grouped by env version for comparison.</p>
          </div>
          <div>
            <p className="text-white text-[11px] font-medium mb-1">Metrics Explained</p>
            <p><span className="text-green-400">Episode Reward</span> — cumulative reward per episode (higher = better). <span className="text-blue-400">Episode Length</span> — steps per episode (depends on task). <span className="text-yellow-400">Success Rate</span> — fraction of successful episodes. <span className="text-red-400">Policy Loss</span> — optimization loss (should decrease then stabilize).</p>
          </div>
        </div>
      </section>

      {/* Usage */}
      <section className="space-y-2">
        <h3 className="text-sm font-semibold border-b border-[#1a1a1a] pb-1">Usage (Python SDK)</h3>
        <pre className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-4 text-xs text-[#bbb] overflow-x-auto">{`import kualia

env = kualia.make('${env.slug || "your-env"}', api_key='YOUR_KEY')
obs, info = env.reset(seed=42)

for step in range(${episode.max_steps || env.max_steps || 1000}):
    action = env.action_space.sample()  # or your trained agent
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()`}</pre>
      </section>
    </div>
  );
}

// ── Shared Components ───────────────────────────

function MiniChart({ data, dataKey, label, color, format, status }: { data: any[]; dataKey: string; label: string; color: string; format?: string; status?: string }) {
  const values = data.map(d => d[dataKey]).filter(v => v !== undefined && v !== null);
  if (values.length < 2) {
    const msg = status === "completed" ? `${label}: N/A` : `${label}: waiting...`;
    return <div className="border border-[#1a1a1a] rounded-lg p-3 h-28 flex items-center justify-center"><span className="text-[10px] text-[#333]">{msg}</span></div>;
  }
  const min = Math.min(...values); const max = Math.max(...values); const range = max - min || 1;
  const w = 200; const h = 60;
  const points = values.map((v, i) => `${(i/(values.length-1))*w},${h-((v-min)/range)*h}`).join(" ");
  const latest = values[values.length-1];
  const formatted = format === "percent" ? `${(latest*100).toFixed(1)}%` : typeof latest === "number" ? latest.toFixed(2) : latest;
  return (
    <div className="border border-[#1a1a1a] rounded-lg p-3">
      <div className="flex justify-between items-center mb-1"><span className="text-[10px] text-[#555]">{label}</span><span className="text-xs font-mono" style={{color}}>{formatted}</span></div>
      <svg width="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="overflow-visible">
        <polyline fill="none" stroke={color} strokeWidth="2" points={points} opacity={0.8} />
        <circle cx={w} cy={h-((latest-min)/range)*h} r="3" fill={color} />
      </svg>
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: any; color: string }) {
  const colors: Record<string, string> = { green: "text-green-400", yellow: "text-yellow-400", blue: "text-blue-400", gray: "text-[#888]" };
  return <div className="border border-[#1a1a1a] rounded-lg p-3 text-center"><p className={`text-lg font-mono font-bold ${colors[color]||"text-white"}`}>{value}</p><p className="text-[10px] text-[#555] mt-0.5">{label}</p></div>;
}

function DashboardView({ env, spec, tests }: { env: any; spec: any; tests: any[] }) {
  const passed = tests.filter((t:any) => t.status === "pass").length;
  const total = tests.length || 8;
  const obsSpace = spec.observation_space || {};
  const actSpace = spec.action_space || {};
  const rewardFn = spec.reward_function || {};
  const episode = spec.episode || {};
  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className={`w-3 h-3 rounded-full ${passed===total?"bg-green-500":passed>=6?"bg-yellow-500":"bg-red-500"}`} />
        <span className="text-sm font-medium">{passed===total?"All Tests Passing":`${passed}/${total} Tests Passing`}</span>
      </div>
      <div className="grid grid-cols-4 gap-2">
        {tests.map((t:any)=>(
          <div key={t.name} className={`border rounded-lg p-2.5 ${t.status==="pass"?"border-green-900/50 bg-green-950/20":"border-red-900/50 bg-red-950/20"}`} title={t.detail}>
            <div className="flex items-center gap-1.5 mb-1">{t.status==="pass"?<CheckCircle size={10} className="text-green-400 shrink-0"/>:<XCircle size={10} className="text-red-400 shrink-0"/>}<span className="text-[10px] font-medium truncate">{t.name}</span></div>
            <p className="text-[9px] text-[#555] line-clamp-2">{t.detail}</p>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <SpaceCard title="Observation Space" icon={<Eye size={12} className="text-blue-400"/>} space={obsSpace} fallback={env?.observation_space} color="blue" />
        <SpaceCard title="Action Space" icon={<Zap size={12} className="text-purple-400"/>} space={actSpace} fallback={env?.action_space} color="purple" />
      </div>
      <div className="border border-[#1a1a1a] rounded-lg p-4">
        <h4 className="text-xs font-medium flex items-center gap-1.5 mb-3"><Target size={12} className="text-yellow-400"/> Reward Function</h4>
        {(rewardFn.type||env?.reward_description)&&<p className="text-[11px] text-[#aaa]">{rewardFn.type||env?.reward_description}</p>}
        {rewardFn.components?.length>0&&<div className="flex flex-wrap gap-1 mt-2">{rewardFn.components.map((c:string,i:number)=><span key={i} className="text-[9px] px-1.5 py-0.5 bg-yellow-950/30 text-yellow-400 rounded">{c}</span>)}</div>}
      </div>
      <div className="border border-[#1a1a1a] rounded-lg p-4">
        <h4 className="text-xs font-medium flex items-center gap-1.5 mb-3"><Layers size={12} className="text-cyan-400"/> Episode</h4>
        <div className="grid grid-cols-2 gap-x-6 gap-y-2">
          {[["Max Steps",episode.max_steps||env?.max_steps],["Domain",env?.domain],["Difficulty",env?.difficulty],["Status",env?.status]].map(([l,v])=>(<div key={String(l)} className="flex justify-between text-[11px]"><span className="text-[#555]">{l}</span><span className="font-mono">{v||"—"}</span></div>))}
        </div>
      </div>
      {env?.description&&<div className="border border-[#1a1a1a] rounded-lg p-4"><h4 className="text-xs font-medium mb-2">Description</h4><p className="text-[11px] text-[#aaa] leading-relaxed">{env.description}</p></div>}
    </div>
  );
}

function SpaceCard({ title, icon, space, fallback, color }: { title: string; icon: React.ReactNode; space: any; fallback?: string; color: string }) {
  return (
    <div className="border border-[#1a1a1a] rounded-lg p-4">
      <h4 className="text-xs font-medium flex items-center gap-1.5 mb-3">{icon} {title}</h4>
      <div className="space-y-2">
        <div className="flex justify-between text-[11px]"><span className="text-[#555]">Type</span><span className="font-mono">{space.type||fallback||"—"}</span></div>
        {space.shape&&<div className="flex justify-between text-[11px]"><span className="text-[#555]">Shape</span><span className="font-mono">[{Array.isArray(space.shape)?space.shape.join(", "):space.shape}]</span></div>}
        {space.low!==undefined&&<div className="flex justify-between text-[11px]"><span className="text-[#555]">Range</span><span className="font-mono">[{space.low}, {space.high}]</span></div>}
        {space.components?.length>0&&<div className="mt-2"><p className="text-[10px] text-[#555] mb-1">Components</p><div className="flex flex-wrap gap-1">{space.components.map((c:string,i:number)=><span key={i} className={`text-[9px] px-1.5 py-0.5 rounded bg-${color}-950/30 text-${color}-400`}>{c}</span>)}</div></div>}
      </div>
    </div>
  );
}

function CodeView({ env, versions, showVersions, setShowVersions, handleRollback }: { env: any; versions: any[]; showVersions: boolean; setShowVersions: (v: boolean) => void; handleRollback: (v: number) => void }) {
  return (
    <div className="space-y-4">
      <pre className="code-block text-xs leading-relaxed whitespace-pre overflow-x-auto">{env?.code || "# No code yet"}</pre>
      <div>
        <button onClick={() => setShowVersions(!showVersions)} className="flex items-center gap-1 text-xs text-[#555] hover:text-[#888]">
          <ChevronDown size={12} className={showVersions ? "rotate-180" : ""} /> Version History ({versions.length})
        </button>
        {showVersions && <div className="mt-2 space-y-1">{versions.map(v => (
          <div key={v.id} className="flex items-center justify-between text-xs border border-[#1a1a1a] rounded p-2">
            <div><span className="text-[#888]">v{v.version}</span><span className="text-[#555] ml-2">{v.change_summary}</span></div>
            <button onClick={() => handleRollback(v.version)} className="text-[#555] hover:text-white" title="Rollback"><RotateCcw size={12} /></button>
          </div>
        ))}</div>}
      </div>
    </div>
  );
}
