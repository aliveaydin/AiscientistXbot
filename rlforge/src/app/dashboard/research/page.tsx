"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { FlaskConical, Plus, Loader2 } from "lucide-react";
import { getMyResearch } from "@/lib/api";

export default function DashboardResearchPage() {
  const { getToken } = useAuth();
  const [projects, setProjects] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
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

  useEffect(() => {
    load();
  }, [load]);

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
        <Link
          href="/research"
          className="flex items-center gap-2 bg-white text-black px-4 py-2 rounded-md text-sm font-medium hover:bg-[#e0e0e0] transition-colors"
        >
          <Plus className="w-4 h-4" /> New Project
        </Link>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-6 h-6 text-[#555] animate-spin" />
        </div>
      ) : projects.length === 0 ? (
        <div className="border border-dashed border-[#1a1a1a] rounded-lg p-12 text-center">
          <FlaskConical className="w-10 h-10 text-[#333] mx-auto mb-4" />
          <p className="text-[#888] mb-2">No research projects yet.</p>
          <p className="text-sm text-[#666] mb-6">
            Start an AI-powered research project with the multi-agent research lab.
          </p>
          <Link
            href="/research"
            className="inline-flex items-center gap-2 bg-white text-black px-5 py-2.5 rounded-md text-sm font-medium hover:bg-[#e0e0e0] transition-colors"
          >
            <Plus className="w-4 h-4" /> New Research Project
          </Link>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {projects.map((project: any) => (
              <Link
                key={project.id}
                href={`/research/${project.id}`}
                className="border border-[#1a1a1a] rounded-lg p-5 hover:border-[#333] hover:bg-[#0a0a0a] transition-all group"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-sm font-semibold text-white group-hover:underline">{project.title}</h3>
                  <StatusBadge status={project.status} />
                </div>
                {project.description && (
                  <p className="text-xs text-[#888] line-clamp-2 mb-3">{project.description}</p>
                )}
                <div className="flex items-center gap-3 text-[10px] text-[#666]">
                  <span>Phase: {phaseLabels[project.current_phase] || project.current_phase}</span>
                  {project.created_at && (
                    <span>{new Date(project.created_at).toLocaleDateString()}</span>
                  )}
                </div>
              </Link>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="text-xs text-[#888] hover:text-white disabled:opacity-30 disabled:cursor-not-allowed px-3 py-1 border border-[#1a1a1a] rounded"
              >
                Previous
              </button>
              <span className="text-xs text-[#666]">{page + 1} / {totalPages}</span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="text-xs text-[#888] hover:text-white disabled:opacity-30 disabled:cursor-not-allowed px-3 py-1 border border-[#1a1a1a] rounded"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
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
    <span
      className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded border ${
        styles[status] || "text-[#888] bg-[#888]/10 border-[#888]/20"
      }`}
    >
      {status}
    </span>
  );
}
