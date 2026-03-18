"use client";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { Loader2, CheckCircle, XCircle, ArrowRight } from "lucide-react";
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

export default function CreatePage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const [description, setDescription] = useState("");
  const [domain, setDomain] = useState("auto");
  const [difficulty, setDifficulty] = useState("medium");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
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
    return () => { if (progressTimer.current) clearInterval(progressTimer.current); };
  }, [loading]);

  async function handleGenerate() {
    if (!description.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const token = await getToken();
      const data = await generateEnv(
        description.trim(),
        domain === "auto" ? undefined : domain,
        difficulty,
        token,
      );
      setResult(data);
    } catch (e: any) {
      setError(e.message || "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-16 fade-in">
      <h1 className="text-3xl font-bold mb-2">Create Environment</h1>
      <p className="text-[#888] mb-10">Describe the RL environment you want in natural language.</p>

      <div className="space-y-6">
        <div>
          <label className="text-sm text-[#888] mb-2 block">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="A 2D robot arm that must reach a target position. The arm has 3 joints with continuous torque control. Reward based on distance to target minus energy cost."
            className="w-full h-40 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-4 text-sm text-white placeholder:text-[#555] resize-none focus:outline-none focus:border-[#333]"
          />
        </div>

        <div className="flex gap-6">
          <div>
            <label className="text-sm text-[#888] mb-2 block">Domain</label>
            <select
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#333]"
            >
              {domainOptions.map((d) => (
                <option key={d} value={d}>
                  {d.charAt(0).toUpperCase() + d.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-[#888] mb-2 block">Difficulty</label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#333]"
            >
              {difficultyOptions.map((d) => (
                <option key={d} value={d}>
                  {d.charAt(0).toUpperCase() + d.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={loading || !description.trim()}
          className="flex items-center gap-2 px-6 py-3 bg-white text-black text-sm font-medium rounded-lg hover:bg-[#e5e5e5] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" /> Generating...
            </>
          ) : (
            "Generate Environment"
          )}
        </button>

        {loading && (
          <div className="border border-[#1a1a1a] rounded-xl p-5 space-y-3">
            <div className="space-y-2">
              {PROGRESS_STEPS.map((step, i) => (
                <div key={i} className={`flex items-center gap-2 text-xs transition-opacity duration-300 ${
                  i < progressIdx ? "text-green-400" : i === progressIdx ? "text-white" : "text-[#333]"
                }`}>
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
            </div>
            <p className="text-[10px] text-[#555]">This may take 30-60 seconds depending on complexity.</p>
          </div>
        )}

        {error && (
          <div className="border border-red-900 rounded-lg p-4 text-sm text-red-400">{error}</div>
        )}

        {result && (
          <div className="border border-[#1a1a1a] rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">{result.name}</h3>
              <span className="text-xs text-[#555] font-mono">{result.slug}</span>
            </div>

            {result.test_results && (
              <div>
                <p className="text-xs text-[#555] mb-2">
                  Tests: {result.test_results.passed}/{result.test_results.total} passed
                </p>
                <div className="flex flex-wrap gap-2">
                  {result.test_results.tests?.map((t: any) => (
                    <span
                      key={t.name}
                      className={`text-xs px-2 py-1 rounded flex items-center gap-1 ${
                        t.status === "pass" ? "bg-green-950 text-green-400" : "bg-red-950 text-red-400"
                      }`}
                    >
                      {t.status === "pass" ? <CheckCircle size={10} /> : <XCircle size={10} />}
                      {t.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {result.generation_log && (
              <details className="text-xs text-[#555]">
                <summary className="cursor-pointer hover:text-[#888]">Generation log</summary>
                <pre className="mt-2 whitespace-pre-wrap">{result.generation_log}</pre>
              </details>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => router.push(`/builder/${result.id}`)}
                className="flex items-center gap-2 px-4 py-2 bg-white text-black text-sm rounded-lg hover:bg-[#e5e5e5] transition-colors"
              >
                Open in Builder <ArrowRight size={14} />
              </button>
              {result.slug && (
                <button
                  onClick={() => router.push(`/catalog/${result.slug}`)}
                  className="px-4 py-2 border border-[#333] text-sm rounded-lg hover:border-[#555] transition-colors"
                >
                  View Details
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
