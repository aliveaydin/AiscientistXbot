import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Eye, Joystick, Trophy, Calendar, Layers, Gauge } from "lucide-react";
import { getPublicEnvironment } from "@/lib/api";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  try {
    const env = await getPublicEnvironment(Number(id));
    return {
      title: env?.name || "Environment",
      description: env?.description?.slice(0, 160) || "RL Environment from kualia.ai",
    };
  } catch {
    return { title: "Environment" };
  }
}

const difficultyConfig: Record<string, { color: string; bg: string }> = {
  easy: { color: "text-green-400", bg: "border-green-500/30 bg-green-500/5" },
  medium: { color: "text-yellow-400", bg: "border-yellow-500/30 bg-yellow-500/5" },
  hard: { color: "text-orange-400", bg: "border-orange-500/30 bg-orange-500/5" },
  expert: { color: "text-red-400", bg: "border-red-500/30 bg-red-500/5" },
};

export default async function EnvironmentDetailPage({ params }: Props) {
  const { id } = await params;
  let env: any = null;
  try {
    env = await getPublicEnvironment(Number(id));
  } catch {}

  if (!env) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-24 text-center">
        <div className="border border-[#1a1a1a] rounded-lg p-12">
          <div className="text-4xl mb-4 opacity-40">404</div>
          <p className="text-[#888] mb-6">This environment was not found or has been unpublished.</p>
          <Link href="/environments" className="inline-flex items-center gap-1.5 text-sm text-[#888] hover:text-white transition-colors border border-[#333] rounded-lg px-4 py-2">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Environments
          </Link>
        </div>
      </div>
    );
  }

  const diff = difficultyConfig[env.difficulty] || { color: "text-[#666]", bg: "border-[#222] bg-transparent" };

  return (
    <div className="fade-in mx-auto max-w-4xl px-6 py-16 md:py-24">
      <Link href="/environments" className="inline-flex items-center gap-1.5 text-sm text-[#888] hover:text-white transition-colors mb-8">
        <ArrowLeft className="w-3.5 h-3.5" /> All Environments
      </Link>

      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-2 mb-4">
          {env.category && (
            <span className="inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-wider text-[#888] border border-[#222] bg-[#111] rounded px-2 py-0.5">
              <Layers className="w-2.5 h-2.5" /> {env.category}
            </span>
          )}
          {env.difficulty && (
            <span className={`inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-wider border rounded px-2 py-0.5 ${diff.color} ${diff.bg}`}>
              <Gauge className="w-2.5 h-2.5" /> {env.difficulty}
            </span>
          )}
          {env.published_at && (
            <span className="flex items-center gap-1 text-xs text-[#666] ml-1">
              <Calendar className="w-3 h-3" />
              {new Date(env.published_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
            </span>
          )}
        </div>

        <h1 className="text-2xl md:text-3xl font-bold text-white mb-3">{env.name}</h1>
        {env.description && <p className="text-[#888] leading-relaxed max-w-2xl">{env.description}</p>}
      </div>

      <div className="h-px bg-gradient-to-r from-[#333] via-[#555] to-[#333] mb-8" />

      {/* Spec Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <SpecCard icon={<Eye className="w-4 h-4" />} label="Observation Space" value={env.observation_space || "Not specified"} accent="border-t-blue-500/40" />
        <SpecCard icon={<Joystick className="w-4 h-4" />} label="Action Space" value={env.action_space || "Not specified"} accent="border-t-purple-500/40" />
        <SpecCard icon={<Trophy className="w-4 h-4" />} label="Reward" value={env.reward_description || "Not specified"} accent="border-t-amber-500/40" />
      </div>

      <div className="mt-16 pt-8 border-t border-[#1a1a1a]">
        <Link href="/environments" className="inline-flex items-center gap-1.5 text-sm text-[#888] hover:text-white transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Environments
        </Link>
      </div>
    </div>
  );
}

function SpecCard({ icon, label, value, accent }: { icon: React.ReactNode; label: string; value: string; accent: string }) {
  return (
    <div className={`border border-[#1a1a1a] border-t-2 ${accent} rounded-lg p-4 bg-[#0c0c0c]`}>
      <div className="flex items-center gap-2 text-[#888] mb-2">
        {icon}
        <span className="text-[10px] font-mono uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-sm text-[#ccc] font-mono leading-relaxed">{value}</p>
    </div>
  );
}
