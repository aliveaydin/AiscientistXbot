import Link from "next/link";
import { getResearchProject } from "@/lib/api";
import { ArrowLeft, User, FileText, BookOpen } from "lucide-react";

const agentColors: Record<string, string> = {
  aria: "text-amber-400 border-amber-900",
  marcus: "text-blue-400 border-blue-900",
  elena: "text-emerald-400 border-emerald-900",
};

const agentNames: Record<string, string> = {
  aria: "Prof. Aria",
  marcus: "Dr. Marcus",
  elena: "Dr. Elena",
};

interface Props {
  params: Promise<{ id: string }>;
}

export default async function ResearchProjectPage({ params }: Props) {
  const { id } = await params;
  let project: any = null;
  try {
    project = await getResearchProject(Number(id));
  } catch {
    return (
      <div className="max-w-6xl mx-auto px-6 py-16">
        <p className="text-[#888]">Project not found.</p>
        <Link href="/research" className="text-sm text-[#555] hover:text-white mt-4 inline-block">Back</Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-16 fade-in">
      <Link href="/research" className="text-sm text-[#555] hover:text-white flex items-center gap-1 mb-8">
        <ArrowLeft size={14} /> Back to Research
      </Link>

      {/* Header */}
      <div className="mb-10">
        <h1 className="text-2xl font-bold mb-2">{project.title}</h1>
        {project.topic && (
          <p className="text-sm text-[#888] mb-1">Topic: {project.topic}</p>
        )}
        <div className="flex items-center gap-3 mt-3">
          <span className={`text-xs px-2 py-0.5 rounded-full border ${
            project.status === "completed" ? "border-green-900 text-green-500" :
            project.status === "active" ? "border-blue-900 text-blue-500" :
            "border-[#1a1a1a] text-[#888]"
          }`}>
            {project.status}
          </span>
          <span className="text-xs text-[#555] font-mono">Phase: {project.current_phase}</span>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Chatboard */}
        <div className="lg:col-span-2">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <User size={16} className="text-[#888]" /> Agent Chatboard
          </h2>
          {project.messages?.length === 0 ? (
            <p className="text-[#555] text-sm py-8 text-center">No messages yet. Run the lab to start.</p>
          ) : (
            <div className="space-y-4 max-h-[70vh] overflow-y-auto">
              {project.messages.map((m: any) => {
                const colorClass = agentColors[m.agent_name] || "text-[#888] border-[#1a1a1a]";
                const name = agentNames[m.agent_name] || m.agent_name;
                return (
                  <div key={m.id} className={`border rounded-lg p-4 ${colorClass.split(" ")[1] || "border-[#1a1a1a]"}`}>
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-sm font-medium ${colorClass.split(" ")[0]}`}>{name}</span>
                      <span className="text-[10px] text-[#555] font-mono px-1.5 py-0.5 border border-[#1a1a1a] rounded">
                        {m.phase} R{m.round_num}
                      </span>
                    </div>
                    <div className="text-sm text-[#ccc] leading-relaxed whitespace-pre-wrap">
                      {m.content}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-8">
          {/* Papers */}
          {project.papers?.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <FileText size={14} className="text-[#888]" /> Papers
              </h3>
              <div className="space-y-2">
                {project.papers.map((p: any) => (
                  <div key={p.id} className="border border-[#1a1a1a] rounded-lg p-3">
                    <p className="text-sm font-medium">{p.title}</p>
                    <p className="text-xs text-[#555] mt-1">
                      {p.status} / v{p.version}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* References */}
          {project.references?.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <BookOpen size={14} className="text-[#888]" /> References ({project.references.length})
              </h3>
              <div className="space-y-2">
                {project.references.map((r: any) => (
                  <div key={r.id} className="border border-[#1a1a1a] rounded-lg p-3">
                    <p className="text-sm">{r.article_title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] text-[#555]">{r.article_source}</span>
                      {r.arxiv_url && (
                        <a
                          href={r.arxiv_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[10px] text-[#555] hover:text-white underline"
                        >
                          ArXiv
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Selected Idea */}
          {project.selected_idea && (
            <div>
              <h3 className="text-sm font-semibold mb-3">Selected Research Direction</h3>
              <div className="border border-[#1a1a1a] rounded-lg p-3 text-sm text-[#888] whitespace-pre-wrap">
                {project.selected_idea.substring(0, 500)}{project.selected_idea.length > 500 ? "..." : ""}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
