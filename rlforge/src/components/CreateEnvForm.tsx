"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { Loader2, CheckCircle, Sparkles } from "lucide-react";
import { generateEnv } from "@/lib/api";

const domainOptions = ["auto", "finance", "game", "control", "optimization", "robotics"];
const difficultyOptions = ["easy", "medium", "hard"];

const PROGRESS_STEPS = [
  "Classifying domain...",
  "Generating environment spec & code...",
  "Running 8 validation tests...",
  "Fixing issues (if any)...",
  "Saving environment...",
];

export function CreateEnvForm() {
  const router = useRouter();
  const { getToken } = useAuth();
  const [description, setDescription] = useState("");
  const [domain, setDomain] = useState("auto");
  const [difficulty, setDifficulty] = useState("medium");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [progressIdx, setProgressIdx] = useState(0);
  const progressTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (loading) {
      setProgressIdx(0);
      const delays = [2000, 15000, 10000, 15000, 5000];
      let elapsed = 0;
      let step = 0;
      progressTimer.current = setInterval(() => {
        elapsed += 1000;
        if (step < delays.length - 1 && elapsed >= delays[step]) {
          step++;
          setProgressIdx(step);
          elapsed = 0;
        }
      }, 1000);
    } else {
      if (progressTimer.current) clearInterval(progressTimer.current);
    }
    return () => {
      if (progressTimer.current) clearInterval(progressTimer.current);
    };
  }, [loading]);

  async function handleGenerate() {
    if (!description.trim()) return;
    setLoading(true);
    setError("");

    try {
      const token = await getToken();
      const data = await generateEnv(
        description.trim(),
        domain === "auto" ? undefined : domain,
        difficulty,
        token,
      );
      router.push(`/builder/${data.id}`);
    } catch (e: any) {
      setError(e.message || "Generation failed");
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="A 2D robot arm that must reach a target position. The arm has 3 joints with continuous torque control. Reward based on distance to target minus energy cost."
        className="w-full h-32 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-4 text-sm text-white placeholder:text-[#555] resize-none focus:outline-none focus:border-[#333]"
        disabled={loading}
      />

      <div className="flex flex-wrap items-end gap-4">
        <div>
          <label className="text-xs text-[#888] mb-1.5 block">Domain</label>
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            disabled={loading}
            className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#333] disabled:opacity-50"
          >
            {domainOptions.map((d) => (
              <option key={d} value={d}>
                {d.charAt(0).toUpperCase() + d.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-[#888] mb-1.5 block">Difficulty</label>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            disabled={loading}
            className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#333] disabled:opacity-50"
          >
            {difficultyOptions.map((d) => (
              <option key={d} value={d}>
                {d.charAt(0).toUpperCase() + d.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={handleGenerate}
          disabled={loading || !description.trim()}
          className="flex items-center gap-2 px-5 py-2 bg-white text-black text-sm font-medium rounded-lg hover:bg-[#e5e5e5] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <Loader2 size={14} className="animate-spin" /> Generating...
            </>
          ) : (
            <>
              <Sparkles size={14} /> Generate
            </>
          )}
        </button>
      </div>

      {loading && (
        <div className="border border-[#1a1a1a] rounded-lg p-4 space-y-2">
          {PROGRESS_STEPS.map((step, i) => (
            <div
              key={i}
              className={`flex items-center gap-2 text-xs transition-opacity duration-300 ${
                i < progressIdx
                  ? "text-green-400"
                  : i === progressIdx
                    ? "text-white"
                    : "text-[#333]"
              }`}
            >
              {i < progressIdx ? (
                <CheckCircle size={12} />
              ) : i === progressIdx ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <div className="w-3 h-3 rounded-full border border-[#333]" />
              )}
              {step}
            </div>
          ))}
          <p className="text-[10px] text-[#555] mt-1">
            This may take 30-60 seconds.
          </p>
        </div>
      )}

      {error && (
        <div className="border border-red-900 rounded-lg p-3 text-sm text-red-400">
          {error}
        </div>
      )}
    </div>
  );
}
