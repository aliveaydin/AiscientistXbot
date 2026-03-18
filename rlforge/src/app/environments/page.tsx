import { Metadata } from "next";
import Link from "next/link";
import { Joystick, ArrowRight, Bot, Footprints, Hand, Navigation, Cog } from "lucide-react";
import { getPublicEnvironments } from "@/lib/api";

export const metadata: Metadata = {
  title: "RL Environments",
  description: "Reinforcement learning environments designed by kualia.ai for robotics, locomotion, manipulation, and navigation.",
};

const categoryIcons: Record<string, React.ReactNode> = {
  robotics: <Bot className="w-4 h-4" />,
  locomotion: <Footprints className="w-4 h-4" />,
  manipulation: <Hand className="w-4 h-4" />,
  navigation: <Navigation className="w-4 h-4" />,
  custom: <Cog className="w-4 h-4" />,
};

const difficultyColor: Record<string, string> = {
  easy: "text-green-500 border-green-500/30",
  medium: "text-yellow-500 border-yellow-500/30",
  hard: "text-orange-500 border-orange-500/30",
  expert: "text-red-500 border-red-500/30",
};

export default async function EnvironmentsPage() {
  let envs: any[] = [];
  try {
    const data = await getPublicEnvironments(50);
    envs = data.items || [];
  } catch {}

  return (
    <div className="fade-in mx-auto max-w-6xl px-6 py-16 md:py-24">
      <div className="mb-12">
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-3">RL Environments</h1>
        <p className="text-[#888] max-w-lg">
          Custom reinforcement learning environments designed for robotics research.
          Each environment defines observation spaces, action spaces, reward functions, and training objectives.
        </p>
      </div>

      {envs.length === 0 ? (
        <div className="border border-[#1a1a1a] rounded-lg p-12 text-center">
          <Joystick className="w-10 h-10 text-[#333] mx-auto mb-4" />
          <p className="text-[#666] mb-1">No environments published yet.</p>
          <p className="text-[#555] text-sm">Environments will appear here as they are developed and validated.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {envs.map((env: any) => (
            <Link
              key={env.id}
              href={`/environments/${env.id}`}
              className="group border border-[#1a1a1a] rounded-lg overflow-hidden hover:border-[#333] hover:bg-[#0a0a0a] transition-all"
            >
              <div className="h-36 bg-[#0a0a0a] border-b border-[#1a1a1a] flex items-center justify-center">
                <div className="text-[#333]">
                  {categoryIcons[env.category] || <Joystick className="w-8 h-8" />}
                </div>
              </div>
              <div className="p-5">
                <div className="flex items-center gap-2 mb-3">
                  {env.category && (
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#666] border border-[#222] rounded px-1.5 py-0.5">
                      {env.category}
                    </span>
                  )}
                  {env.difficulty && (
                    <span className={`text-[10px] font-mono uppercase tracking-wider border rounded px-1.5 py-0.5 ${difficultyColor[env.difficulty] || "text-[#666] border-[#222]"}`}>
                      {env.difficulty}
                    </span>
                  )}
                </div>
                <h2 className="text-base font-semibold text-white mb-2">{env.name}</h2>
                {env.description && (
                  <p className="text-sm text-[#888] line-clamp-2 leading-relaxed mb-3">{env.description}</p>
                )}
                <div className="flex items-center gap-4 text-xs text-[#666]">
                  {env.observation_space && <span>Obs: {env.observation_space}</span>}
                  {env.action_space && <span>Act: {env.action_space}</span>}
                </div>
                <span className="inline-flex items-center gap-1 text-xs text-[#666] group-hover:text-[#999] mt-3 transition-colors">
                  View details <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
