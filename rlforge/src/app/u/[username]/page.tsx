import { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { User, Box, FlaskConical, ArrowRight, Calendar } from "lucide-react";
import { getPublicProfile } from "@/lib/api";

interface Props {
  params: Promise<{ username: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { username } = await params;
  try {
    const data = await getPublicProfile(username);
    return {
      title: `${data.user.display_name || username} — kualia.ai`,
      description: `${data.user.display_name || username}'s RL environments and research on kualia.ai`,
    };
  } catch {
    return { title: "User not found" };
  }
}

export default async function ProfilePage({ params }: Props) {
  const { username } = await params;

  let data: any;
  try {
    data = await getPublicProfile(username);
  } catch {
    notFound();
  }

  const { user, environments, research_count } = data;

  return (
    <div className="fade-in mx-auto max-w-4xl px-6 py-16 md:py-24">
      {/* Profile header */}
      <div className="flex items-start gap-5 mb-10">
        {user.avatar_url ? (
          <img
            src={user.avatar_url}
            alt={user.display_name || username}
            className="w-20 h-20 rounded-full border border-[#222]"
          />
        ) : (
          <div className="w-20 h-20 rounded-full bg-[#111] border border-[#222] flex items-center justify-center">
            <User className="w-8 h-8 text-[#555]" />
          </div>
        )}
        <div>
          <h1 className="text-2xl font-bold text-white">
            {user.display_name || username}
          </h1>
          <p className="text-sm text-[#888] mt-0.5">@{username}</p>
          {user.bio && <p className="text-sm text-[#aaa] mt-2 max-w-md">{user.bio}</p>}
          <div className="flex items-center gap-4 mt-3 text-xs text-[#666]">
            <span className="flex items-center gap-1">
              <Box className="w-3 h-3" /> {environments.length} environment{environments.length !== 1 ? "s" : ""}
            </span>
            <span className="flex items-center gap-1">
              <FlaskConical className="w-3 h-3" /> {research_count} research project{research_count !== 1 ? "s" : ""}
            </span>
            {user.created_at && (
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" /> Joined {new Date(user.created_at).toLocaleDateString("en-US", { month: "short", year: "numeric" })}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Published environments */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Published Environments</h2>
        {environments.length === 0 ? (
          <div className="border border-[#1a1a1a] rounded-lg p-8 text-center">
            <p className="text-[#666] text-sm">No published environments yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {environments.map((env: any) => (
              <Link
                key={env.id}
                href={`/environments/${env.id}`}
                className="group border border-[#1a1a1a] rounded-lg p-5 hover:border-[#333] hover:bg-[#0a0a0a] transition-all"
              >
                <div className="flex items-center gap-2 mb-2">
                  {env.category && (
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#666] border border-[#222] rounded px-1.5 py-0.5">
                      {env.category}
                    </span>
                  )}
                  {env.difficulty && (
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#666] border border-[#222] rounded px-1.5 py-0.5">
                      {env.difficulty}
                    </span>
                  )}
                </div>
                <h3 className="text-sm font-semibold text-white mb-1 group-hover:underline">{env.name}</h3>
                {env.description && (
                  <p className="text-xs text-[#888] line-clamp-2">{env.description}</p>
                )}
                <span className="inline-flex items-center gap-1 text-xs text-[#666] group-hover:text-[#999] mt-2 transition-colors">
                  View <ArrowRight className="w-3 h-3" />
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
