"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import {
  Cpu, Loader2, ChevronRight, ChevronDown,
  BarChart3, ExternalLink,
} from "lucide-react";
import { getMyTraining, getTrainingReport } from "@/lib/api";

interface Run {
  id: number;
  env_id: number;
  env_name: string;
  algorithm: string;
  status: string;
  config: any;
  results: any;
  started_at: string | null;
  completed_at: string | null;
  created_at: string | null;
}

interface EnvGroup {
  env_id: number;
  env_name: string;
  runs: Run[];
  best: Run | null;
}

export default function DashboardTrainingPage() {
  const { getToken } = useAuth();
  const [runs, setRuns] = useState<Run[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const perPage = 50;

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

  useEffect(() => { load(); }, [load]);

  const groups = useMemo<EnvGroup[]>(() => {
    const map = new Map<number, EnvGroup>();
    for (const r of runs) {
      let g = map.get(r.env_id);
      if (!g) {
        g = { env_id: r.env_id, env_name: r.env_name, runs: [], best: null };
        map.set(r.env_id, g);
      }
      g.runs.push(r);
    }
    for (const g of map.values()) {
      const completed = g.runs.filter(r => r.status === "completed" && r.results?.mean_reward != null);
      if (completed.length > 0) {
        g.best = completed.reduce((a, b) =>
          (a.results?.mean_reward ?? -Infinity) >= (b.results?.mean_reward ?? -Infinity) ? a : b
        );
      }
    }
    return Array.from(map.values());
  }, [runs]);

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Training</h1>
        <p className="text-sm text-[#888] mt-1">
          {groups.length} environment{groups.length !== 1 ? "s" : ""} &middot; {total} experiment{total !== 1 ? "s" : ""}
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-6 h-6 text-[#555] animate-spin" />
        </div>
      ) : groups.length === 0 ? (
        <div className="border border-dashed border-[#1a1a1a] rounded-lg p-12 text-center">
          <Cpu className="w-10 h-10 text-[#333] mx-auto mb-4" />
          <p className="text-[#888] mb-2">No experiments yet.</p>
          <p className="text-sm text-[#666]">
            Train an agent on one of your environments to see results here.
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {groups.map(g => (
              <EnvGroupCard key={g.env_id} group={g} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="text-xs text-[#888] hover:text-white disabled:opacity-30 disabled:cursor-not-allowed px-3 py-1 border border-[#1a1a1a] rounded"
              >
                Previous
              </button>
              <span className="text-xs text-[#666]">{page + 1} / {totalPages}</span>
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
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

function EnvGroupCard({ group }: { group: EnvGroup }) {
  const [open, setOpen] = useState(false);
  const completed = group.runs.filter(r => r.status === "completed").length;
  const running = group.runs.filter(r => r.status === "running").length;
  const bestReward = group.best?.results?.mean_reward;
  const bestAlgo = group.best?.algorithm;

  return (
    <div className="border border-[#1a1a1a] rounded-lg overflow-hidden">
      {/* Environment header row */}
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-4 py-3 flex items-center gap-3 hover:bg-[#0a0a0a] transition-colors text-left"
      >
        <ChevronRight
          size={14}
          className={`text-[#555] shrink-0 transition-transform duration-200 ${open ? "rotate-90" : ""}`}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <span className="text-sm text-white font-medium truncate">{group.env_name}</span>
            <span className="text-[10px] text-[#555]">
              {group.runs.length} run{group.runs.length > 1 ? "s" : ""}
            </span>
            {running > 0 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-950 text-blue-400 animate-pulse">
                {running} running
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          {bestReward != null && (
            <div className="text-right">
              <span className="text-[10px] text-[#555] block">Best reward</span>
              <span className="text-xs font-mono text-green-400">{Number(bestReward).toFixed(2)}</span>
            </div>
          )}
          {bestAlgo && (
            <span className="text-[10px] font-mono text-[#888] bg-[#111] border border-[#1a1a1a] px-2 py-0.5 rounded hidden sm:inline">
              {bestAlgo}
            </span>
          )}
          <span className="text-[10px] text-[#555]">
            {completed}/{group.runs.length} completed
          </span>
        </div>
      </button>

      {/* Expanded: individual runs */}
      {open && (
        <div className="border-t border-[#1a1a1a]">
          <div className="px-4 py-2 flex items-center justify-between bg-[#060606]">
            <span className="text-[10px] text-[#555] font-medium uppercase tracking-wider">Experiments</span>
            <Link
              href={`/builder/${group.env_id}`}
              className="flex items-center gap-1 text-[10px] text-[#555] hover:text-white transition-colors"
            >
              Open Builder <ExternalLink size={10} />
            </Link>
          </div>
          <div className="divide-y divide-[#1a1a1a]/50">
            {group.runs.map(run => (
              <RunRow key={run.id} run={run} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function RunRow({ run }: { run: Run }) {
  const [expanded, setExpanded] = useState(false);
  const [curves, setCurves] = useState<any[] | null>(null);
  const [report, setReport] = useState<any>(null);
  const [loadingReport, setLoadingReport] = useState(false);

  const reward = run.results?.mean_reward ?? run.results?.final_reward;
  const successRate = run.results?.success_rate;
  const duration = run.started_at && run.completed_at
    ? formatDuration(new Date(run.completed_at).getTime() - new Date(run.started_at).getTime())
    : "—";

  async function toggle() {
    if (expanded) { setExpanded(false); return; }
    setExpanded(true);
    if (run.status === "completed" && !report) {
      setLoadingReport(true);
      try {
        const r = await getTrainingReport(run.env_id, run.id);
        setReport(r);
        if (r.curve) setCurves(r.curve);
      } catch {}
      finally { setLoadingReport(false); }
    }
  }

  return (
    <div>
      <button
        onClick={toggle}
        className="w-full px-4 py-2.5 flex items-center gap-3 hover:bg-[#0a0a0a] transition-colors text-left"
      >
        <ChevronRight
          size={12}
          className={`text-[#444] shrink-0 transition-transform duration-200 ${expanded ? "rotate-90" : ""}`}
        />
        <span className="text-[11px] font-mono text-[#666] w-10 shrink-0">#{run.id}</span>
        <span className={`text-[10px] px-2 py-0.5 rounded shrink-0 ${
          run.status === "completed" ? "bg-green-950 text-green-400" :
          run.status === "running" ? "bg-blue-950 text-blue-400 animate-pulse" :
          run.status === "failed" ? "bg-red-950 text-red-400" :
          "bg-[#1a1a1a] text-[#888]"
        }`}>
          {run.status}
        </span>
        <span className="text-[11px] font-mono text-[#888]">{run.algorithm}</span>
        <span className="text-[10px] text-[#555]">
          {run.results?.total_timesteps ? formatSteps(run.results.total_timesteps) + " steps" : ""}
        </span>
        <div className="flex-1" />
        <div className="flex items-center gap-3 shrink-0">
          {reward != null && (
            <span className="text-[10px] font-mono text-green-400">R: {Number(reward).toFixed(2)}</span>
          )}
          {successRate != null && (
            <span className="text-[10px] font-mono text-yellow-400">{Math.round(successRate * 100)}%</span>
          )}
          <span className="text-[10px] text-[#555] hidden sm:inline">{duration}</span>
          <span className="text-[10px] text-[#444] hidden md:inline">
            {run.created_at ? new Date(run.created_at).toLocaleDateString() : ""}
          </span>
        </div>
      </button>

      {run.results?.error && (
        <div className="px-10 pb-2">
          <p className="text-[10px] text-red-400 truncate">{run.results.error}</p>
        </div>
      )}

      {expanded && (
        <div className="mx-4 mb-3 border border-[#1a1a1a] rounded-lg overflow-hidden bg-[#060606]">
          {loadingReport ? (
            <div className="flex justify-center py-8">
              <Loader2 size={16} className="animate-spin text-[#555]" />
            </div>
          ) : run.status !== "completed" ? (
            <div className="p-4 text-center text-[10px] text-[#555]">
              {run.status === "running" ? "Training in progress..." : "No report available."}
            </div>
          ) : (
            <>
              {/* Key metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-px bg-[#1a1a1a]">
                <MetricCell label="Mean Reward" value={reward != null ? Number(reward).toFixed(2) : "—"} color="text-green-400" />
                <MetricCell label="Success Rate" value={successRate != null ? `${Math.round(successRate * 100)}%` : "—"} color="text-yellow-400" />
                <MetricCell label="Duration" value={duration} color="text-[#bbb]" />
                <MetricCell label="Timesteps" value={run.results?.total_timesteps ? formatSteps(run.results.total_timesteps) : "—"} color="text-blue-400" />
              </div>

              {/* Training curves */}
              {curves && curves.length > 1 && (
                <div className="p-4 border-t border-[#1a1a1a]">
                  <h4 className="text-[10px] text-[#555] font-medium uppercase tracking-wider mb-3">Training Curves</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <MiniChart data={curves} dataKey="mean_reward" label="Reward" color="#22c55e" />
                    <MiniChart data={curves} dataKey="mean_ep_length" label="Episode Length" color="#3b82f6" />
                    <MiniChart data={curves} dataKey="success_rate" label="Success Rate" color="#eab308" format="percent" />
                    <MiniChart data={curves} dataKey="loss" label="Policy Loss" color="#ef4444" />
                  </div>
                </div>
              )}

              {/* Hyperparameters */}
              {report?.results?.hyperparameters && (
                <div className="p-4 border-t border-[#1a1a1a]">
                  <h4 className="text-[10px] text-[#555] font-medium uppercase tracking-wider mb-2">Hyperparameters</h4>
                  <div className="grid grid-cols-2 gap-x-6 gap-y-0.5">
                    {Object.entries(report.results.hyperparameters).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-[11px] py-0.5">
                        <span className="text-[#555]">{k}</span>
                        <span className="font-mono text-[#888]">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

function MetricCell({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-[#060606] p-3 text-center">
      <p className={`text-sm font-mono font-bold ${color}`}>{value}</p>
      <p className="text-[9px] text-[#555] mt-0.5">{label}</p>
    </div>
  );
}

function MiniChart({ data, dataKey, label, color, format }: {
  data: any[]; dataKey: string; label: string; color: string; format?: string;
}) {
  const values = data.map(d => d[dataKey]).filter(v => v !== undefined && v !== null);
  if (values.length < 2) {
    return (
      <div className="border border-[#1a1a1a] rounded-lg p-3 h-24 flex items-center justify-center">
        <span className="text-[10px] text-[#333]">{label}: N/A</span>
      </div>
    );
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const w = 200, h = 50;
  const points = values.map((v, i) => `${(i / (values.length - 1)) * w},${h - ((v - min) / range) * h}`).join(" ");
  const latest = values[values.length - 1];
  const formatted = format === "percent" ? `${(latest * 100).toFixed(1)}%` : typeof latest === "number" ? latest.toFixed(2) : latest;

  return (
    <div className="border border-[#1a1a1a] rounded-lg p-3">
      <div className="flex justify-between items-center mb-1">
        <span className="text-[10px] text-[#555]">{label}</span>
        <span className="text-xs font-mono" style={{ color }}>{formatted}</span>
      </div>
      <svg width="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="overflow-visible">
        <polyline fill="none" stroke={color} strokeWidth="2" points={points} opacity={0.8} />
        <circle cx={w} cy={h - ((latest - min) / range) * h} r="3" fill={color} />
      </svg>
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

function formatSteps(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`;
  return String(n);
}
