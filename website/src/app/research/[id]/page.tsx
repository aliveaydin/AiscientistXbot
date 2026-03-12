import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Calendar, BookOpen, Tag, FileText } from "lucide-react";

type Props = { params: Promise<{ id: string }> };

async function getPaper(id: string) {
  try {
    const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${API}/api/public/papers/${id}`, {
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
  const paper = await getPaper(id);
  return {
    title: paper?.title || "Paper",
    description:
      paper?.abstract?.slice(0, 160) || "Research paper from Kualia.ai",
  };
}

export default async function PaperPage({ params }: Props) {
  const { id } = await params;
  const paper = await getPaper(id);

  if (!paper) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-24 text-center">
        <div className="border border-[#1a1a1a] rounded-lg p-12">
          <div className="text-4xl mb-4 opacity-40">404</div>
          <p className="text-[#888] mb-6">Bu makale bulunamadı veya kaldırılmış olabilir.</p>
          <Link
            href="/research"
            className="inline-flex items-center gap-1.5 text-sm text-[#888] hover:text-white transition-colors border border-[#333] rounded-lg px-4 py-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Research
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in mx-auto max-w-3xl px-6 py-16 md:py-24">
      <Link
        href="/research"
        className="inline-flex items-center gap-1.5 text-sm text-[#888] hover:text-white transition-colors mb-8"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        All Papers
      </Link>

      <article>
        <h1 className="text-2xl md:text-3xl font-bold text-white mb-4 leading-tight">
          {paper.title}
        </h1>

        <div className="flex flex-wrap items-center gap-3 mb-6">
          {paper.published_at && (
            <span className="flex items-center gap-1 text-xs text-[#666]">
              <Calendar className="w-3 h-3" />
              {new Date(paper.published_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </span>
          )}
          <span className="text-xs text-[#555]">Kualia.ai Research Lab</span>
          {paper.status && (
            <span
              className={`text-[10px] font-mono uppercase tracking-wider border rounded px-1.5 py-0.5 ${
                paper.status === "published"
                  ? "text-green-500 border-green-500/30"
                  : paper.status === "draft"
                    ? "text-yellow-500 border-yellow-500/30"
                    : "text-[#666] border-[#222]"
              }`}
            >
              {paper.status}
            </span>
          )}
          {paper.version && (
            <span className="text-[10px] font-mono text-[#555] border border-[#222] rounded px-1.5 py-0.5">
              v{paper.version}
            </span>
          )}
        </div>

        {paper.tags && paper.tags.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 mb-6">
            <Tag className="w-3 h-3 text-[#555]" />
            {paper.tags.map((tag: string) => (
              <span
                key={tag}
                className="text-[10px] font-mono text-[#666] border border-[#1a1a1a] rounded px-1.5 py-0.5"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {paper.abstract && (
          <div className="border border-[#1a1a1a] rounded-lg p-5 mb-8 bg-[#0c0c0c]">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="w-3.5 h-3.5 text-[#555]" />
              <span className="text-[10px] font-mono uppercase tracking-wider text-[#555]">
                Abstract
              </span>
            </div>
            <p className="text-sm text-[#999] italic leading-relaxed">
              {paper.abstract}
            </p>
          </div>
        )}

        <div className="line-glow mb-8" />

        {paper.content && (
          <>
            <div className="flex items-center gap-2 mb-6">
              <FileText className="w-4 h-4 text-[#555]" />
              <span className="text-xs font-mono uppercase tracking-wider text-[#555]">
                Full Paper
              </span>
            </div>
            <div
              className="markdown-body text-sm leading-relaxed"
              dangerouslySetInnerHTML={{
                __html: renderMarkdown(paper.content),
              }}
            />
          </>
        )}
      </article>

      <div className="mt-16 pt-8 border-t border-[#1a1a1a]">
        <Link
          href="/research"
          className="inline-flex items-center gap-1.5 text-sm text-[#888] hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Research
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
        result.push(
          `<h${level} class="${sizes[level]} text-white">${text}</h${level}>`
        );
        i++;
        continue;
      }
    }

    if (/^[-*] /.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*] /.test(lines[i])) {
        items.push(
          `<li class="text-[#ccc] ml-1">${inlineFormat(lines[i].replace(/^[-*] /, ""))}</li>`
        );
        i++;
      }
      result.push(
        `<ul class="list-disc list-inside space-y-1 my-4 text-[#ccc]">${items.join("")}</ul>`
      );
      continue;
    }

    if (/^\d+\. /.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        items.push(
          `<li class="text-[#ccc] ml-1">${inlineFormat(lines[i].replace(/^\d+\. /, ""))}</li>`
        );
        i++;
      }
      result.push(
        `<ol class="list-decimal list-inside space-y-1 my-4 text-[#ccc]">${items.join("")}</ol>`
      );
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

    result.push(
      `<p class="text-[#ccc] leading-relaxed my-3">${inlineFormat(line)}</p>`
    );
    i++;
  }

  return result.join("\n");
}

function inlineFormat(text: string): string {
  return text
    .replace(
      /\*\*(.+?)\*\*/g,
      '<strong class="text-white font-semibold">$1</strong>'
    )
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(
      /`([^`]+)`/g,
      '<code class="bg-[#111] border border-[#222] rounded px-1.5 py-0.5 text-[13px] font-mono text-[#e0e0e0]">$1</code>'
    )
    .replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" class="text-blue-400 hover:text-blue-300 underline underline-offset-2" target="_blank" rel="noopener noreferrer">$1</a>'
    );
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
