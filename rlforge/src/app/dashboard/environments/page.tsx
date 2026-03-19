"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { Box, Plus, Loader2, ExternalLink, Sparkles } from "lucide-react";
import { getMyEnvironments } from "@/lib/api";
import { CreateEnvForm } from "@/components/CreateEnvForm";
import { CreateEnvModal } from "@/components/CreateEnvModal";

const difficultyColor: Record<string, string> = {
  easy: "text-green-500 border-green-500/20",
  medium: "text-yellow-500 border-yellow-500/20",
  hard: "text-orange-500 border-orange-500/20",
  expert: "text-red-500 border-red-500/20",
};

export default function DashboardEnvironmentsPage() {
  const { getToken } = useAuth();
  const [envs, setEnvs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [modalOpen, setModalOpen] = useState(false);
  const perPage = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) return;
      const data = await getMyEnvironments(token, perPage, page * perPage);
      setEnvs(data.items || []);
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">My Environments</h1>
          <p className="text-sm text-[#888] mt-1">
            {total} environment{total !== 1 ? "s" : ""} total
          </p>
        </div>
        {total > 0 && (
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-2 bg-white text-black px-4 py-2 rounded-md text-sm font-medium hover:bg-[#e0e0e0] transition-colors"
          >
            <Plus className="w-4 h-4" /> New
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-6 h-6 text-[#555] animate-spin" />
        </div>
      ) : envs.length === 0 ? (
        <div className="border border-[#1a1a1a] rounded-xl p-8">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-5 h-5 text-[#888]" />
            <h2 className="text-lg font-semibold text-white">
              Create Your First Environment
            </h2>
          </div>
          <p className="text-sm text-[#888] mb-6">
            Describe what you need and the AI builder will generate a
            Gymnasium-compatible environment for you.
          </p>
          <CreateEnvForm />
        </div>
      ) : (
        <>
          <div className="border border-[#1a1a1a] rounded-lg overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#1a1a1a] text-[#888] text-xs">
                  <th className="text-left px-4 py-3 font-medium">Name</th>
                  <th className="text-left px-4 py-3 font-medium hidden sm:table-cell">Category</th>
                  <th className="text-left px-4 py-3 font-medium hidden sm:table-cell">Difficulty</th>
                  <th className="text-left px-4 py-3 font-medium">Status</th>
                  <th className="text-left px-4 py-3 font-medium hidden lg:table-cell">Training</th>
                  <th className="text-left px-4 py-3 font-medium hidden md:table-cell">Version</th>
                  <th className="text-right px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {envs.map((env: any) => (
                  <tr
                    key={env.id}
                    className="hover:bg-[#0a0a0a] transition-colors"
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/builder/${env.id}`}
                        className="text-sm text-white hover:underline"
                      >
                        {env.name}
                      </Link>
                      {env.description && (
                        <p className="text-xs text-[#666] mt-0.5 truncate max-w-[200px]">
                          {env.description}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3 hidden sm:table-cell">
                      <span className="text-xs text-[#888] font-mono">
                        {env.category || "\u2014"}
                      </span>
                    </td>
                    <td className="px-4 py-3 hidden sm:table-cell">
                      <span
                        className={`text-[10px] font-mono uppercase tracking-wider border rounded px-1.5 py-0.5 ${difficultyColor[env.difficulty] || "text-[#666] border-[#222]"}`}
                      >
                        {env.difficulty}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <StatusDot status={env.status} />
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell">
                      {env.training ? (
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono text-green-400">
                            R: {env.training.mean_reward}
                          </span>
                          {env.training.success_rate != null && (
                            <span className="text-[10px] font-mono text-yellow-400">
                              {Math.round(env.training.success_rate * 100)}%
                            </span>
                          )}
                          <span className="text-[9px] text-[#555]">
                            {env.training.algorithm}
                          </span>
                        </div>
                      ) : (
                        <span className="text-[10px] text-[#444]">
                          Not trained
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <span className="text-xs text-[#888]">
                        v{env.version}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/builder/${env.id}`}
                          className="text-xs text-[#888] hover:text-white transition-colors flex items-center gap-1"
                        >
                          <ExternalLink className="w-3 h-3" /> Open
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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
              <span className="text-xs text-[#666]">
                {page + 1} / {totalPages}
              </span>
              <button
                onClick={() =>
                  setPage((p) => Math.min(totalPages - 1, p + 1))
                }
                disabled={page >= totalPages - 1}
                className="text-xs text-[#888] hover:text-white disabled:opacity-30 disabled:cursor-not-allowed px-3 py-1 border border-[#1a1a1a] rounded"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      <CreateEnvModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    published: "bg-green-500",
    completed: "bg-green-500",
    running: "bg-blue-400",
    draft: "bg-[#666]",
    failed: "bg-red-500",
    pending: "bg-yellow-500",
  };

  return (
    <div className="flex items-center gap-2">
      <div
        className={`w-1.5 h-1.5 rounded-full ${colors[status] || colors.draft}`}
      />
      <span className="text-xs text-[#888]">{status}</span>
    </div>
  );
}
