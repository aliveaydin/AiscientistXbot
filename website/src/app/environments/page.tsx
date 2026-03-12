import { Metadata } from "next";
import Link from "next/link";
import {
  Joystick,
  ArrowRight,
  Footprints,
  Hand,
  Navigation,
  Cog,
  Bot,
} from "lucide-react";

export const metadata: Metadata = {
  title: "RL Environments",
  description:
    "Reinforcement learning environments designed by Kualia.ai for robotics, locomotion, manipulation, and navigation.",
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

async function getEnvironments() {
  try {
    const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${API}/api/public/environments?limit=50`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return { items: [], total: 0 };
    return res.json();
  } catch {
    return { items: [], total: 0 };
  }
}

export default async function EnvironmentsPage() {
  const data = await getEnvironments();
  const envs = data.items || [];

  return (
    <div className="fade-in mx-auto max-w-6xl px-6 py-16 md:py-24">
      <div className="mb-12">
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-3">
          RL Environments
        </h1>
        <p className="text-[#888] max-w-lg">
          Custom reinforcement learning environments designed for robotics
          research. Each environment defines observation spaces, action spaces,
          reward functions, and training objectives.
        </p>
      </div>

      {/* Category pills */}
      <div className="flex flex-wrap gap-2 mb-8">
        {["All", "Robotics", "Locomotion", "Manipulation", "Navigation", "Custom"].map(
          (cat) => (
            <span
              key={cat}
              className="text-xs font-mono text-[#888] border border-[#222] rounded-full px-3 py-1 hover:border-[#444] hover:text-white transition-colors cursor-default"
            >
              {cat}
            </span>
          )
        )}
      </div>

      {envs.length === 0 ? (
        <div className="border border-[#1a1a1a] rounded-lg p-12 text-center">
          <Joystick className="w-10 h-10 text-[#333] mx-auto mb-4" />
          <p className="text-[#666] mb-1">No environments published yet.</p>
          <p className="text-[#555] text-sm">
            Environments will appear here as they are developed and validated.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {envs.map(
            (env: {
              id: number;
              name: string;
              description?: string;
              category: string;
              difficulty: string;
              observation_space?: string;
              action_space?: string;
              preview_image?: string;
            }) => (
              <Link
                key={env.id}
                href={`/environments/${env.id}`}
                className="group border border-[#1a1a1a] rounded-lg overflow-hidden hover:border-[#333] hover:bg-[#0a0a0a] transition-all"
              >
                {/* Preview */}
                <div className="h-40 bg-[#0a0a0a] border-b border-[#1a1a1a] flex items-center justify-center">
                  {env.preview_image ? (
                    <img
                      src={env.preview_image}
                      alt={env.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-[#333]">
                      {categoryIcons[env.category] || (
                        <Joystick className="w-8 h-8" />
                      )}
                    </div>
                  )}
                </div>

                <div className="p-5">
                  <div className="flex items-center gap-2 mb-3">
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
                  </div>

                  <h2 className="text-base font-semibold text-white mb-2">
                    {env.name}
                  </h2>

                  {env.description && (
                    <p className="text-sm text-[#888] line-clamp-2 leading-relaxed mb-3">
                      {env.description}
                    </p>
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
            )
          )}
        </div>
      )}
    </div>
  );
}
