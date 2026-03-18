import Link from "next/link";
import { getResearchProjects } from "@/lib/api";
import { FlaskConical, ArrowRight } from "lucide-react";
import { CreateProjectForm } from "./CreateProjectForm";

export default async function ResearchPage() {
  let data = { items: [], total: 0 };
  try {
    data = await getResearchProjects();
  } catch {}

  return (
    <div className="max-w-6xl mx-auto px-6 py-16 fade-in">
      <div className="flex items-start justify-between mb-10">
        <div>
          <h1 className="text-3xl font-bold mb-2">Research Lab</h1>
          <p className="text-[#888]">
            Multi-agent AI research lab. Create projects, let AI agents brainstorm, experiment, and write papers.
          </p>
        </div>
      </div>

      <CreateProjectForm />

      <div className="mt-12">
        <h2 className="text-lg font-semibold mb-6">Projects ({data.total})</h2>
        {data.items.length === 0 ? (
          <p className="text-[#555] text-center py-12">No projects yet. Create one above.</p>
        ) : (
          <div className="space-y-4">
            {data.items.map((p: any) => (
              <Link
                key={p.id}
                href={`/research/${p.id}`}
                className="block border border-[#1a1a1a] rounded-xl p-5 hover:border-[#333] transition-colors group"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold group-hover:text-white">{p.title}</h3>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${
                      p.status === "completed" ? "border-green-900 text-green-500" :
                      p.status === "active" ? "border-blue-900 text-blue-500" :
                      "border-[#1a1a1a] text-[#888]"
                    }`}>
                      {p.status}
                    </span>
                    <span className="text-xs text-[#555] font-mono">{p.current_phase}</span>
                  </div>
                </div>
                {p.topic && <p className="text-sm text-[#888] mb-1">Topic: {p.topic}</p>}
                {p.description && <p className="text-sm text-[#555] line-clamp-1">{p.description}</p>}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
