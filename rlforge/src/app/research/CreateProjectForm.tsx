"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Plus } from "lucide-react";
import { createResearchProject } from "@/lib/api";

export function CreateProjectForm() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleCreate() {
    if (!title.trim()) return;
    setLoading(true);
    try {
      const data = await createResearchProject(title.trim(), description, topic);
      router.push(`/research/${data.id}`);
    } catch {
      setLoading(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 px-4 py-2.5 bg-white text-black text-sm font-medium rounded-lg hover:bg-[#e5e5e5] transition-colors"
      >
        <Plus size={14} /> New Project
      </button>
    );
  }

  return (
    <div className="border border-[#1a1a1a] rounded-xl p-6 space-y-4">
      <div>
        <label className="text-sm text-[#888] mb-1 block">Project Title</label>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Curriculum Learning for Sparse Reward Navigation"
          className="w-full bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-3 py-2 text-sm text-white placeholder:text-[#555] focus:outline-none focus:border-[#333]"
        />
      </div>
      <div>
        <label className="text-sm text-[#888] mb-1 block">Research Topic (optional, for ArXiv search)</label>
        <input
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. reward shaping in multi-agent reinforcement learning"
          className="w-full bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-3 py-2 text-sm text-white placeholder:text-[#555] focus:outline-none focus:border-[#333]"
        />
      </div>
      <div>
        <label className="text-sm text-[#888] mb-1 block">Description (optional)</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Brief description of the research goals..."
          className="w-full h-20 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-3 py-2 text-sm text-white placeholder:text-[#555] resize-none focus:outline-none focus:border-[#333]"
        />
      </div>
      <div className="flex gap-3">
        <button
          onClick={handleCreate}
          disabled={loading || !title.trim()}
          className="flex items-center gap-2 px-4 py-2 bg-white text-black text-sm rounded-lg hover:bg-[#e5e5e5] disabled:opacity-50 transition-colors"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />} Create
        </button>
        <button
          onClick={() => setOpen(false)}
          className="px-4 py-2 text-sm text-[#888] hover:text-white transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
