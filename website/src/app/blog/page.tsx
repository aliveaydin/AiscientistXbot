import { Metadata } from "next";
import Link from "next/link";
import { BookOpen, Calendar, ArrowRight } from "lucide-react";

export const metadata: Metadata = {
  title: "Blog",
  description:
    "Technical blog posts and analysis from Kualia.ai — deep dives into AI, robotics, and reinforcement learning.",
};

async function getPosts() {
  try {
    const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${API}/api/public/blog?limit=50`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return { items: [], total: 0 };
    return res.json();
  } catch {
    return { items: [], total: 0 };
  }
}

export default async function BlogPage() {
  const data = await getPosts();
  const posts = data.items || [];

  return (
    <div className="fade-in mx-auto max-w-6xl px-6 py-16 md:py-24">
      <div className="mb-12">
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-3">
          Blog
        </h1>
        <p className="text-[#888] max-w-lg">
          Technical analysis, insights, and commentary on AI research, robotics,
          and reinforcement learning.
        </p>
      </div>

      {posts.length === 0 ? (
        <div className="border border-[#1a1a1a] rounded-lg p-12 text-center">
          <BookOpen className="w-10 h-10 text-[#333] mx-auto mb-4" />
          <p className="text-[#666] mb-1">No blog posts published yet.</p>
          <p className="text-[#555] text-sm">
            Articles will appear here once written and published.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {posts.map(
            (post: {
              id: number;
              title: string;
              content?: string;
              language: string;
              published_at?: string;
            }) => (
              <Link
                key={post.id}
                href={`/blog/${post.id}`}
                className="group border border-[#1a1a1a] rounded-lg p-6 hover:border-[#333] hover:bg-[#0a0a0a] transition-all"
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#555] border border-[#222] rounded px-1.5 py-0.5">
                    {post.language === "tr" ? "TR" : "EN"}
                  </span>
                  {post.published_at && (
                    <span className="flex items-center gap-1 text-xs text-[#666]">
                      <Calendar className="w-3 h-3" />
                      {new Date(post.published_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </span>
                  )}
                </div>
                <h2 className="text-base font-semibold text-white mb-2 group-hover:text-white">
                  {post.title}
                </h2>
                {post.content && (
                  <p className="text-sm text-[#888] line-clamp-2 leading-relaxed">
                    {post.content
                      .replace(/[#*`_]/g, "")
                      .replace(/\n/g, " ")
                      .slice(0, 150)}
                    ...
                  </p>
                )}
                <span className="inline-flex items-center gap-1 text-xs text-[#666] group-hover:text-[#999] mt-3 transition-colors">
                  Read more <ArrowRight className="w-3 h-3" />
                </span>
              </Link>
            )
          )}
        </div>
      )}
    </div>
  );
}
