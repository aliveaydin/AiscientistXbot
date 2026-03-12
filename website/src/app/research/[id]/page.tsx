import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Calendar } from "lucide-react";

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
    description: paper?.abstract?.slice(0, 160) || "Research paper from Kualia.ai",
  };
}

export default async function PaperPage({ params }: Props) {
  const { id } = await params;
  const paper = await getPaper(id);

  if (!paper) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-24 text-center">
        <p className="text-[#888]">Paper not found.</p>
        <Link href="/research" className="text-sm text-[#666] hover:text-white mt-4 inline-block">
          Back to Research
        </Link>
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

        {paper.published_at && (
          <div className="flex items-center gap-1.5 text-xs text-[#666] mb-6">
            <Calendar className="w-3 h-3" />
            {new Date(paper.published_at).toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
            <span className="ml-3 text-[#555]">Kualia.ai Research Lab</span>
          </div>
        )}

        {paper.abstract && (
          <div className="border-l-2 border-[#333] pl-4 mb-8">
            <p className="text-sm text-[#999] italic leading-relaxed">
              {paper.abstract}
            </p>
          </div>
        )}

        <div className="line-glow mb-8" />

        <div
          className="prose-invert text-sm leading-relaxed space-y-4"
          dangerouslySetInnerHTML={{ __html: formatContent(paper.content) }}
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
    .replace(/`([^`]+)`/g, '<code>$1</code>')
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
