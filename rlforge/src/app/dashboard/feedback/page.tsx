"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { usePathname } from "next/navigation";
import {
  MessageSquareText,
  Bug,
  Lightbulb,
  HelpCircle,
  Send,
  CheckCircle,
  Clock,
  ChevronDown,
} from "lucide-react";
import { submitFeedback, getMyFeedback } from "@/lib/api";

const feedbackTypes = [
  { id: "bug", label: "Bug Report", icon: Bug, color: "text-red-400", desc: "Something is broken or not working as expected" },
  { id: "feature", label: "Feature Request", icon: Lightbulb, color: "text-yellow-400", desc: "Suggest a new feature or improvement" },
  { id: "question", label: "Question", icon: HelpCircle, color: "text-blue-400", desc: "Need help understanding something" },
  { id: "general", label: "General", icon: MessageSquareText, color: "text-[#888]", desc: "Any other feedback" },
];

const statusColors: Record<string, string> = {
  new: "bg-blue-500/20 text-blue-400",
  reviewed: "bg-purple-500/20 text-purple-400",
  in_progress: "bg-yellow-500/20 text-yellow-400",
  resolved: "bg-green-500/20 text-green-400",
  wont_fix: "bg-[#333] text-[#888]",
};

interface FeedbackItem {
  id: number;
  type: string;
  title: string;
  body: string;
  status: string;
  priority: string | null;
  ai_category: string | null;
  ai_summary: string | null;
  ai_sentiment: string | null;
  created_at: string;
}

export default function FeedbackPage() {
  const { getToken } = useAuth();
  const pathname = usePathname();
  const [type, setType] = useState("bug");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [myItems, setMyItems] = useState<FeedbackItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    try {
      const token = await getToken();
      if (!token) return;
      const data = await getMyFeedback(token);
      setMyItems(data.items || []);
    } catch { /* ignore */ }
    setLoading(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !body.trim()) return;
    setSubmitting(true);
    try {
      const token = await getToken();
      if (!token) return;
      await submitFeedback(token, {
        type,
        title: title.trim(),
        body: body.trim(),
        page_url: typeof window !== "undefined" ? window.location.origin + pathname : undefined,
      });
      setSubmitted(true);
      setTitle("");
      setBody("");
      setTimeout(() => setSubmitted(false), 4000);
      loadHistory();
    } catch (err) {
      console.error(err);
      alert("Failed to submit feedback. Please try again.");
    }
    setSubmitting(false);
  }

  const selectedType = feedbackTypes.find((t) => t.id === type)!;

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-1">Send Feedback</h1>
      <p className="text-sm text-[#888] mb-8">
        Help us improve kualia.ai — report bugs, request features, or ask questions.
      </p>

      {submitted && (
        <div className="mb-6 flex items-center gap-3 bg-green-500/10 border border-green-500/30 rounded-xl p-4">
          <CheckCircle className="w-5 h-5 text-green-400 shrink-0" />
          <div>
            <p className="text-sm font-medium text-green-400">Feedback submitted!</p>
            <p className="text-xs text-green-400/60">Thank you. Our team will review it shortly.</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Type selector */}
        <div>
          <label className="text-xs text-[#888] uppercase tracking-wider mb-3 block">Type</label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {feedbackTypes.map((ft) => {
              const Icon = ft.icon;
              const active = type === ft.id;
              return (
                <button
                  key={ft.id}
                  type="button"
                  onClick={() => setType(ft.id)}
                  className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border text-center transition-all ${
                    active
                      ? "border-white/20 bg-white/5 text-white"
                      : "border-[#1a1a1a] text-[#666] hover:border-[#333] hover:text-[#aaa]"
                  }`}
                >
                  <Icon className={`w-5 h-5 ${active ? ft.color : ""}`} />
                  <span className="text-xs font-medium">{ft.label}</span>
                </button>
              );
            })}
          </div>
          <p className="text-[11px] text-[#555] mt-2">{selectedType.desc}</p>
        </div>

        {/* Title */}
        <div>
          <label className="text-xs text-[#888] uppercase tracking-wider mb-2 block">Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={
              type === "bug"
                ? "e.g. Training crashes after 50K steps"
                : type === "feature"
                  ? "e.g. Add support for multi-agent environments"
                  : "Brief summary..."
            }
            className="w-full bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-4 py-3 text-sm text-white placeholder:text-[#444] focus:outline-none focus:border-[#333]"
            required
          />
        </div>

        {/* Body */}
        <div>
          <label className="text-xs text-[#888] uppercase tracking-wider mb-2 block">Details</label>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={6}
            placeholder={
              type === "bug"
                ? "What happened? What did you expect to happen? Steps to reproduce..."
                : type === "feature"
                  ? "Describe the feature. How would it help your workflow?"
                  : "Tell us more..."
            }
            className="w-full bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-4 py-3 text-sm text-white placeholder:text-[#444] focus:outline-none focus:border-[#333] resize-none"
            required
          />
        </div>

        <button
          type="submit"
          disabled={submitting || !title.trim() || !body.trim()}
          className="flex items-center gap-2 px-6 py-2.5 bg-white text-black text-sm font-medium rounded-lg hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-4 h-4" />
          {submitting ? "Submitting..." : "Submit Feedback"}
        </button>
      </form>

      {/* History */}
      {!loading && myItems.length > 0 && (
        <div className="mt-12">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center gap-2 text-sm text-[#888] hover:text-white transition-colors"
          >
            <ChevronDown className={`w-4 h-4 transition-transform ${showHistory ? "rotate-180" : ""}`} />
            Your previous feedback ({myItems.length})
          </button>

          {showHistory && (
            <div className="mt-4 space-y-3">
              {myItems.map((item) => (
                <div
                  key={item.id}
                  className="border border-[#1a1a1a] rounded-lg p-4 bg-[#0a0a0a]"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-[10px] uppercase text-[#555] border border-[#222] px-1.5 py-0.5 rounded">
                        {item.type}
                      </span>
                      <h4 className="text-sm font-medium text-white truncate">{item.title}</h4>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full whitespace-nowrap ${statusColors[item.status] || statusColors.new}`}>
                      {item.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="text-xs text-[#888] line-clamp-2">{item.body}</p>
                  <div className="flex items-center gap-3 mt-2 text-[10px] text-[#555]">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                    {item.priority && (
                      <span className="uppercase">{item.priority}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
