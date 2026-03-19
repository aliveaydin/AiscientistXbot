"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FlaskConical, Plus, Loader2, X, Sparkles } from "lucide-react";
import { getMyResearch, createResearchProject } from "@/lib/api";

export default function DashboardResearchPage() {
  const { getToken } = useAuth();
  const router = useRouter();
  const [projects, setProjects] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const perPage = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) return;
      const data = await getMyResearch(token, perPage, page * perPage);
      setProjects(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [getToken, page]);

  useEffect(() => { load(); }, [load]);

  const totalPages = Math.ceil(total / perPage);

  const phaseLabels: Record<string, string> = {
    brainstorm: "Brainstorm",
    literature: "Literature Review",
    methodology: "Methodology",
    experiments: "Experiments",
    writing: "Writing",
    review: "Review",
    completed: "Completed",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Research Projects</h1>
          <p className="text-sm text-[#888] mt-1">{total} project{total !== 1 ? "s" : ""} total</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-white text-black px-4 py-2 rounded-md text-sm font-medium hover:bg-[#e0e0e0] transition-colors"
        >
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      {showCreate && (
        <CreateProjectInline
          onClose={() => setShowCreate(false)}
          onCreated={(id) => { router.push(`/research/${id}`); }}
        />
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-6 h-6 text-[#555] animate-spin" />
        </div>
      ) : projects.length === 0 && !showCreate ? (
        <div className="border border-dashed border-[#1a1a1a] rounded-lg p-12 text-center">
          <FlaskConical className="w-10 h-10 text-[#333] mx-auto mb-4" />
          <p className="text-[#888] mb-2">No research projects yet.</p>
          <p className="text-sm text-[#666] mb-6">
            Start an AI-powered research project with the multi-agent research lab.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-2 bg-white text-black px-5 py-2.5 rounded-md text-sm font-medium hover:bg-[#e0e0e0] transition-colors"
          >
            <Plus className="w-4 h-4" /> New Research Project
          </button>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {projects.map((project: any) => (
              <Link
                key={project.id}
                href={`/research/${project.id}`}
                className="block border border-[#1a1a1a] rounded-lg p-5 hover:border-[#333] hover:bg-[#0a0a0a] transition-all group"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-sm font-semibold text-white group-hover:underline">{project.title}</h3>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={project.status} />
                    <span className="text-[10px] text-[#555] font-mono">{phaseLabels[project.current_phase] || project.current_phase}</span>
                  </div>
                </div>
                {project.description && (
                  <p className="text-xs text-[#888] line-clamp-2">{project.description}</p>
                )}
                {project.created_at && (
                  <p className="text-[10px] text-[#555] mt-2">{new Date(project.created_at).toLocaleDateString()}</p>
                )}
              </Link>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className="text-xs text-[#888] hover:text-white disabled:opacity-30 px-3 py-1 border border-[#1a1a1a] rounded">Previous</button>
              <span className="text-xs text-[#666]">{page + 1} / {totalPages}</span>
              <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1} className="text-xs text-[#888] hover:text-white disabled:opacity-30 px-3 py-1 border border-[#1a1a1a] rounded">Next</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function CreateProjectInline({ onClose, onCreated }: { onClose: () => void; onCreated: (id: number) => void }) {
  const { getToken } = useAuth();
  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  async function handleCreate() {
    if (!title.trim()) return;
    setCreating(true); setError("");
    try {
      const token = await getToken();
      const data = await createResearchProject(title, description, topic, token);
      onCreated(data.id);
    } catch (e: any) {
      setError(e.message || "Failed to create project");
    } finally { setCreating(false); }
  }

  return (
    <div className="border border-[#1a1a1a] rounded-lg p-5 bg-[#0a0a0a]">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">New Research Project</h3>
        <button onClick={onClose} className="text-[#555] hover:text-white"><X size={16} /></button>
      </div>
      <div className="space-y-3">
        <div>
          <label className="text-[11px] text-[#555] block mb-1">Title *</label>
          <input value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Reward Shaping for Drone Navigation" className="w-full bg-[#111] border border-[#1a1a1a] rounded px-3 py-2 text-sm text-white outline-none focus:border-[#333]" />
        </div>
        <div>
          <label className="text-[11px] text-[#555] block mb-1">Topic / Keywords</label>
          <input value={topic} onChange={e => setTopic(e.target.value)} placeholder="e.g. reward shaping, target following, drone control" className="w-full bg-[#111] border border-[#1a1a1a] rounded px-3 py-2 text-sm text-white outline-none focus:border-[#333]" />
        </div>
        <div>
          <label className="text-[11px] text-[#555] block mb-1">Description</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)} rows={2} placeholder="Brief description of the research direction..." className="w-full bg-[#111] border border-[#1a1a1a] rounded px-3 py-2 text-sm text-white outline-none focus:border-[#333] resize-none" />
        </div>
        {error && <p className="text-xs text-red-400">{error}</p>}
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-1.5 text-xs text-[#888] hover:text-white border border-[#1a1a1a] rounded">Cancel</button>
          <button onClick={handleCreate} disabled={creating || !title.trim()} className="flex items-center gap-1.5 px-4 py-1.5 text-xs bg-white text-black rounded font-medium hover:bg-[#ddd] disabled:opacity-40">
            {creating ? <><Loader2 size={12} className="animate-spin" /> Creating...</> : <><Sparkles size={12} /> Create & Start</>}
          </button>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    active: "text-blue-400 bg-blue-400/10 border-blue-400/20",
    completed: "text-green-500 bg-green-500/10 border-green-500/20",
    paused: "text-yellow-500 bg-yellow-500/10 border-yellow-500/20",
    failed: "text-red-500 bg-red-500/10 border-red-500/20",
  };
  return (
    <span className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded border ${styles[status] || "text-[#888] bg-[#888]/10 border-[#888]/20"}`}>
      {status}
    </span>
  );
}
