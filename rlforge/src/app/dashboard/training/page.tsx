"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { Cpu, Loader2 } from "lucide-react";
import { getMyTraining } from "@/lib/api";

export default function DashboardTrainingPage() {
  const { getToken } = useAuth();
  const [runs, setRuns] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const perPage = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) return;
      const data = await getMyTraining(token, perPage, page * perPage);
      setRuns(data.items || []);
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
      <div>
        <h1 className="text-xl font-bold text-white">Training Runs</h1>
        <p className="text-sm text-[#888] mt-1">{total} run{total !== 1 ? "s" : ""} total</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-6 h-6 text-[#555] animate-spin" />
        </div>
      ) : runs.length === 0 ? (
        <div className="border border-dashed border-[#1a1a1a] rounded-lg p-12 text-center">
          <Cpu className="w-10 h-10 text-[#333] mx-auto mb-4" />
          <p className="text-[#888] mb-2">No training runs yet.</p>
          <p className="text-sm text-[#666]">
            Train an agent on one of your environments to see results here.
          </p>
        </div>
      ) : (
        <>
          <div className="border border-[#1a1a1a] rounded-lg overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#1a1a1a] text-[#888] text-xs">
                  <th className="text-left px-4 py-3 font-medium">Environment</th>
                  <th className="text-left px-4 py-3 font-medium">Algorithm</th>
                  <th className="text-left px-4 py-3 font-medium">Status</th>
                  <th className="text-left px-4 py-3 font-medium hidden sm:table-cell">Reward</th>
                  <th className="text-left px-4 py-3 font-medium hidden md:table-cell">Duration</th>
                  <th className="text-left px-4 py-3 font-medium hidden md:table-cell">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {runs.map((run: any) => {
                  const reward = run.results?.mean_reward ?? run.results?.final_reward;
                  const duration = run.started_at && run.completed_at
                    ? formatDuration(new Date(run.completed_at).getTime() - new Date(run.started_at).getTime())
                    : "—";
                  return (
                    <tr key={run.id} className="hover:bg-[#0a0a0a] transition-colors">
                      <td className="px-4 py-3">
                        <Link href={`/builder/${run.env_id}`} className="text-sm text-white hover:underline">
                          {run.env_name}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs font-mono text-[#888] bg-[#111] border border-[#1a1a1a] px-2 py-0.5 rounded">
                          {run.algorithm}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <StatusDot status={run.status} />
                      </td>
                      <td className="px-4 py-3 hidden sm:table-cell">
                        <span className="text-xs text-[#888] font-mono">
                          {reward != null ? Number(reward).toFixed(2) : "—"}
                        </span>
                      </td>
                      <td className="px-4 py-3 hidden md:table-cell">
                        <span className="text-xs text-[#888]">{duration}</span>
                      </td>
                      <td className="px-4 py-3 hidden md:table-cell">
                        <span className="text-xs text-[#888]">
                          {run.created_at ? new Date(run.created_at).toLocaleDateString() : "—"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
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

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: "bg-green-500",
    running: "bg-blue-400 animate-pulse",
    failed: "bg-red-500",
    pending: "bg-yellow-500",
  };

  return (
    <div className="flex items-center gap-2">
      <div className={`w-1.5 h-1.5 rounded-full ${colors[status] || "bg-[#666]"}`} />
      <span className="text-xs text-[#888]">{status}</span>
    </div>
  );
}

function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ${seconds % 60}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}
