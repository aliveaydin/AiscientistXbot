"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, User, FileText, BookOpen, Play, Loader2, CheckCircle, ChevronRight } from "lucide-react";
import { getResearchProject, runLabPhase, runLabAll } from "@/lib/api";

const agentColors: Record<string, string> = {
  aria: "text-amber-400 border-amber-900",
  marcus: "text-blue-400 border-blue-900",
  elena: "text-emerald-400 border-emerald-900",
};

const agentNames: Record<string, string> = {
  aria: "Prof. Aria",
  marcus: "Dr. Marcus",
  elena: "Dr. Elena",
};

const phaseLabels: Record<string, string> = {
  brainstorm: "Brainstorm",
  literature: "Literature Review",
  methodology: "Methodology",
  experiments: "Experiments",
  writing: "Writing",
  review: "Review",
  completed: "Completed",
};

export default function ResearchProjectPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [runningAll, setRunningAll] = useState(false);
  const [phaseResult, setPhaseResult] = useState<string | null>(null);
  const chatEnd = useRef<HTMLDivElement>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await getResearchProject(projectId);
      setProject(data);
    } catch {
      setProject(null);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: "smooth" }); }, [project?.messages]);

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  async function handleRunPhase() {
    setRunning(true); setPhaseResult(null);
    try {
      const result = await runLabPhase(projectId);
      setPhaseResult(`Phase "${result.phase}" completed.`);
      await load();
    } catch (e: any) {
      setPhaseResult(`Error: ${e.message}`);
    } finally { setRunning(false); }
  }

  async function handleRunAll() {
    setRunningAll(true); setPhaseResult("Running all phases in background...");
    try {
      await runLabAll(projectId);
      pollRef.current = setInterval(async () => {
        try {
          const data = await getResearchProject(projectId);
          setProject(data);
          if (data.status === "completed" || data.status === "failed") {
            if (pollRef.current) clearInterval(pollRef.current);
            setRunningAll(false);
            setPhaseResult(data.status === "completed" ? "All phases completed!" : "Research failed.");
          }
        } catch {}
      }, 5000);
    } catch (e: any) {
      setPhaseResult(`Error: ${e.message}`);
      setRunningAll(false);
    }
  }

  if (loading) return <div className="max-w-6xl mx-auto px-6 py-16 flex justify-center"><Loader2 className="w-6 h-6 text-[#555] animate-spin" /></div>;
  if (!project) return <div className="max-w-6xl mx-auto px-6 py-16"><p className="text-[#888]">Project not found.</p><Link href="/dashboard/research" className="text-sm text-[#555] hover:text-white mt-4 inline-block">Back</Link></div>;

  const isCompleted = project.status === "completed";
  const isActive = project.status === "active";

  return (
    <div className="max-w-6xl mx-auto px-6 py-16 fade-in">
      <Link href="/dashboard/research" className="text-sm text-[#555] hover:text-white flex items-center gap-1 mb-8">
        <ArrowLeft size={14} /> Back to Research
      </Link>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-2">{project.title}</h1>
        {project.topic && <p className="text-sm text-[#888] mb-1">Topic: {project.topic}</p>}
        <div className="flex items-center gap-3 mt-3">
          <span className={`text-xs px-2 py-0.5 rounded-full border ${
            isCompleted ? "border-green-900 text-green-500" :
            isActive ? "border-blue-900 text-blue-500" :
            "border-[#1a1a1a] text-[#888]"
          }`}>{project.status}</span>
          <span className="text-xs text-[#555] font-mono">Phase: {phaseLabels[project.current_phase] || project.current_phase}</span>
        </div>
      </div>

      {/* Run Controls */}
      {isActive && (
        <div className="flex items-center gap-3 mb-8 p-4 border border-[#1a1a1a] rounded-lg bg-[#0a0a0a]">
          <button
            onClick={handleRunPhase}
            disabled={running || runningAll}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-white text-black rounded-md font-medium hover:bg-[#ddd] disabled:opacity-40 transition-colors"
          >
            {running ? <><Loader2 size={14} className="animate-spin" /> Running Phase...</> : <><ChevronRight size={14} /> Run Next Phase</>}
          </button>
          <button
            onClick={handleRunAll}
            disabled={running || runningAll}
            className="flex items-center gap-2 px-4 py-2 text-sm border border-[#1a1a1a] rounded-md text-[#888] hover:text-white hover:border-[#333] disabled:opacity-40 transition-colors"
          >
            {runningAll ? <><Loader2 size={14} className="animate-spin" /> Running All...</> : <><Play size={14} /> Run All Phases</>}
          </button>
          <span className="text-[11px] text-[#555] ml-2">
            Current: {phaseLabels[project.current_phase] || project.current_phase}
          </span>
        </div>
      )}

      {isCompleted && (
        <div className="flex items-center gap-2 mb-8 p-3 border border-green-900/50 rounded-lg bg-green-950/20">
          <CheckCircle size={14} className="text-green-400" />
          <span className="text-sm text-green-400">Research completed</span>
        </div>
      )}

      {phaseResult && !runningAll && (
        <div className={`mb-6 p-3 rounded-lg text-xs ${phaseResult.startsWith("Error") ? "bg-red-950/30 border border-red-900/50 text-red-400" : "bg-blue-950/30 border border-blue-900/50 text-blue-400"}`}>
          {phaseResult}
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Chatboard */}
        <div className="lg:col-span-2">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <User size={16} className="text-[#888]" /> Agent Chatboard
          </h2>
          {!project.messages || project.messages.length === 0 ? (
            <div className="border border-dashed border-[#1a1a1a] rounded-lg p-8 text-center">
              <p className="text-[#555] text-sm mb-2">No messages yet.</p>
              {isActive && <p className="text-[10px] text-[#444]">Click &quot;Run Next Phase&quot; or &quot;Run All Phases&quot; above to start the AI agents.</p>}
            </div>
          ) : (
            <div className="space-y-4 max-h-[70vh] overflow-y-auto">
              {project.messages.map((m: any) => {
                const colorClass = agentColors[m.agent_name] || "text-[#888] border-[#1a1a1a]";
                const name = agentNames[m.agent_name] || m.agent_name;
                return (
                  <div key={m.id} className={`border rounded-lg p-4 ${colorClass.split(" ")[1] || "border-[#1a1a1a]"}`}>
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-sm font-medium ${colorClass.split(" ")[0]}`}>{name}</span>
                      <span className="text-[10px] text-[#555] font-mono px-1.5 py-0.5 border border-[#1a1a1a] rounded">
                        {m.phase} R{m.round_num}
                      </span>
                    </div>
                    <div className="text-sm text-[#ccc] leading-relaxed whitespace-pre-wrap">{m.content}</div>
                  </div>
                );
              })}
              <div ref={chatEnd} />
            </div>
          )}

          {runningAll && (
            <div className="mt-4 flex items-center gap-2 text-sm text-blue-400">
              <Loader2 size={14} className="animate-spin" />
              <span>Agents are working... This page refreshes automatically.</span>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-8">
          {project.papers?.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <FileText size={14} className="text-[#888]" /> Papers
              </h3>
              <div className="space-y-2">
                {project.papers.map((p: any) => (
                  <div key={p.id} className="border border-[#1a1a1a] rounded-lg p-3">
                    <p className="text-sm font-medium">{p.title}</p>
                    <p className="text-xs text-[#555] mt-1">{p.status} / v{p.version}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {project.references?.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <BookOpen size={14} className="text-[#888]" /> References ({project.references.length})
              </h3>
              <div className="space-y-2">
                {project.references.map((r: any) => (
                  <div key={r.id} className="border border-[#1a1a1a] rounded-lg p-3">
                    <p className="text-sm">{r.article_title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] text-[#555]">{r.article_source}</span>
                      {r.arxiv_url && (
                        <a href={r.arxiv_url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-[#555] hover:text-white underline">ArXiv</a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {project.selected_idea && (
            <div>
              <h3 className="text-sm font-semibold mb-3">Selected Research Direction</h3>
              <div className="border border-[#1a1a1a] rounded-lg p-3 text-sm text-[#888] whitespace-pre-wrap">
                {project.selected_idea.substring(0, 500)}{project.selected_idea.length > 500 ? "..." : ""}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
