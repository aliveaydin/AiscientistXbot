import Link from "next/link";
import { getEnvBySlug } from "@/lib/api";
import { ArrowLeft, CheckCircle, XCircle, Play, Download, Code } from "lucide-react";

interface Props {
  params: Promise<{ slug: string }>;
}

export default async function EnvDetailPage({ params }: Props) {
  const { slug } = await params;
  let env: any = null;
  try {
    env = await getEnvBySlug(slug);
  } catch {
    return (
      <div className="max-w-6xl mx-auto px-6 py-16">
        <p className="text-[#888]">Environment not found.</p>
        <Link href="/catalog" className="text-sm text-[#555] hover:text-white mt-4 inline-block">Back to Catalog</Link>
      </div>
    );
  }

  const tests = env.test_results?.tests || [];

  return (
    <div className="max-w-6xl mx-auto px-6 py-16 fade-in">
      <Link href="/catalog" className="text-sm text-[#555] hover:text-white flex items-center gap-1 mb-8">
        <ArrowLeft size={14} /> Back to Catalog
      </Link>

      <div className="flex flex-col lg:flex-row gap-10">
        {/* Left: Specs */}
        <div className="lg:w-1/3 space-y-6">
          <div>
            <h1 className="text-2xl font-bold mb-2">{env.name}</h1>
            <p className="text-sm text-[#888] leading-relaxed">{env.description}</p>
          </div>

          <div className="space-y-3">
            {[
              { label: "Domain", value: env.domain },
              { label: "Difficulty", value: env.difficulty },
              { label: "Observation", value: env.observation_space },
              { label: "Action", value: env.action_space },
              { label: "Reward", value: env.reward_description },
              { label: "Max Steps", value: env.max_steps },
              { label: "Version", value: `v${env.version || 1}` },
            ].map((item) =>
              item.value ? (
                <div key={item.label} className="border border-[#1a1a1a] rounded-lg p-3">
                  <p className="text-xs text-[#555] mb-1">{item.label}</p>
                  <p className="text-sm">{String(item.value)}</p>
                </div>
              ) : null
            )}
          </div>

          {/* Test Results */}
          <div>
            <p className="text-xs text-[#555] mb-2">Tests ({env.test_results?.passed || 0}/{env.test_results?.total || 8})</p>
            <div className="flex flex-wrap gap-2">
              {tests.map((t: any) => (
                <span
                  key={t.name}
                  className={`text-xs px-2 py-1 rounded flex items-center gap-1 ${
                    t.status === "pass"
                      ? "bg-green-950 text-green-400"
                      : "bg-red-950 text-red-400"
                  }`}
                  title={t.detail}
                >
                  {t.status === "pass" ? <CheckCircle size={10} /> : <XCircle size={10} />}
                  {t.name}
                </span>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-2">
            <Link
              href={`/builder/${env.id}`}
              className="flex items-center justify-center gap-2 px-4 py-2.5 bg-white text-black text-sm font-medium rounded-lg hover:bg-[#e5e5e5] transition-colors"
            >
              <Code size={14} /> Open in Builder
            </Link>
          </div>

          {/* API usage */}
          <div>
            <p className="text-xs text-[#555] mb-2">Use via API</p>
            <div className="code-block text-xs">
              <code>
                import kualia{"\n\n"}
                env = kualia.make(<span className="text-[#aaa]">&quot;{env.slug}&quot;</span>){"\n"}
                obs, info = env.reset()
              </code>
            </div>
          </div>
        </div>

        {/* Right: Code */}
        <div className="lg:w-2/3">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm text-[#888]">Environment Code</p>
            <span className="text-xs text-[#555] font-mono">{env.code?.length || 0} chars</span>
          </div>
          <pre className="code-block text-xs leading-relaxed max-h-[70vh] overflow-y-auto whitespace-pre">
            {env.code || "# No code generated"}
          </pre>
        </div>
      </div>
    </div>
  );
}
