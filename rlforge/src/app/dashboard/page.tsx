"use client";

import { useEffect, useState } from "react";
import { useUser, useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { Box, Cpu, FlaskConical, Plus, ArrowRight, Loader2, Sparkles, Zap } from "lucide-react";
import { getMyEnvironments, getMyTraining, getMyResearch, syncUser } from "@/lib/api";
import { CreateEnvForm } from "@/components/CreateEnvForm";
import { CreateEnvModal } from "@/components/CreateEnvModal";
import { useCreditInfo } from "@/components/CreditProvider";

interface Stats {
  envCount: number;
  trainingCount: number;
  researchCount: number;
  recentEnvs: any[];
  recentTraining: any[];
  recentResearch: any[];
}

export default function DashboardPage() {
  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  const credit = useCreditInfo();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    if (!isLoaded || !user) return;

    (async () => {
      try {
        const token = await getToken();
        if (!token) return;

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
          recentResearch: researchData.items || [],
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

  const isEmpty =
    stats &&
    stats.envCount === 0 &&
    stats.trainingCount === 0 &&
    stats.researchCount === 0;

  const cards = [
    { label: "Environments", count: stats?.envCount ?? 0, icon: Box, href: "/dashboard/environments", color: "text-blue-400" },
    { label: "Training Runs", count: stats?.trainingCount ?? 0, icon: Cpu, href: "/dashboard/training", color: "text-green-400" },
    { label: "Research Projects", count: stats?.researchCount ?? 0, icon: FlaskConical, href: "/dashboard/research", color: "text-purple-400" },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">
            Welcome back{user?.firstName ? `, ${user.firstName}` : ""}
          </h1>
          <p className="text-sm text-[#888] mt-1">
            Here&apos;s an overview of your work on kualia.ai
          </p>
        </div>
        {!isEmpty && (
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-2 bg-white text-black px-4 py-2 rounded-md text-sm font-medium hover:bg-[#e0e0e0] transition-colors shrink-0"
          >
            <Plus className="w-4 h-4" /> New Environment
          </button>
        )}
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

      {/* Credit & Plan Overview */}
      {!credit.loading && (
        <div className="border border-[#1a1a1a] rounded-lg p-5 bg-[#0a0a0a]">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-yellow-400/10 flex items-center justify-center">
                <Zap className="w-5 h-5 text-yellow-400" />
              </div>
              <div>
                <p className="text-sm text-[#888]">{credit.plan?.display_name || "Free"} Plan</p>
                <p className="text-xl font-bold text-white">${credit.balance.toFixed(2)} <span className="text-sm font-normal text-[#888]">credits</span></p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {credit.monthly_usage && credit.monthly_usage.total_spent > 0 && (
                <div className="text-right">
                  <p className="text-xs text-[#888]">This month</p>
                  <p className="text-sm text-white font-medium">${credit.monthly_usage.total_spent.toFixed(2)} used</p>
                </div>
              )}
              <Link
                href="/pricing"
                className="px-4 py-2 text-sm bg-[#1a1a1a] border border-[#2a2a2a] rounded-md hover:border-[#3a3a3a] text-white transition-colors"
              >
                {credit.plan?.name === "free" ? "Upgrade" : "Manage Plan"}
              </Link>
            </div>
          </div>
          {credit.monthly_usage && Object.keys(credit.monthly_usage.by_operation).length > 0 && (
            <div className="mt-4 pt-4 border-t border-[#1a1a1a] flex flex-wrap gap-x-6 gap-y-2">
              {Object.entries(credit.monthly_usage.by_operation).map(([op, amount]) => (
                <div key={op} className="text-xs">
                  <span className="text-[#888] capitalize">{op.replace(/_/g, " ")}: </span>
                  <span className="text-white font-medium">${(amount as number).toFixed(2)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empty state — inline builder prompt */}
      {isEmpty && (
        <div className="border border-[#1a1a1a] rounded-xl p-8">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-5 h-5 text-[#888]" />
            <h2 className="text-lg font-semibold text-white">
              Create Your First Environment
            </h2>
          </div>
          <p className="text-sm text-[#888] mb-6">
            Describe the RL environment you want in natural language and the AI
            will generate it for you.
          </p>
          <CreateEnvForm />
        </div>
      )}

      {/* Recent environments */}
      {stats && stats.recentEnvs.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white">
              Recent Environments
            </h2>
            <Link
              href="/dashboard/environments"
              className="text-xs text-[#888] hover:text-white transition-colors"
            >
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
                    {env.category} &middot; {env.difficulty} &middot; v
                    {env.version}
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
            <h2 className="text-base font-semibold text-white">
              Recent Training Runs
            </h2>
            <Link
              href="/dashboard/training"
              className="text-xs text-[#888] hover:text-white transition-colors"
            >
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

      {/* Recent research projects */}
      {stats && stats.recentResearch.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white">
              Recent Research Projects
            </h2>
            <Link
              href="/dashboard/research"
              className="text-xs text-[#888] hover:text-white transition-colors"
            >
              View all
            </Link>
          </div>
          <div className="border border-[#1a1a1a] rounded-lg divide-y divide-[#1a1a1a]">
            {stats.recentResearch.map((project: any) => (
              <Link
                key={project.id}
                href={`/research/${project.id}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-[#0a0a0a] transition-colors"
              >
                <div className="min-w-0">
                  <p className="text-sm text-white truncate">{project.title}</p>
                  <p className="text-xs text-[#666] mt-0.5">
                    {project.current_phase || "hypothesis"} &middot; {project.topic || "No topic"}
                  </p>
                </div>
                <StatusBadge status={project.status} />
              </Link>
            ))}
          </div>
        </div>
      )}

      <CreateEnvModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    published: "text-green-500 bg-green-500/10 border-green-500/20",
    completed: "text-green-500 bg-green-500/10 border-green-500/20",
    active: "text-blue-400 bg-blue-400/10 border-blue-400/20",
    running: "text-blue-400 bg-blue-400/10 border-blue-400/20",
    draft: "text-[#888] bg-[#888]/10 border-[#888]/20",
    failed: "text-red-500 bg-red-500/10 border-red-500/20",
    pending: "text-yellow-500 bg-yellow-500/10 border-yellow-500/20",
    paused: "text-yellow-500 bg-yellow-500/10 border-yellow-500/20",
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
