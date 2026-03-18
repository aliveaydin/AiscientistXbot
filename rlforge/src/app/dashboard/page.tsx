"use client";

import { useEffect, useState } from "react";
import { useUser, useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { Box, Cpu, FlaskConical, Plus, ArrowRight, Loader2 } from "lucide-react";
import { getMyEnvironments, getMyTraining, getMyResearch, syncUser } from "@/lib/api";

interface Stats {
  envCount: number;
  trainingCount: number;
  researchCount: number;
  recentEnvs: any[];
  recentTraining: any[];
}

export default function DashboardPage() {
  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoaded || !user) return;

    (async () => {
      try {
        const token = await getToken();
        if (!token) return;

        // Sync user data with backend on first dashboard visit
        await syncUser(token, {
          email: user.primaryEmailAddress?.emailAddress || "",
          display_name: user.fullName || user.firstName || "",
          avatar_url: user.imageUrl || "",
          username: user.username || "",
        });

        const [envData, trainData, researchData] = await Promise.all([
          getMyEnvironments(token, 5),
          getMyTraining(token, 5),
          getMyResearch(token, 5),
        ]);

        setStats({
          envCount: envData.total || 0,
          trainingCount: trainData.total || 0,
          researchCount: researchData.total || 0,
          recentEnvs: envData.items || [],
          recentTraining: trainData.items || [],
        });
      } catch (err) {
        console.error("Dashboard load error:", err);
      } finally {
        setLoading(false);
      }
    })();
  }, [isLoaded, user, getToken]);

  if (!isLoaded || loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-6 h-6 text-[#555] animate-spin" />
      </div>
    );
  }

  const cards = [
    { label: "Environments", count: stats?.envCount ?? 0, icon: Box, href: "/dashboard/environments", color: "text-blue-400" },
    { label: "Training Runs", count: stats?.trainingCount ?? 0, icon: Cpu, href: "/dashboard/training", color: "text-green-400" },
    { label: "Research Projects", count: stats?.researchCount ?? 0, icon: FlaskConical, href: "/dashboard/research", color: "text-purple-400" },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Welcome back{user?.firstName ? `, ${user.firstName}` : ""}
          </h1>
          <p className="text-sm text-[#888] mt-1">
            Here&apos;s an overview of your work on kualia.ai
          </p>
        </div>
        <Link
          href="/create"
          className="flex items-center gap-2 bg-white text-black px-4 py-2 rounded-md text-sm font-medium hover:bg-[#e0e0e0] transition-colors"
        >
          <Plus className="w-4 h-4" /> New Environment
        </Link>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Link
              key={card.href}
              href={card.href}
              className="border border-[#1a1a1a] rounded-lg p-5 hover:border-[#333] hover:bg-[#0a0a0a] transition-all group"
            >
              <div className="flex items-center justify-between mb-3">
                <Icon className={`w-5 h-5 ${card.color}`} />
                <ArrowRight className="w-4 h-4 text-[#333] group-hover:text-[#666] transition-colors" />
              </div>
              <p className="text-2xl font-bold text-white">{card.count}</p>
              <p className="text-xs text-[#888] mt-1">{card.label}</p>
            </Link>
          );
        })}
      </div>

      {/* Recent environments */}
      {stats && stats.recentEnvs.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white">Recent Environments</h2>
            <Link href="/dashboard/environments" className="text-xs text-[#888] hover:text-white transition-colors">
              View all
            </Link>
          </div>
          <div className="border border-[#1a1a1a] rounded-lg divide-y divide-[#1a1a1a]">
            {stats.recentEnvs.map((env: any) => (
              <Link
                key={env.id}
                href={`/builder/${env.id}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-[#0a0a0a] transition-colors"
              >
                <div className="min-w-0">
                  <p className="text-sm text-white truncate">{env.name}</p>
                  <p className="text-xs text-[#666] mt-0.5">
                    {env.category} &middot; {env.difficulty} &middot; v{env.version}
                  </p>
                </div>
                <StatusBadge status={env.status} />
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Recent training runs */}
      {stats && stats.recentTraining.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white">Recent Training Runs</h2>
            <Link href="/dashboard/training" className="text-xs text-[#888] hover:text-white transition-colors">
              View all
            </Link>
          </div>
          <div className="border border-[#1a1a1a] rounded-lg divide-y divide-[#1a1a1a]">
            {stats.recentTraining.map((run: any) => (
              <Link
                key={run.id}
                href={`/builder/${run.env_id}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-[#0a0a0a] transition-colors"
              >
                <div className="min-w-0">
                  <p className="text-sm text-white truncate">{run.env_name}</p>
                  <p className="text-xs text-[#666] mt-0.5">
                    {run.algorithm} &middot; {run.status}
                  </p>
                </div>
                <StatusBadge status={run.status} />
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {stats && stats.envCount === 0 && stats.trainingCount === 0 && stats.researchCount === 0 && (
        <div className="border border-[#1a1a1a] border-dashed rounded-lg p-12 text-center">
          <Box className="w-10 h-10 text-[#333] mx-auto mb-4" />
          <p className="text-[#888] mb-2">You haven&apos;t created anything yet.</p>
          <p className="text-sm text-[#666] mb-6">
            Start by generating your first RL environment with the AI builder.
          </p>
          <Link
            href="/create"
            className="inline-flex items-center gap-2 bg-white text-black px-5 py-2.5 rounded-md text-sm font-medium hover:bg-[#e0e0e0] transition-colors"
          >
            <Plus className="w-4 h-4" /> Create Environment
          </Link>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    published: "text-green-500 bg-green-500/10 border-green-500/20",
    completed: "text-green-500 bg-green-500/10 border-green-500/20",
    running: "text-blue-400 bg-blue-400/10 border-blue-400/20",
    draft: "text-[#888] bg-[#888]/10 border-[#888]/20",
    failed: "text-red-500 bg-red-500/10 border-red-500/20",
    pending: "text-yellow-500 bg-yellow-500/10 border-yellow-500/20",
  };

  return (
    <span
      className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded border ${
        styles[status] || styles.draft
      }`}
    >
      {status}
    </span>
  );
}
