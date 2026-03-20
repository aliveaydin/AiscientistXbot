"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, Play, Loader2, CheckCircle, BookOpen,
  FlaskConical, Cpu, BarChart3, FileText, ChevronRight,
  ExternalLink, Beaker, Brain, Wrench,
} from "lucide-react";
import {
  getLabProject, getLabChatboard, getLabEnvironments,
  getLabTrainingRuns, getLabPaper, getLabReferences,
  runLabPhase, runLabAll,
} from "@/lib/api";

const PHASES = ["research", "design", "experiment", "analyze", "write", "review"];

const phaseConfig: Record<string, { label: string; icon: typeof Brain; desc: string }> = {
  research: { label: "Research", icon: Brain, desc: "Literature & hypothesis" },
  design:   { label: "Design", icon: Wrench, desc: "Generate environments" },
  experiment: { label: "Experiment", icon: Beaker, desc: "Train agents" },
  analyze:  { label: "Analyze", icon: BarChart3, desc: "Interpret results" },
  write:    { label: "Write", icon: FileText, desc: "Draft paper" },
  review:   { label: "Review", icon: CheckCircle, desc: "Review & finalize" },
};

const agentColors: Record<string, { text: string; border: string; bg: string }> = {
  sage:  { text: "text-amber-400", border: "border-amber-900/60", bg: "bg-amber-950/20" },
  atlas: { text: "text-blue-400", border: "border-blue-900/60", bg: "bg-blue-950/20" },
};

const agentNames: Record<string, string> = { sage: "Sage", atlas: "Atlas" };
const agentRoles: Record<string, string> = { sage: "Research Strategist", atlas: "RL Engineer" };

type Tab = "feed" | "environments" | "training" | "paper" | "references";

export default function ResearchProjectPage() {
  const { id } = useParams();
  const projectId = Number(id);

  const [project, setProject] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [environments, setEnvironments] = useState<any[]>([]);
  const [trainingRuns, setTrainingRuns] = useState<any[]>([]);
  const [paper, setPaper] = useState<any>(null);
  const [references, setReferences] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [runningAll, setRunningAll] = useState(false);
  const [tab, setTab] = useState<Tab>("feed");
  const chatEnd = useRef<HTMLDivElement>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const loadAll = useCallback(async () => {
    try {
      const [proj, chat, refs] = await Promise.all([
        getLabProject(projectId),
        getLabChatboard(projectId),
        getLabReferences(projectId).catch(() => []),
      ]);
      setProject(proj);
      setMessages(chat);
      setReferences(refs);

      if (proj.environment_count > 0) {
        getLabEnvironments(projectId).then(setEnvironments).catch(() => {});
      }

      const phaseIdx = PHASES.indexOf(proj.current_phase);
      if (phaseIdx >= 2 || proj.status === "completed") {
        getLabTrainingRuns(projectId).then(setTrainingRuns).catch(() => {});
      }
      if (phaseIdx >= 4 || proj.status === "completed") {
        getLabPaper(projectId).then(setPaper).catch(() => {});
      }
    } catch {
      setProject(null);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { loadAll(); }, [loadAll]);
  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const startPolling = useCallback((onStopCondition: (proj: any, prevPhase: string) => boolean, setFlag: (v: boolean) => void, capturedPhase: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const [proj, chat] = await Promise.all([
          getLabProject(projectId),
          getLabChatboard(projectId),
        ]);
        setProject(proj);
        setMessages(chat);

        if (proj.environment_count > 0) {
          getLabEnvironments(projectId).then(setEnvironments).catch(() => {});
        }
        const phaseIdx = PHASES.indexOf(proj.current_phase);
        if (phaseIdx >= 2 || proj.status === "completed") {
          getLabTrainingRuns(projectId).then(setTrainingRuns).catch(() => {});
        }
        if (phaseIdx >= 4 || proj.status === "completed") {
          getLabPaper(projectId).then(setPaper).catch(() => {});
        }

        if (onStopCondition(proj, capturedPhase)) {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          setFlag(false);
        }
      } catch { /* ignore */ }
    }, 4000);
  }, [projectId]);

  async function handleRunPhase() {
    if (!project) return;
    const capturedPhase = project.current_phase;
    setRunning(true);
    try {
      await runLabPhase(projectId);
      startPolling(
        (proj, prev) => proj.current_phase !== prev || proj.status === "completed" || proj.status === "failed",
        setRunning,
        capturedPhase,
      );
    } catch {
      setRunning(false);
    }
  }

  async function handleRunAll() {
    if (!project) return;
    const capturedPhase = project.current_phase;
    setRunningAll(true);
    try {
      await runLabAll(projectId);
      startPolling(
        (proj) => proj.status === "completed" || proj.status === "failed",
        setRunningAll,
        capturedPhase,
      );
    } catch {
      setRunningAll(false);
    }
  }

  const currentPhaseIdx = project ? PHASES.indexOf(project.current_phase) : -1;
  const isCompleted = project?.status === "completed";
  const isActive = project?.status === "active";

  const completedPhases = useMemo(() => {
    if (!project) return new Set<string>();
    if (isCompleted) return new Set(PHASES);
    const idx = PHASES.indexOf(project.current_phase);
    return new Set(PHASES.slice(0, idx));
  }, [project, isCompleted]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-16 flex justify-center">
        <Loader2 className="w-6 h-6 text-[#555] animate-spin" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-16">
        <p className="text-[#888]">Project not found.</p>
        <Link href="/dashboard/research" className="text-sm text-[#555] hover:text-white mt-4 inline-block">Back</Link>
      </div>
    );
  }

  const tabs: { key: Tab; label: string; icon: typeof FlaskConical; count?: number }[] = [
    { key: "feed", label: "Live Feed", icon: FlaskConical, count: messages.length },
    { key: "environments", label: "Environments", icon: Cpu, count: environments.length },
    { key: "training", label: "Training", icon: BarChart3, count: trainingRuns.length },
    { key: "paper", label: "Paper", icon: FileText },
    { key: "references", label: "References", icon: BookOpen, count: references.length },
  ];

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 fade-in">
      {/* Back */}
      <Link href="/dashboard/research" className="text-sm text-[#555] hover:text-white flex items-center gap-1 mb-6">
        <ArrowLeft size={14} /> Back to Research
      </Link>

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold mb-1">{project.title}</h1>
            {project.topic && <p className="text-sm text-[#888]">{project.topic}</p>}
          </div>
          <span className={`shrink-0 text-xs px-3 py-1 rounded-full border font-medium ${
            isCompleted ? "border-green-800 text-green-400 bg-green-950/30" :
            isActive ? "border-blue-800 text-blue-400 bg-blue-950/30" :
            "border-[#222] text-[#888] bg-[#0a0a0a]"
          }`}>{project.status}</span>
        </div>
      </div>

      {/* Phase Timeline */}
      <div className="mb-8 p-4 border border-[#1a1a1a] rounded-xl bg-[#0a0a0a]">
        <div className="flex items-center justify-between gap-1">
          {PHASES.map((phase, i) => {
            const cfg = phaseConfig[phase];
            const Icon = cfg.icon;
            const isCurrent = project.current_phase === phase && !isCompleted;
            const isDone = completedPhases.has(phase);
            return (
              <div key={phase} className="flex items-center flex-1">
                <div className={`flex flex-col items-center flex-1 ${
                  isCurrent ? "opacity-100" : isDone ? "opacity-80" : "opacity-30"
                }`}>
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center mb-1.5 transition-all ${
                    isCurrent ? "bg-white text-black ring-2 ring-white/20" :
                    isDone ? "bg-green-900/50 text-green-400 border border-green-800" :
                    "bg-[#111] text-[#555] border border-[#1a1a1a]"
                  }`}>
                    {isDone ? <CheckCircle size={16} /> : isCurrent && (running || runningAll)
                      ? <Loader2 size={16} className="animate-spin" /> : <Icon size={16} />}
                  </div>
                  <span className={`text-[11px] font-medium ${isCurrent ? "text-white" : isDone ? "text-green-400" : "text-[#555]"}`}>
                    {cfg.label}
                  </span>
                  <span className="text-[9px] text-[#444] hidden sm:block">{cfg.desc}</span>
                </div>
                {i < PHASES.length - 1 && (
                  <div className={`h-px flex-1 mx-1 mt-[-18px] ${isDone ? "bg-green-800" : "bg-[#1a1a1a]"}`} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Run Controls */}
      {isActive && (
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={handleRunPhase}
            disabled={running || runningAll}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-white text-black rounded-lg font-medium hover:bg-[#ddd] disabled:opacity-40 transition-colors"
          >
            {running ? <><Loader2 size={14} className="animate-spin" /> Running...</> : <><ChevronRight size={14} /> Run Next Phase</>}
          </button>
          <button
            onClick={handleRunAll}
            disabled={running || runningAll}
            className="flex items-center gap-2 px-4 py-2 text-sm border border-[#222] rounded-lg text-[#888] hover:text-white hover:border-[#444] disabled:opacity-40 transition-colors"
          >
            {runningAll ? <><Loader2 size={14} className="animate-spin" /> Running All...</> : <><Play size={14} /> Run All Phases</>}
          </button>
          {(running || runningAll) && (
            <span className="text-xs text-blue-400 animate-pulse ml-2">
              {runningAll ? "Pipeline running" : "Phase running"} — auto-refreshing...
            </span>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-[#1a1a1a] pb-px overflow-x-auto">
        {tabs.map(t => {
          const Icon = t.icon;
          const active = tab === t.key;
          return (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                active ? "border-white text-white" : "border-transparent text-[#555] hover:text-[#999]"
              }`}
            >
              <Icon size={14} />
              {t.label}
              {t.count !== undefined && t.count > 0 && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${active ? "bg-white/10" : "bg-[#111]"}`}>
                  {t.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {tab === "feed" && <FeedTab messages={messages} chatEnd={chatEnd} runningAll={running || runningAll} isActive={isActive} />}
      {tab === "environments" && <EnvironmentsTab environments={environments} />}
      {tab === "training" && <TrainingTab runs={trainingRuns} />}
      {tab === "paper" && <PaperTab paper={paper} />}
      {tab === "references" && <ReferencesTab references={references} />}
    </div>
  );
}

/* ─── Feed Tab ───────────────────────────────────────────────── */

function FeedTab({ messages, chatEnd, runningAll, isActive }: {
  messages: any[]; chatEnd: React.RefObject<HTMLDivElement | null>; runningAll: boolean; isActive: boolean;
}) {
  if (!messages.length) {
    return (
      <div className="border border-dashed border-[#1a1a1a] rounded-xl p-12 text-center">
        <FlaskConical size={32} className="mx-auto text-[#333] mb-3" />
        <p className="text-[#555] text-sm mb-1">No activity yet.</p>
        {isActive && <p className="text-[10px] text-[#444]">Click &quot;Run Next Phase&quot; or &quot;Run All Phases&quot; to start.</p>}
      </div>
    );
  }

  return (
    <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
      {messages.map((m: any) => {
        const colors = agentColors[m.agent_name] || { text: "text-[#888]", border: "border-[#1a1a1a]", bg: "" };
        const name = agentNames[m.agent_name] || m.agent_name;
        const role = agentRoles[m.agent_name] || "";
        return (
          <div key={m.id} className={`border rounded-lg p-4 ${colors.border} ${colors.bg}`}>
            <div className="flex items-center gap-2 mb-2">
              <span className={`text-sm font-semibold ${colors.text}`}>{name}</span>
              <span className="text-[10px] text-[#555]">{role}</span>
              <span className="text-[10px] text-[#444] font-mono ml-auto px-1.5 py-0.5 border border-[#1a1a1a] rounded">
                {m.phase}
              </span>
            </div>
            <div className="text-sm text-[#ccc] leading-relaxed whitespace-pre-wrap break-words">
              {m.content}
            </div>
          </div>
        );
      })}
      {runningAll && (
        <div className="flex items-center gap-2 text-sm text-blue-400 py-3">
          <Loader2 size={14} className="animate-spin" />
          <span>Agents are working...</span>
        </div>
      )}
      <div ref={chatEnd} />
    </div>
  );
}

/* ─── Environments Tab ───────────────────────────────────────── */

function EnvironmentsTab({ environments }: { environments: any[] }) {
  if (!environments.length) {
    return (
      <div className="border border-dashed border-[#1a1a1a] rounded-xl p-12 text-center">
        <Cpu size={32} className="mx-auto text-[#333] mb-3" />
        <p className="text-[#555] text-sm">No environments generated yet.</p>
        <p className="text-[10px] text-[#444] mt-1">Environments are created during the Design phase.</p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {environments.map((env: any) => {
        const tests = env.test_results;
        const passed = tests?.passed ?? 0;
        const total = tests?.total ?? 0;
        const allPassed = passed === total && total > 0;
        return (
          <div key={env.id} className="border border-[#1a1a1a] rounded-xl p-5 bg-[#0a0a0a] hover:border-[#333] transition-colors">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-sm">{env.name}</h3>
                <p className="text-[11px] text-[#555] mt-0.5">
                  {env.domain} &middot; {env.difficulty}
                </p>
              </div>
              <span className={`text-[10px] px-2 py-0.5 rounded-full border ${
                allPassed ? "border-green-800 text-green-400" : "border-yellow-800 text-yellow-400"
              }`}>
                {passed}/{total} tests
              </span>
            </div>
            {env.description && (
              <p className="text-xs text-[#888] mb-3 line-clamp-2">{env.description}</p>
            )}
            <div className="flex flex-wrap gap-2 text-[10px] text-[#555] mb-3">
              {env.observation_space && <span className="px-2 py-0.5 bg-[#111] rounded border border-[#1a1a1a]">obs: {env.observation_space.substring(0, 40)}</span>}
              {env.action_space && <span className="px-2 py-0.5 bg-[#111] rounded border border-[#1a1a1a]">act: {env.action_space.substring(0, 40)}</span>}
            </div>
            <Link
              href={`/builder/${env.id}`}
              className="flex items-center gap-1 text-xs text-[#555] hover:text-white transition-colors"
            >
              Open in Builder <ExternalLink size={10} />
            </Link>
          </div>
        );
      })}
    </div>
  );
}

/* ─── Training Tab ───────────────────────────────────────────── */

function TrainingTab({ runs }: { runs: any[] }) {
  if (!runs.length) {
    return (
      <div className="border border-dashed border-[#1a1a1a] rounded-xl p-12 text-center">
        <BarChart3 size={32} className="mx-auto text-[#333] mb-3" />
        <p className="text-[#555] text-sm">No training runs yet.</p>
        <p className="text-[10px] text-[#444] mt-1">Training starts during the Experiment phase.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Total Runs" value={runs.length} />
        <StatCard label="Completed" value={runs.filter(r => r.status === "completed").length} color="text-green-400" />
        <StatCard label="Best Reward" value={
          Math.max(...runs.filter(r => r.mean_reward != null).map(r => r.mean_reward), 0).toFixed(2)
        } />
        <StatCard label="Avg Success" value={
          (runs.filter(r => r.success_rate != null).reduce((s, r) => s + r.success_rate, 0) /
           Math.max(runs.filter(r => r.success_rate != null).length, 1) * 100).toFixed(0) + "%"
        } />
      </div>

      {/* Run cards */}
      {runs.map((run: any) => (
        <TrainingRunCard key={run.id} run={run} />
      ))}
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="border border-[#1a1a1a] rounded-lg p-3 bg-[#0a0a0a]">
      <p className="text-[10px] text-[#555] uppercase tracking-wider">{label}</p>
      <p className={`text-lg font-bold mt-0.5 ${color || "text-white"}`}>{value}</p>
    </div>
  );
}

function TrainingRunCard({ run }: { run: any }) {
  const [expanded, setExpanded] = useState(false);
  const isCompleted = run.status === "completed";
  const isRunning = run.status === "running";

  return (
    <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a] overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-4 text-left hover:bg-[#111] transition-colors"
      >
        <ChevronRight size={14} className={`text-[#555] transition-transform ${expanded ? "rotate-90" : ""}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium truncate">{run.env_name}</span>
            <span className="text-[10px] px-2 py-0.5 bg-[#111] border border-[#1a1a1a] rounded font-mono">
              {run.algorithm}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          {isCompleted && run.mean_reward != null && (
            <span className="text-xs text-[#888]">Reward: <span className="text-white font-medium">{run.mean_reward}</span></span>
          )}
          <span className={`text-[10px] px-2 py-0.5 rounded-full border ${
            isCompleted ? "border-green-800 text-green-400" :
            isRunning ? "border-blue-800 text-blue-400" :
            "border-red-800 text-red-400"
          }`}>
            {isRunning && <Loader2 size={10} className="inline animate-spin mr-1" />}
            {run.status}
          </span>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-[#1a1a1a] p-4">
          {isCompleted ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <MiniStat label="Mean Reward" value={run.mean_reward ?? "N/A"} />
                <MiniStat label="Success Rate" value={run.success_rate != null ? `${(run.success_rate * 100).toFixed(1)}%` : "N/A"} />
                <MiniStat label="Timesteps" value={run.total_timesteps?.toLocaleString() ?? "N/A"} />
                <MiniStat label="Duration" value={run.training_time_sec ? `${run.training_time_sec}s` : "N/A"} />
              </div>
              {run.curve && run.curve.length > 0 && <MiniRewardChart curve={run.curve} />}
            </div>
          ) : (
            <p className="text-xs text-[#555]">
              {isRunning ? "Training in progress..." : `Status: ${run.status}`}
            </p>
          )}
          <div className="mt-3">
            <Link
              href={`/builder/${run.env_id}`}
              className="text-xs text-[#555] hover:text-white flex items-center gap-1"
            >
              Open Environment <ExternalLink size={10} />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-[10px] text-[#555]">{label}</p>
      <p className="text-sm font-medium">{value}</p>
    </div>
  );
}

function MiniRewardChart({ curve }: { curve: any[] }) {
  const rewards = curve.map(p => p.mean_reward ?? 0);
  const min = Math.min(...rewards);
  const max = Math.max(...rewards);
  const range = max - min || 1;

  const w = 400;
  const h = 80;
  const points = rewards.map((r, i) => {
    const x = (i / Math.max(rewards.length - 1, 1)) * w;
    const y = h - ((r - min) / range) * (h - 10) - 5;
    return `${x},${y}`;
  });
  const pathD = points.length > 1 ? `M${points.join(" L")}` : "";

  if (!pathD) return null;

  return (
    <div>
      <p className="text-[10px] text-[#555] mb-1">Reward Curve</p>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-20 bg-[#111] rounded-lg border border-[#1a1a1a]" preserveAspectRatio="none">
        <path d={pathD} fill="none" stroke="#3b82f6" strokeWidth="2" />
      </svg>
      <div className="flex justify-between text-[9px] text-[#555] mt-1">
        <span>{min.toFixed(2)}</span>
        <span>{max.toFixed(2)}</span>
      </div>
    </div>
  );
}

/* ─── Paper Tab ──────────────────────────────────────────────── */

function PaperTab({ paper }: { paper: any }) {
  if (!paper) {
    return (
      <div className="border border-dashed border-[#1a1a1a] rounded-xl p-12 text-center">
        <FileText size={32} className="mx-auto text-[#333] mb-3" />
        <p className="text-[#555] text-sm">No paper yet.</p>
        <p className="text-[10px] text-[#444] mt-1">The paper is written during the Write phase.</p>
      </div>
    );
  }

  return (
    <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a]">
      <div className="p-6 border-b border-[#1a1a1a]">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold">{paper.title}</h2>
            <p className="text-xs text-[#555] mt-1">
              Status: <span className={paper.status === "final" ? "text-green-400" : "text-yellow-400"}>{paper.status}</span>
              {" "}| Version {paper.version}
            </p>
          </div>
        </div>
        {paper.abstract && (
          <div className="mt-4 p-4 bg-[#111] rounded-lg border border-[#1a1a1a]">
            <p className="text-[10px] text-[#555] uppercase tracking-wider mb-2">Abstract</p>
            <p className="text-sm text-[#ccc] leading-relaxed">{paper.abstract}</p>
          </div>
        )}
      </div>
      <div className="p-6 prose prose-invert prose-sm max-w-none">
        <div className="text-sm text-[#ccc] leading-relaxed whitespace-pre-wrap break-words">
          {paper.content}
        </div>
      </div>
    </div>
  );
}

/* ─── References Tab ─────────────────────────────────────────── */

function ReferencesTab({ references }: { references: any[] }) {
  if (!references.length) {
    return (
      <div className="border border-dashed border-[#1a1a1a] rounded-xl p-12 text-center">
        <BookOpen size={32} className="mx-auto text-[#333] mb-3" />
        <p className="text-[#555] text-sm">No references yet.</p>
        <p className="text-[10px] text-[#444] mt-1">Papers are imported from ArXiv during the Research phase.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-[#555] mb-3">{references.length} reference paper(s) from ArXiv</p>
      {references.map((r: any) => (
        <div key={r.id} className="flex items-center justify-between border border-[#1a1a1a] rounded-lg p-3 bg-[#0a0a0a] hover:border-[#333] transition-colors">
          <p className="text-sm text-[#ccc] flex-1 mr-3">{r.article_title}</p>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-[10px] text-[#555]">{r.article_source}</span>
            {r.arxiv_url && (
              <a href={r.arxiv_url} target="_blank" rel="noopener noreferrer"
                className="text-[10px] text-[#555] hover:text-white flex items-center gap-0.5">
                ArXiv <ExternalLink size={9} />
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
