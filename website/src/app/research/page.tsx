import { Metadata } from "next";
import Link from "next/link";
import { FileText, Calendar, ArrowRight } from "lucide-react";

export const metadata: Metadata = {
  title: "Research",
  description:
    "Published research papers from Kualia.ai — reinforcement learning, robotics, and embodied intelligence.",
};

async function getPapers() {
  try {
    const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${API}/api/public/papers?limit=50`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return { items: [], total: 0 };
    return res.json();
  } catch {
    return { items: [], total: 0 };
  }
}

export default async function ResearchPage() {
  const data = await getPapers();
  const papers = data.items || [];

  return (
    <div className="fade-in mx-auto max-w-6xl px-6 py-16 md:py-24">
      <div className="mb-12">
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-3">
          Research
        </h1>
        <p className="text-[#888] max-w-lg">
          Papers produced by our autonomous research lab. Each publication goes
          through multi-agent review before release.
        </p>
      </div>

      {papers.length === 0 ? (
        <div className="border border-[#1a1a1a] rounded-lg p-12 text-center">
          <FileText className="w-10 h-10 text-[#333] mx-auto mb-4" />
          <p className="text-[#666] mb-1">No papers published yet.</p>
          <p className="text-[#555] text-sm">
            Papers will appear here once reviewed and finalized in the research lab.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {papers.map(
            (paper: {
              id: number;
              title: string;
              abstract?: string;
              published_at?: string;
            }) => (
              <Link
                key={paper.id}
                href={`/research/${paper.id}`}
                className="group block border border-[#1a1a1a] rounded-lg p-6 hover:border-[#333] hover:bg-[#0a0a0a] transition-all"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h2 className="text-lg font-semibold text-white group-hover:text-white mb-2">
                      {paper.title}
                    </h2>
                    {paper.abstract && (
                      <p className="text-sm text-[#888] line-clamp-2 leading-relaxed">
                        {paper.abstract}
                      </p>
                    )}
                    {paper.published_at && (
                      <div className="flex items-center gap-1.5 mt-3 text-xs text-[#666]">
                        <Calendar className="w-3 h-3" />
                        {new Date(paper.published_at).toLocaleDateString(
                          "en-US",
                          {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          }
                        )}
                      </div>
                    )}
                  </div>
                  <ArrowRight className="w-4 h-4 text-[#555] group-hover:text-white transition-colors flex-shrink-0 mt-1" />
                </div>
              </Link>
            )
          )}
        </div>
      )}
    </div>
  );
}
