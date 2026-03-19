import Link from "next/link";
import { getPublicPapers } from "@/lib/api";
import {
  ArrowRight,
  Search,
  Compass,
  FlaskConical,
  BarChart3,
  FileText,
  CheckCircle,
  Brain,
  Cpu,
  Sparkles,
  BookOpen,
  Beaker,
  LineChart,
  GraduationCap,
  Lightbulb,
  Microscope,
} from "lucide-react";

/* ── Static Data ───────────────────────────────── */

const phases = [
  {
    num: "01",
    title: "Research",
    desc: "Sage searches ArXiv for relevant literature, identifies gaps, and builds a knowledge base for the project.",
    icon: <Search size={18} />,
    agent: "Sage",
    color: "amber",
  },
  {
    num: "02",
    title: "Design",
    desc: "Agents collaborate to define hypotheses, propose experiment methodology, and select environment parameters.",
    icon: <Compass size={18} />,
    agent: "Sage + Atlas",
    color: "blue",
  },
  {
    num: "03",
    title: "Experiment",
    desc: "Atlas builds real Gymnasium environments, trains SB3 agents, and collects actual training metrics and curves.",
    icon: <FlaskConical size={18} />,
    agent: "Atlas",
    color: "blue",
  },
  {
    num: "04",
    title: "Analyze",
    desc: "Training results are analyzed — reward curves, convergence rates, success metrics — all from real runs.",
    icon: <BarChart3 size={18} />,
    agent: "Atlas",
    color: "blue",
  },
  {
    num: "05",
    title: "Write",
    desc: "Sage drafts a complete academic paper with introduction, methodology, results, and conclusions backed by real data.",
    icon: <FileText size={18} />,
    agent: "Sage",
    color: "amber",
  },
  {
    num: "06",
    title: "Review",
    desc: "Both agents review the paper for accuracy, consistency with experimental results, and academic rigor.",
    icon: <CheckCircle size={18} />,
    agent: "Sage + Atlas",
    color: "green",
  },
];

const agentCards = [
  {
    name: "Sage",
    role: "Research Strategist",
    color: "amber",
    initials: "SG",
    bgClass: "bg-amber-950",
    textClass: "text-amber-400",
    borderClass: "border-amber-900/40",
    abilities: [
      "ArXiv literature search & analysis",
      "Research gap identification",
      "Hypothesis formulation",
      "Academic paper writing",
      "Citation management",
    ],
  },
  {
    name: "Atlas",
    role: "RL Engineer",
    color: "blue",
    initials: "AT",
    bgClass: "bg-blue-950",
    textClass: "text-blue-400",
    borderClass: "border-blue-900/40",
    abilities: [
      "Gymnasium environment generation",
      "SB3 agent training (PPO, SAC, DQN)",
      "Hyperparameter configuration",
      "Training metric collection",
      "Result analysis & visualization",
    ],
  },
];

/* ── Page ──────────────────────────────────────── */

export default async function ResearchPage() {
  let papers: any[] = [];
  try {
    const data = await getPublicPapers();
    papers = data.items || [];
  } catch {}

  return (
    <div className="fade-in">
      {/* ── Hero ──────────────────────────── */}
      <section className="min-h-[70vh] flex flex-col items-center justify-center px-6 text-center">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-10 h-10 rounded-xl bg-[#0a0a0a] border border-[#1a1a1a] flex items-center justify-center">
            <Brain size={20} className="text-[#888]" />
          </div>
        </div>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.05] max-w-4xl">
          AI Research Lab
        </h1>
        <p className="text-xl md:text-2xl text-[#888] mt-6 max-w-2xl leading-relaxed">
          Automated RL research pipeline — from literature review to published paper
        </p>
        <p className="text-sm text-[#555] mt-4 max-w-xl leading-relaxed">
          Two specialized AI agents collaborate to search literature, design experiments,
          train real RL agents, analyze results, and write complete academic papers.
        </p>
        <div className="flex flex-wrap gap-4 mt-10 justify-center">
          <Link
            href="/sign-up"
            className="inline-flex items-center gap-2 px-7 py-3.5 bg-white text-black text-sm font-medium rounded-lg hover:bg-[#e5e5e5] transition-colors"
          >
            Start Your Research <ArrowRight size={16} />
          </Link>
          <a
            href="#published-papers"
            className="px-7 py-3.5 border border-[#333] text-sm rounded-lg hover:border-[#555] transition-colors text-[#888] hover:text-white"
          >
            View Published Papers
          </a>
        </div>
        <div className="flex flex-wrap gap-3 mt-12 justify-center">
          {[
            { label: "ArXiv Search", icon: <Search size={12} /> },
            { label: "Real Experiments", icon: <FlaskConical size={12} /> },
            { label: "SB3 Training", icon: <Cpu size={12} /> },
            { label: "Gymnasium Envs", icon: <Beaker size={12} /> },
            { label: "Academic Papers", icon: <FileText size={12} /> },
            { label: "Multi-Agent AI", icon: <Brain size={12} /> },
          ].map((c) => (
            <span
              key={c.label}
              className="flex items-center gap-1.5 text-[11px] text-[#555] px-3 py-1.5 border border-[#1a1a1a] rounded-full"
            >
              {c.icon} {c.label}
            </span>
          ))}
        </div>
      </section>

      <div className="line-glow" />

      {/* ── How the Lab Works — Pipeline ─── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <h2 className="text-2xl font-bold mb-3">How the Lab Works</h2>
        <p className="text-[#666] text-sm mb-14 max-w-lg">
          A six-phase automated pipeline turns a research topic into a complete paper backed by real data.
        </p>

        {/* Timeline */}
        <div className="relative">
          <div className="hidden md:block absolute top-6 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#1a1a1a] to-transparent" />
          <div className="grid md:grid-cols-6 gap-6 md:gap-3">
            {phases.map((p, i) => (
              <div key={p.num} className="relative group">
                <div className="flex items-center gap-3 mb-3 md:flex-col md:items-start md:gap-2">
                  <div
                    className={`w-10 h-10 rounded-lg bg-[#0a0a0a] border flex items-center justify-center shrink-0 transition-colors ${
                      p.color === "amber"
                        ? "border-amber-900/30 text-amber-500/60 group-hover:text-amber-400 group-hover:border-amber-800/50"
                        : p.color === "blue"
                          ? "border-blue-900/30 text-blue-500/60 group-hover:text-blue-400 group-hover:border-blue-800/50"
                          : "border-green-900/30 text-green-500/60 group-hover:text-green-400 group-hover:border-green-800/50"
                    }`}
                  >
                    {p.icon}
                  </div>
                  <div>
                    <span className="text-[10px] text-[#333] font-mono">{p.num}</span>
                    <h3 className="font-semibold text-sm">{p.title}</h3>
                  </div>
                </div>
                <p className="text-xs text-[#666] leading-relaxed mb-2">{p.desc}</p>
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                    p.color === "amber"
                      ? "bg-amber-950/40 text-amber-500"
                      : p.color === "blue"
                        ? "bg-blue-950/40 text-blue-500"
                        : "bg-green-950/40 text-green-500"
                  }`}
                >
                  {p.agent}
                </span>
                {i < phases.length - 1 && (
                  <ArrowRight size={12} className="hidden md:block absolute -right-2 top-3.5 text-[#333]" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="line-glow" />

      {/* ── AI Research Agents ────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="text-center mb-14">
          <h2 className="text-2xl font-bold mb-3">AI Research Agents</h2>
          <p className="text-[#666] text-sm max-w-lg mx-auto">
            Two specialized agents work together — one thinks strategically, the other builds and runs experiments.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {agentCards.map((agent) => (
            <div
              key={agent.name}
              className={`border rounded-xl bg-[#0a0a0a] overflow-hidden ${agent.borderClass}`}
            >
              <div className="p-6">
                <div className="flex items-center gap-4 mb-5">
                  <div
                    className={`w-12 h-12 rounded-full ${agent.bgClass} flex items-center justify-center`}
                  >
                    <span className={`text-sm font-bold ${agent.textClass}`}>{agent.initials}</span>
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">{agent.name}</h3>
                    <p className={`text-sm ${agent.textClass}`}>{agent.role}</p>
                  </div>
                </div>
                <ul className="space-y-2.5">
                  {agent.abilities.map((ability) => (
                    <li key={ability} className="flex items-start gap-2.5 text-sm text-[#888]">
                      <CheckCircle size={14} className={`${agent.textClass} mt-0.5 shrink-0`} />
                      {ability}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>

        {/* Agent collaboration mock */}
        <div className="mt-10">
          <MockAgentCollaboration />
        </div>
      </section>

      <div className="line-glow" />

      {/* ── Real Experiments, Real Data ───── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="flex flex-col md:flex-row gap-8 md:gap-12 items-center">
          <div className="flex-1 space-y-4">
            <div className="text-[#555]"><Microscope size={20} /></div>
            <h3 className="text-xl font-bold">Real Experiments, Real Data</h3>
            <p className="text-sm text-[#888] leading-relaxed max-w-md">
              Unlike tools that simulate or hallucinate results, Kualia&apos;s Research Lab generates actual
              Gymnasium environments, trains real Stable Baselines3 agents, and captures authentic
              training metrics — reward curves, convergence rates, episode lengths, and success rates.
            </p>
            <p className="text-sm text-[#666] leading-relaxed max-w-md">
              Every chart in the paper comes from a real training run. Every number is backed by data.
            </p>
          </div>
          <div className="flex-1 w-full">
            <MockRealData />
          </div>
        </div>
      </section>

      <div className="line-glow" />

      {/* ── Paper Generation ──────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="flex flex-col md:flex-row-reverse gap-8 md:gap-12 items-center">
          <div className="flex-1 space-y-4">
            <div className="text-[#555]"><GraduationCap size={20} /></div>
            <h3 className="text-xl font-bold">Complete Academic Papers</h3>
            <p className="text-sm text-[#888] leading-relaxed max-w-md">
              The lab produces full academic papers with proper structure — abstract, introduction,
              related work, methodology, experimental setup, results, discussion, and conclusion.
              All sections reference real experimental data and include proper citations.
            </p>
            <p className="text-sm text-[#666] leading-relaxed max-w-md">
              Papers are generated in markdown with LaTeX math support, ready for further editing
              or direct publication.
            </p>
          </div>
          <div className="flex-1 w-full">
            <MockPaperPreview />
          </div>
        </div>
      </section>

      <div className="line-glow" />

      {/* ── From Builder to Paper ─────────── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="flex flex-col md:flex-row gap-8 md:gap-12 items-center">
          <div className="flex-1 space-y-4">
            <div className="text-[#555]"><Lightbulb size={20} /></div>
            <h3 className="text-xl font-bold">From Builder to Paper</h3>
            <p className="text-sm text-[#888] leading-relaxed max-w-md">
              Already built an environment in the Kualia Builder? Use the &quot;Create Paper&quot; button
              to generate a research paper directly from your existing environment and training data.
            </p>
            <p className="text-sm text-[#666] leading-relaxed max-w-md">
              The Research Lab uses your environment code, training configurations, and experiment
              results as the foundation — then searches literature, contextualizes your work, and
              writes a paper around your real results.
            </p>
            <Link
              href="/create"
              className="inline-flex items-center gap-1.5 text-sm text-white hover:text-[#ccc] transition-colors mt-2"
            >
              Go to Builder <ArrowRight size={14} />
            </Link>
          </div>
          <div className="flex-1 w-full">
            <MockBuilderToPaper />
          </div>
        </div>
      </section>

      <div className="line-glow" />

      {/* ── Published Papers ──────────────── */}
      <section id="published-papers" className="max-w-6xl mx-auto px-6 py-24">
        <h2 className="text-2xl font-bold mb-3">Published Papers</h2>
        <p className="text-[#666] text-sm mb-10 max-w-lg">
          Research papers generated by the lab, each backed by real experiments and training data.
        </p>

        {papers.length === 0 ? (
          <div className="border border-[#1a1a1a] rounded-xl p-12 text-center">
            <BookOpen className="w-10 h-10 text-[#333] mx-auto mb-4" />
            <p className="text-[#666] mb-1">No papers published yet.</p>
            <p className="text-[#555] text-sm">
              Papers will appear here as research projects are completed.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {papers.map((paper: any) => (
              <Link
                key={paper.id}
                href={`/research/${paper.project_id || paper.id}`}
                className="group border border-[#1a1a1a] rounded-xl p-6 hover:border-[#333] hover:bg-[#0a0a0a]/50 transition-all"
              >
                <div className="flex items-start gap-3 mb-3">
                  <FileText size={16} className="text-[#555] mt-0.5 shrink-0" />
                  <h3 className="font-semibold text-sm group-hover:text-white transition-colors line-clamp-2">
                    {paper.title}
                  </h3>
                </div>
                {paper.abstract && (
                  <p className="text-xs text-[#666] line-clamp-3 leading-relaxed mb-3 ml-7">
                    {paper.abstract}
                  </p>
                )}
                <div className="flex items-center gap-3 ml-7">
                  {paper.status && (
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full border ${
                        paper.status === "published"
                          ? "border-green-900 text-green-500"
                          : "border-[#1a1a1a] text-[#666]"
                      }`}
                    >
                      {paper.status}
                    </span>
                  )}
                  {paper.created_at && (
                    <span className="text-[10px] text-[#555]">
                      {new Date(paper.created_at).toLocaleDateString()}
                    </span>
                  )}
                  <span className="ml-auto inline-flex items-center gap-1 text-[10px] text-[#555] group-hover:text-[#888] transition-colors">
                    Read <ArrowRight size={10} />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <div className="line-glow" />

      {/* ── CTA ───────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-24 text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">Start Your Research</h2>
        <p className="text-[#666] mb-10 max-w-md mx-auto">
          Give the lab a topic. Get a paper backed by real experiments.
        </p>
        <div className="flex flex-wrap gap-4 justify-center">
          <Link
            href="/sign-up"
            className="inline-flex items-center gap-2 px-7 py-3.5 bg-white text-black text-sm font-medium rounded-lg hover:bg-[#e5e5e5] transition-colors"
          >
            Create Free Account <ArrowRight size={16} />
          </Link>
          <Link
            href="/environments"
            className="inline-flex items-center gap-2 px-7 py-3.5 border border-[#333] text-sm rounded-lg hover:border-[#555] transition-colors text-[#888] hover:text-white"
          >
            Browse Environments
          </Link>
        </div>
      </section>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   MOCK UI COMPONENTS
   ═══════════════════════════════════════════════════ */

function MockAgentCollaboration() {
  return (
    <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a] overflow-hidden">
      <div className="border-b border-[#1a1a1a] px-4 py-2.5 flex items-center gap-2">
        <Brain size={12} className="text-[#555]" />
        <span className="text-[10px] text-[#888]">Agent Collaboration — Research Phase</span>
        <span className="text-[9px] text-[#555] ml-auto font-mono">Phase 1/6</span>
      </div>

      <div className="p-4 space-y-3" style={{ minHeight: "280px" }}>
        <div className="flex gap-2.5">
          <div className="w-7 h-7 rounded-full bg-amber-950 flex items-center justify-center shrink-0">
            <span className="text-[9px] text-amber-400 font-bold">SG</span>
          </div>
          <div className="bg-[#0a0a0a] border border-amber-900/20 rounded-lg p-3 text-[11px] flex-1">
            <p className="text-[9px] text-amber-400 font-medium mb-1.5">Sage — Research Strategist</p>
            <p className="text-[#bbb] leading-relaxed">
              Found 23 relevant papers on ArXiv for &quot;curriculum learning in sparse-reward navigation.&quot;
              Key gap: no existing work combines automatic curriculum generation with hindsight experience replay
              in continuous-control navigation tasks.
            </p>
          </div>
        </div>

        <div className="flex gap-2.5">
          <div className="w-7 h-7 rounded-full bg-blue-950 flex items-center justify-center shrink-0">
            <span className="text-[9px] text-blue-400 font-bold">AT</span>
          </div>
          <div className="bg-[#0a0a0a] border border-blue-900/20 rounded-lg p-3 text-[11px] flex-1">
            <p className="text-[9px] text-blue-400 font-medium mb-1.5">Atlas — RL Engineer</p>
            <p className="text-[#bbb] leading-relaxed">
              I can build 3 Gymnasium environments with increasing difficulty: point-navigation, obstacle
              navigation, and multi-goal maze. We should compare PPO with and without HER as the baseline,
              then add our curriculum approach.
            </p>
          </div>
        </div>

        <div className="flex gap-2.5">
          <div className="w-7 h-7 rounded-full bg-amber-950 flex items-center justify-center shrink-0">
            <span className="text-[9px] text-amber-400 font-bold">SG</span>
          </div>
          <div className="bg-[#0a0a0a] border border-amber-900/20 rounded-lg p-3 text-[11px] flex-1">
            <p className="text-[9px] text-amber-400 font-medium mb-1.5">Sage — Research Strategist</p>
            <p className="text-[#bbb] leading-relaxed">
              Agreed. The paper structure will be: (1) problem formulation with formal MDP definition,
              (2) the curriculum generation algorithm, (3) experimental evaluation across all 3 domains.
              Moving to Design phase.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 pt-1">
          <div className="flex-1 h-1 rounded-full bg-[#1a1a1a] overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-amber-600 to-blue-600 rounded-full"
              style={{ width: "16%" }}
            />
          </div>
          <span className="text-[9px] text-[#555] shrink-0">Phase 1/6 — Research</span>
        </div>
      </div>
    </div>
  );
}

function MockRealData() {
  const rewardData = [5, 8, 7, 12, 18, 22, 28, 25, 35, 42, 48, 55, 60, 65, 72, 78, 82, 85, 88, 91];
  const baselineData = [5, 7, 6, 9, 11, 13, 14, 16, 18, 20, 22, 24, 25, 27, 28, 30, 31, 32, 33, 34];

  return (
    <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a] overflow-hidden">
      <div className="border-b border-[#1a1a1a] px-4 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <LineChart size={12} className="text-[#555]" />
          <span className="text-[10px] text-[#888]">Real Training Data</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[9px] flex items-center gap-1"><span className="w-2 h-0.5 bg-green-400 inline-block rounded" /> Curriculum</span>
          <span className="text-[9px] flex items-center gap-1 text-[#666]"><span className="w-2 h-0.5 bg-[#555] inline-block rounded" /> Baseline</span>
        </div>
      </div>

      <div className="p-4">
        <DualChart primary={rewardData} secondary={baselineData} label="Mean Episode Reward" primaryValue="91.3" secondaryValue="34.2" />

        <div className="grid grid-cols-3 gap-2 mt-3">
          {[
            { label: "Training Steps", value: "500K", sub: "Real SB3 runs" },
            { label: "Environments", value: "3", sub: "Gymnasium v0.29" },
            { label: "Total Runs", value: "12", sub: "PPO + SAC" },
          ].map((m) => (
            <div key={m.label} className="border border-[#1a1a1a] rounded-lg p-2.5 text-center">
              <p className="text-sm font-mono font-bold text-white">{m.value}</p>
              <p className="text-[9px] text-[#888]">{m.label}</p>
              <p className="text-[8px] text-[#555]">{m.sub}</p>
            </div>
          ))}
        </div>

        <div className="mt-3 border border-green-900/20 bg-green-950/10 rounded-lg px-3 py-2 flex items-start gap-2">
          <CheckCircle size={12} className="text-green-500 mt-0.5 shrink-0" />
          <p className="text-[10px] text-green-400/80 leading-relaxed">
            All data points come from actual Stable Baselines3 training runs on real Gymnasium environments — no simulated or hallucinated results.
          </p>
        </div>
      </div>
    </div>
  );
}

function DualChart({
  primary,
  secondary,
  label,
  primaryValue,
  secondaryValue,
}: {
  primary: number[];
  secondary: number[];
  label: string;
  primaryValue: string;
  secondaryValue: string;
}) {
  const all = [...primary, ...secondary];
  const min = Math.min(...all);
  const max = Math.max(...all);
  const range = max - min || 1;
  const w = 280;
  const h = 80;
  const toPoints = (data: number[]) =>
    data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`).join(" ");

  return (
    <div className="border border-[#1a1a1a] rounded-lg p-3">
      <div className="flex justify-between items-center mb-2">
        <span className="text-[10px] text-[#666]">{label}</span>
        <div className="flex gap-3">
          <span className="text-[10px] font-mono text-green-400">{primaryValue}</span>
          <span className="text-[10px] font-mono text-[#555]">{secondaryValue}</span>
        </div>
      </div>
      <svg width="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="overflow-visible">
        <polyline fill="none" stroke="#555" strokeWidth="1" points={toPoints(secondary)} opacity={0.5} strokeDasharray="3 2" />
        <polyline fill="none" stroke="#22c55e" strokeWidth="1.5" points={toPoints(primary)} opacity={0.8} />
        <circle cx={w} cy={h - ((primary[primary.length - 1] - min) / range) * h} r="2.5" fill="#22c55e" />
      </svg>
      <div className="flex justify-between text-[8px] text-[#444] mt-1 font-mono">
        <span>0</span>
        <span>Steps →</span>
        <span>500K</span>
      </div>
    </div>
  );
}

function MockPaperPreview() {
  return (
    <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a] overflow-hidden">
      <div className="border-b border-[#1a1a1a] px-4 py-2.5 flex items-center gap-2">
        <FileText size={12} className="text-[#555]" />
        <span className="text-[10px] text-[#888]">Generated Paper Preview</span>
        <span className="text-[9px] px-2 py-0.5 bg-green-950 text-green-400 rounded ml-auto">Complete</span>
      </div>

      <div className="p-5 space-y-4" style={{ minHeight: "320px" }}>
        <div className="text-center space-y-2 pb-4 border-b border-[#1a1a1a]">
          <h4 className="text-sm font-bold leading-snug">
            Automatic Curriculum Generation with Hindsight Experience Replay
            for Sparse-Reward Navigation Tasks
          </h4>
          <p className="text-[10px] text-[#666]">Kualia AI Research Lab, 2025</p>
        </div>

        <div>
          <h5 className="text-[10px] font-bold text-[#888] uppercase tracking-wider mb-1.5">Abstract</h5>
          <p className="text-[10px] text-[#666] leading-relaxed">
            We propose ACGHER, a method combining automatic curriculum generation with hindsight
            experience replay for continuous-control navigation in sparse-reward settings. Through
            experiments on three Gymnasium environments of increasing complexity, we demonstrate
            that ACGHER achieves 91.3 mean reward compared to 34.2 for the PPO baseline, while
            requiring 40% fewer training steps to converge...
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <h5 className="text-[10px] font-bold text-[#888] uppercase tracking-wider mb-1.5">Sections</h5>
            <ol className="space-y-1">
              {[
                "Introduction",
                "Related Work",
                "Methodology",
                "Experimental Setup",
                "Results & Discussion",
                "Conclusion",
              ].map((s, i) => (
                <li key={s} className="text-[10px] text-[#555] flex items-center gap-2">
                  <span className="text-[9px] font-mono text-[#444]">{i + 1}.</span> {s}
                </li>
              ))}
            </ol>
          </div>

          <div>
            <h5 className="text-[10px] font-bold text-[#888] uppercase tracking-wider mb-1.5">Data</h5>
            <div className="space-y-1.5">
              {[
                { label: "Environments", value: "3" },
                { label: "Training runs", value: "12" },
                { label: "Total steps", value: "6M" },
                { label: "Citations", value: "23" },
                { label: "Tables", value: "4" },
                { label: "Figures", value: "6" },
              ].map((d) => (
                <div key={d.label} className="flex justify-between text-[10px]">
                  <span className="text-[#555]">{d.label}</span>
                  <span className="font-mono text-[#888]">{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="border border-[#1a1a1a] rounded-lg p-2.5">
          <h5 className="text-[9px] font-bold text-[#666] mb-1">Table 1: Main Results</h5>
          <table className="w-full text-[9px]">
            <thead>
              <tr className="border-b border-[#1a1a1a]">
                <th className="px-2 py-1 text-left text-[#555] font-medium">Method</th>
                <th className="px-2 py-1 text-center text-[#555] font-medium">Reward</th>
                <th className="px-2 py-1 text-center text-[#555] font-medium">Success</th>
                <th className="px-2 py-1 text-center text-[#555] font-medium">Steps</th>
              </tr>
            </thead>
            <tbody>
              {[
                { method: "PPO (baseline)", reward: "34.2", success: "38%", steps: "500K", best: false },
                { method: "PPO + HER", reward: "62.7", success: "71%", steps: "500K", best: false },
                { method: "ACGHER (ours)", reward: "91.3", success: "96%", steps: "300K", best: true },
              ].map((r) => (
                <tr key={r.method} className="border-b border-[#1a1a1a]/30">
                  <td className={`px-2 py-1 ${r.best ? "text-white font-medium" : "text-[#888]"}`}>{r.method}</td>
                  <td className={`px-2 py-1 text-center font-mono ${r.best ? "text-green-400" : "text-[#666]"}`}>{r.reward}</td>
                  <td className={`px-2 py-1 text-center font-mono ${r.best ? "text-green-400" : "text-[#666]"}`}>{r.success}</td>
                  <td className={`px-2 py-1 text-center font-mono ${r.best ? "text-green-400" : "text-[#666]"}`}>{r.steps}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MockBuilderToPaper() {
  return (
    <div className="space-y-3">
      {/* Builder card */}
      <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a] overflow-hidden">
        <div className="border-b border-[#1a1a1a] px-4 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu size={12} className="text-[#555]" />
            <span className="text-[10px] text-[#888]">Environment Builder</span>
            <span className="text-[9px] text-[#555] font-mono">drone-navigation-v3</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[9px] px-2 py-0.5 border border-green-900 text-green-400 rounded">8/8 tests</span>
          </div>
        </div>
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex gap-2">
              {["Obs: Box[18]", "Act: Box[4]", "PPO trained"].map((tag) => (
                <span key={tag} className="text-[9px] px-2 py-0.5 bg-[#1a1a1a] text-[#666] rounded">
                  {tag}
                </span>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2 text-[10px] text-[#555] mb-4">
            <Sparkles size={12} />
            <span>3 training runs completed · Best reward: 78.2</span>
          </div>

          {/* The CTA button */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-4 py-2 bg-white text-black text-[11px] font-medium rounded-lg">
              <FileText size={12} /> Create Paper
            </div>
            <ArrowRight size={14} className="text-[#555]" />
            <span className="text-[10px] text-[#666]">Generates a research paper from this environment</span>
          </div>
        </div>
      </div>

      {/* Arrow connector */}
      <div className="flex justify-center">
        <div className="flex flex-col items-center gap-1 text-[#333]">
          <div className="w-px h-4 bg-gradient-to-b from-[#1a1a1a] to-[#333]" />
          <Sparkles size={14} />
          <div className="w-px h-4 bg-gradient-to-b from-[#333] to-[#1a1a1a]" />
        </div>
      </div>

      {/* Paper output */}
      <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a] p-4">
        <div className="flex items-start gap-3">
          <FileText size={16} className="text-amber-500/60 mt-0.5 shrink-0" />
          <div>
            <h4 className="text-[11px] font-semibold mb-1">
              Obstacle Avoidance with Penalty-Based Reward Shaping for UAV Navigation
            </h4>
            <p className="text-[9px] text-[#666] leading-relaxed">
              An automated paper analyzing your drone-navigation-v3 environment, including training curves
              from 3 PPO runs, convergence analysis, and comparison with baseline configurations.
            </p>
            <div className="flex gap-2 mt-2">
              {["Real data", "3 experiments", "12 citations"].map((tag) => (
                <span key={tag} className="text-[8px] px-1.5 py-0.5 bg-amber-950/30 text-amber-400 rounded">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
