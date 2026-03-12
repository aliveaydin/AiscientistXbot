import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Calendar, Clock } from "lucide-react";

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
    description:
      post?.content?.replace(/[#*`_\n]/g, " ").slice(0, 160) ||
      "Blog post from Kualia.ai",
  };
}

function estimateReadingTime(text: string): number {
  const words = text.replace(/[#*`_\[\]()]/g, " ").split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / 200));
}

export default async function BlogPostPage({ params }: Props) {
  const { id } = await params;
  const post = await getPost(id);

  if (!post) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-24 text-center">
        <div className="border border-[#1a1a1a] rounded-lg p-12">
          <div className="text-4xl mb-4 opacity-40">404</div>
          <p className="text-[#888] mb-6">Bu yazı bulunamadı veya kaldırılmış olabilir.</p>
          <Link
            href="/blog"
            className="inline-flex items-center gap-1.5 text-sm text-[#888] hover:text-white transition-colors border border-[#333] rounded-lg px-4 py-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Blog
          </Link>
        </div>
      </div>
    );
  }

  const readingTime = estimateReadingTime(post.content || "");

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
        <div className="flex flex-wrap items-center gap-3 mb-4">
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
          <span className="flex items-center gap-1 text-xs text-[#666]">
            <Clock className="w-3 h-3" />
            {readingTime} min read
          </span>
        </div>

        <h1 className="text-2xl md:text-3xl font-bold text-white mb-6 leading-tight">
          {post.title}
        </h1>

        <div className="line-glow mb-8" />

        <div
          className="markdown-body text-sm leading-relaxed"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(post.content) }}
        />
      </article>

      <div className="mt-16 pt-8 border-t border-[#1a1a1a]">
        <Link
          href="/blog"
          className="inline-flex items-center gap-1.5 text-sm text-[#888] hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Blog
        </Link>
      </div>
    </div>
  );
}

function renderMarkdown(content: string): string {
  if (!content) return "";

  const lines = content.split("\n");
  const result: string[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("```")) {
      const lang = line.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(escapeHtml(lines[i]));
        i++;
      }
      i++;
      result.push(
        `<div class="my-6 rounded-lg border border-[#1a1a1a] overflow-hidden">` +
          (lang
            ? `<div class="px-4 py-1.5 bg-[#111] border-b border-[#1a1a1a] text-[10px] font-mono uppercase tracking-wider text-[#555]">${escapeHtml(lang)}</div>`
            : "") +
          `<pre class="p-4 overflow-x-auto bg-[#0c0c0c]"><code class="text-[13px] font-mono text-[#ccc] leading-relaxed">${codeLines.join("\n")}</code></pre></div>`
      );
      continue;
    }

    if (line.startsWith("> ")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].startsWith("> ")) {
        quoteLines.push(lines[i].slice(2));
        i++;
      }
      result.push(
        `<blockquote class="border-l-2 border-[#333] pl-4 my-4 text-[#999] italic">${quoteLines.map((l) => inlineFormat(l)).join("<br/>")}</blockquote>`
      );
      continue;
    }

    if (/^#{1,3} /.test(line)) {
      const match = line.match(/^(#{1,3}) (.+)$/);
      if (match) {
        const level = match[1].length;
        const text = inlineFormat(match[2]);
        const sizes: Record<number, string> = {
          1: "text-2xl font-bold mt-10 mb-4",
          2: "text-xl font-bold mt-8 mb-3",
          3: "text-lg font-semibold mt-6 mb-2",
        };
        result.push(`<h${level} class="${sizes[level]} text-white">${text}</h${level}>`);
        i++;
        continue;
      }
    }

    if (/^[-*] /.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*] /.test(lines[i])) {
        items.push(`<li class="text-[#ccc] ml-1">${inlineFormat(lines[i].replace(/^[-*] /, ""))}</li>`);
        i++;
      }
      result.push(`<ul class="list-disc list-inside space-y-1 my-4 text-[#ccc]">${items.join("")}</ul>`);
      continue;
    }

    if (/^\d+\. /.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        items.push(`<li class="text-[#ccc] ml-1">${inlineFormat(lines[i].replace(/^\d+\. /, ""))}</li>`);
        i++;
      }
      result.push(`<ol class="list-decimal list-inside space-y-1 my-4 text-[#ccc]">${items.join("")}</ol>`);
      continue;
    }

    if (/^---+$/.test(line.trim())) {
      result.push(`<hr class="my-8 border-[#1a1a1a]" />`);
      i++;
      continue;
    }

    if (line.trim() === "") {
      i++;
      continue;
    }

    result.push(`<p class="text-[#ccc] leading-relaxed my-3">${inlineFormat(line)}</p>`);
    i++;
  }

  return result.join("\n");
}

function inlineFormat(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, '<code class="bg-[#111] border border-[#222] rounded px-1.5 py-0.5 text-[13px] font-mono text-[#e0e0e0]">$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-400 hover:text-blue-300 underline underline-offset-2" target="_blank" rel="noopener noreferrer">$1</a>');
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
