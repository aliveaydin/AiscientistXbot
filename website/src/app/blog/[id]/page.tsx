import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Calendar } from "lucide-react";

type Props = { params: Promise<{ id: string }> };

async function getPost(id: string) {
  try {
    const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${API}/api/public/blog/${id}`, {
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
  const post = await getPost(id);
  return {
    title: post?.title || "Blog Post",
    description: post?.content?.replace(/[#*`_\n]/g, " ").slice(0, 160) || "Blog post from Kualia.ai",
  };
}

export default async function BlogPostPage({ params }: Props) {
  const { id } = await params;
  const post = await getPost(id);

  if (!post) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-24 text-center">
        <p className="text-[#888]">Post not found.</p>
        <Link href="/blog" className="text-sm text-[#666] hover:text-white mt-4 inline-block">
          Back to Blog
        </Link>
      </div>
    );
  }

  return (
    <div className="fade-in mx-auto max-w-3xl px-6 py-16 md:py-24">
      <Link
        href="/blog"
        className="inline-flex items-center gap-1.5 text-sm text-[#888] hover:text-white transition-colors mb-8"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        All Posts
      </Link>

      <article>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#555] border border-[#222] rounded px-1.5 py-0.5">
            {post.language === "tr" ? "TR" : "EN"}
          </span>
          {post.published_at && (
            <span className="flex items-center gap-1 text-xs text-[#666]">
              <Calendar className="w-3 h-3" />
              {new Date(post.published_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </span>
          )}
        </div>

        <h1 className="text-2xl md:text-3xl font-bold text-white mb-6 leading-tight">
          {post.title}
        </h1>

        <div className="line-glow mb-8" />

        <div
          className="prose-invert text-sm leading-relaxed space-y-4"
          dangerouslySetInnerHTML={{ __html: formatContent(post.content) }}
        />
      </article>
    </div>
  );
}

function formatContent(content: string): string {
  if (!content) return "";
  let html = content
    .replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold text-white mt-8 mb-3">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold text-white mt-10 mb-4">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold text-white mt-10 mb-4">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/^- (.+)$/gm, '<li class="text-[#ccc] ml-4">$1</li>');

  const lines = html.split("\n");
  const result: string[] = [];
  for (const line of lines) {
    if (line.startsWith("<h") || line.startsWith("<li")) {
      result.push(line);
    } else if (line.trim()) {
      result.push(`<p class="text-[#ccc] leading-relaxed">${line}</p>`);
    }
  }
  return result.join("\n");
}
