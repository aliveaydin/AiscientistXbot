import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Cpu, Eye, Joystick, Trophy, Calendar } from "lucide-react";

type Props = { params: Promise<{ id: string }> };

async function getEnv(id: string) {
  try {
    const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${API}/api/public/environments/${id}`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const env = await getEnv(id);
  return {
    title: env?.name || "Environment",
    description: env?.description?.slice(0, 160) || "RL Environment from Kualia.ai",
  };
}

export default async function EnvironmentDetailPage({ params }: Props) {
  const { id } = await params;
  const env = await getEnv(id);

  if (!env) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-24 text-center">
        <p className="text-[#888]">Environment not found.</p>
        <Link href="/environments" className="text-sm text-[#666] hover:text-white mt-4 inline-block">
          Back to Environments
        </Link>
      </div>
    );
  }

  const difficultyColor: Record<string, string> = {
    easy: "text-green-500 border-green-500/30",
    medium: "text-yellow-500 border-yellow-500/30",
    hard: "text-orange-500 border-orange-500/30",
    expert: "text-red-500 border-red-500/30",
  };

  return (
    <div className="fade-in mx-auto max-w-4xl px-6 py-16 md:py-24">
      <Link
        href="/environments"
        className="inline-flex items-center gap-1.5 text-sm text-[#888] hover:text-white transition-colors mb-8"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        All Environments
      </Link>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#666] border border-[#222] rounded px-1.5 py-0.5">
            {env.category}
          </span>
          <span
            className={`text-[10px] font-mono uppercase tracking-wider border rounded px-1.5 py-0.5 ${
              difficultyColor[env.difficulty] || "text-[#666] border-[#222]"
            }`}
          >
            {env.difficulty}
          </span>
          {env.published_at && (
            <span className="flex items-center gap-1 text-xs text-[#666] ml-2">
              <Calendar className="w-3 h-3" />
              {new Date(env.published_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })}
            </span>
          )}
        </div>

        <h1 className="text-2xl md:text-3xl font-bold text-white mb-3">
          {env.name}
        </h1>

        {env.description && (
          <p className="text-[#888] leading-relaxed max-w-2xl">
            {env.description}
          </p>
        )}
      </div>

      {/* Preview */}
      {env.preview_image && (
        <div className="border border-[#1a1a1a] rounded-lg overflow-hidden mb-8">
          <img src={env.preview_image} alt={env.name} className="w-full" />
        </div>
      )}

      <div className="line-glow mb-8" />

      {/* Specs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <SpecCard
          icon={<Eye className="w-4 h-4" />}
          label="Observation Space"
          value={env.observation_space || "Not specified"}
        />
        <SpecCard
          icon={<Joystick className="w-4 h-4" />}
          label="Action Space"
          value={env.action_space || "Not specified"}
        />
        <SpecCard
          icon={<Trophy className="w-4 h-4" />}
          label="Reward"
          value={env.reward_description || "Not specified"}
        />
      </div>

      {/* Code */}
      {env.code && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[#888]" />
            Environment Code
          </h2>
          <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg overflow-x-auto">
            <pre className="p-5 text-sm text-[#ccc] font-mono leading-relaxed">
              <code>{env.code}</code>
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

function SpecCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="border border-[#1a1a1a] rounded-lg p-4">
      <div className="flex items-center gap-2 text-[#888] mb-2">
        {icon}
        <span className="text-xs uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-sm text-[#ccc]">{value}</p>
    </div>
  );
}
