import { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight, Sparkles, IterationCcw, Play, FlaskConical,
  BarChart3, GitBranch, FileDown, Cpu, Terminal,
  Layers, Zap, Brain, TestTubeDiagonal,
  Send, CheckCircle, XCircle, Bot, Loader2,
  Download, RefreshCw, Eye, Target, Joystick,
  Footprints, Hand, Navigation, Cog, ArrowRightLeft,
  MessageSquare, GitCompare, FileCode2, Shield,
  Activity, Clock, TrendingUp, Package,
} from "lucide-react";
import { getPublicEnvironments } from "@/lib/api";

export const metadata: Metadata = {
  title: "AI-Powered RL Environment Generation | Kualia",
  description:
    "Design, generate, and iterate on custom Gymnasium reinforcement learning environments with AI. Train agents, run experiments, and export results.",
};

const categoryIcons: Record<string, React.ReactNode> = {
  robotics: <Bot className="w-4 h-4" />,
  locomotion: <Footprints className="w-4 h-4" />,
  manipulation: <Hand className="w-4 h-4" />,
  navigation: <Navigation className="w-4 h-4" />,
  custom: <Cog className="w-4 h-4" />,
};

const difficultyColor: Record<string, string> = {
  easy: "text-green-500 border-green-500/30",
  medium: "text-yellow-500 border-yellow-500/30",
  hard: "text-orange-500 border-orange-500/30",
  expert: "text-red-500 border-red-500/30",
};

export default async function EnvironmentsPage() {
  let envs: any[] = [];
  try {
    const data = await getPublicEnvironments(50);
    envs = data.items || [];
  } catch {}

  return (
    <div className="fade-in">
      {/* ── Hero ──────────────────────────────────── */}
      <section className="min-h-[80vh] flex flex-col items-center justify-center px-6 text-center pt-20 pb-16">
        <div className="flex items-center gap-2 mb-6">
          <span className="text-[11px] text-[#555] px-3 py-1.5 border border-[#1a1a1a] rounded-full flex items-center gap-1.5">
            <Sparkles size={12} className="text-blue-400" />
            AI-Generated Gymnasium Environments
          </span>
        </div>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.05] max-w-5xl">
          RL Environment Generation
          <br />
          <span className="text-[#555]">powered by AI.</span>
        </h1>
        <p className="text-xl md:text-2xl text-[#888] mt-6 max-w-2xl leading-relaxed">
          Describe what you need. Get validated Gymnasium code.
          <br />
          Train agents. Track experiments. Export results.
        </p>
        <div className="flex flex-wrap gap-4 mt-10 justify-center">
          <Link
            href="/create"
            className="px-7 py-3.5 bg-white text-black text-sm font-medium rounded-lg hover:bg-[#e5e5e5] transition-colors inline-flex items-center gap-2"
          >
            Start Building <ArrowRight size={16} />
          </Link>
          <Link
            href="#templates"
            className="px-7 py-3.5 border border-[#333] text-sm rounded-lg hover:border-[#555] transition-colors text-[#888] hover:text-white"
          >
            View Templates
          </Link>
        </div>

        <div className="flex flex-wrap gap-3 mt-12 justify-center">
          {[
            { label: "Gymnasium v0.29+", icon: <Layers size={12} /> },
            { label: "8 Automated Tests", icon: <TestTubeDiagonal size={12} /> },
            { label: "PPO / SAC / DQN", icon: <Zap size={12} /> },
            { label: "PDF Reports", icon: <FileDown size={12} /> },
            { label: "Version Control", icon: <GitBranch size={12} /> },
            { label: "ZIP & GitHub Export", icon: <Package size={12} /> },
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

      {/* ── What is an RL Environment? ────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            What is an RL Environment?
          </h2>
          <p className="text-[#888] max-w-2xl mx-auto leading-relaxed">
            A reinforcement learning environment defines the world an agent
            interacts with. The agent observes a state, takes an action, and
            receives a reward — learning to maximize cumulative reward over time.
          </p>
        </div>

        <div className="flex flex-col md:flex-row gap-12 items-center">
          <div className="flex-1 w-full">
            <RLLoopDiagram />
          </div>
          <div className="flex-1 space-y-6">
            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-lg bg-blue-950/40 border border-blue-900/30 flex items-center justify-center shrink-0">
                <Eye size={18} className="text-blue-400" />
              </div>
              <div>
                <h4 className="font-semibold text-sm mb-1">Observation</h4>
                <p className="text-[#888] text-sm leading-relaxed">
                  What the agent sees — sensor data, positions, velocities, or any
                  state representation the environment exposes.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-lg bg-purple-950/40 border border-purple-900/30 flex items-center justify-center shrink-0">
                <Zap size={18} className="text-purple-400" />
              </div>
              <div>
                <h4 className="font-semibold text-sm mb-1">Action</h4>
                <p className="text-[#888] text-sm leading-relaxed">
                  What the agent does — discrete choices or continuous control
                  signals that affect the environment state.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-lg bg-yellow-950/40 border border-yellow-900/30 flex items-center justify-center shrink-0">
                <Target size={18} className="text-yellow-400" />
              </div>
              <div>
                <h4 className="font-semibold text-sm mb-1">Reward</h4>
                <p className="text-[#888] text-sm leading-relaxed">
                  The feedback signal — a scalar value that tells the agent how
                  good its action was. The agent learns to maximize total reward.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="line-glow" />

      {/* ── How It Works ─────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">How It Works</h2>
          <p className="text-[#888] max-w-2xl mx-auto leading-relaxed">
            From natural language to a trained agent in five steps. No
            boilerplate. No setup headaches.
          </p>
        </div>

        <div className="relative">
          <div className="hidden md:block absolute top-8 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#1a1a1a] to-transparent" />
          <div className="grid md:grid-cols-5 gap-8 md:gap-4">
            {[
              {
                num: "01",
                title: "Describe",
                desc: "Tell the AI what environment you need in plain English. Specify observations, actions, and goals.",
                icon: <MessageSquare size={18} />,
                color: "text-blue-400",
              },
              {
                num: "02",
                title: "Generate",
                desc: "The Architect Agent writes Gymnasium-compatible Python code, validated by 8 automated tests.",
                icon: <Cpu size={18} />,
                color: "text-green-400",
              },
              {
                num: "03",
                title: "Test",
                desc: "Syntax, imports, reset, step, observation space, action space, reward sanity, and determinism — all checked.",
                icon: <Shield size={18} />,
                color: "text-yellow-400",
              },
              {
                num: "04",
                title: "Iterate",
                desc: "Chat with the AI to refine reward functions, dynamics, and observations. Every change versioned.",
                icon: <IterationCcw size={18} />,
                color: "text-purple-400",
              },
              {
                num: "05",
                title: "Train",
                desc: "One-click agent training with PPO, SAC, or DQN. Live metrics, reward curves, and experiment reports.",
                icon: <Play size={18} />,
                color: "text-red-400",
              },
            ].map((s, i) => (
              <div key={s.num} className="relative group">
                <div className="flex items-center gap-3 mb-3 md:flex-col md:items-start md:gap-2">
                  <div className="w-12 h-12 rounded-xl bg-[#0a0a0a] border border-[#1a1a1a] flex items-center justify-center text-[#555] group-hover:text-white group-hover:border-[#333] transition-colors shrink-0">
                    <span className={s.color}>{s.icon}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-[#333] font-mono">
                      {s.num}
                    </span>
                    <h3 className="font-semibold text-sm">{s.title}</h3>
                  </div>
                </div>
                <p className="text-xs text-[#666] leading-relaxed">{s.desc}</p>
                {i < 4 && (
                  <ArrowRight
                    size={14}
                    className="hidden md:block absolute -right-2 top-4 text-[#333]"
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Mock: Builder preview */}
        <div className="mt-20">
          <MockBuilderChat />
        </div>
      </section>

      <div className="line-glow" />

      {/* ── Builder Features ─────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Builder Features
          </h2>
          <p className="text-[#888] max-w-2xl mx-auto leading-relaxed">
            Every tool you need to design production-quality RL environments,
            built into one seamless workflow.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <FeatureCard
            icon={<GitBranch size={20} className="text-blue-400" />}
            title="Full Version Control"
            description="Every iteration creates a new version. Browse history, compare diffs, and roll back to any previous state. Your environment has a complete audit trail."
          >
            <MockVersionHistory />
          </FeatureCard>

          <FeatureCard
            icon={<TestTubeDiagonal size={20} className="text-green-400" />}
            title="8 Automated Tests"
            description="Each generation runs through syntax, import, reset, step, observation space, action space, reward sanity, and determinism checks. Catch errors before training."
          >
            <MockTestGrid />
          </FeatureCard>

          <FeatureCard
            icon={<IterationCcw size={20} className="text-purple-400" />}
            title="Chat-Based Iteration"
            description='Refine your environment through conversation. Say "add wind noise" or "change the reward to be sparse" and the AI rewrites the code while preserving your existing logic.'
          >
            <MockChatIteration />
          </FeatureCard>

          <FeatureCard
            icon={<Download size={20} className="text-yellow-400" />}
            title="Export Options"
            description="Download your environment as a ZIP file with all dependencies, or push directly to a GitHub repository. Ready for local development or CI/CD pipelines."
          >
            <MockExportOptions />
          </FeatureCard>
        </div>
      </section>

      <div className="line-glow" />

      {/* ── Training & Experiments ────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Training & Experiments
          </h2>
          <p className="text-[#888] max-w-2xl mx-auto leading-relaxed">
            Train agents directly in the platform. Compare runs across
            environment versions. Export detailed reports.
          </p>
        </div>

        <div className="flex flex-col md:flex-row gap-8 md:gap-12 items-center mb-20">
          <div className="flex-1 space-y-5">
            <div className="flex items-center gap-3 mb-4">
              {[
                { label: "PPO", color: "border-blue-900/50 text-blue-400" },
                { label: "SAC", color: "border-green-900/50 text-green-400" },
                { label: "DQN", color: "border-purple-900/50 text-purple-400" },
              ].map((a) => (
                <span
                  key={a.label}
                  className={`text-xs font-mono px-3 py-1 border rounded-lg ${a.color}`}
                >
                  {a.label}
                </span>
              ))}
            </div>
            <h3 className="text-xl font-bold">
              One-Click Agent Training
            </h3>
            <p className="text-sm text-[#888] leading-relaxed max-w-md">
              Choose an algorithm, set hyperparameters, and hit train.
              Stable Baselines3 handles the rest. Watch live progress with
              real-time reward curves, episode length, success rate, and
              policy loss.
            </p>
            <div className="grid grid-cols-2 gap-3 max-w-sm">
              {[
                { icon: <Activity size={14} />, label: "Live reward curves" },
                { icon: <Clock size={14} />, label: "ETA & progress bar" },
                { icon: <TrendingUp size={14} />, label: "Success rate tracking" },
                { icon: <BarChart3 size={14} />, label: "Loss visualization" },
              ].map((f) => (
                <div
                  key={f.label}
                  className="flex items-center gap-2 text-xs text-[#666]"
                >
                  <span className="text-[#555]">{f.icon}</span>
                  {f.label}
                </div>
              ))}
            </div>
          </div>
          <div className="flex-1 w-full">
            <MockTraining />
          </div>
        </div>

        <div className="flex flex-col md:flex-row-reverse gap-8 md:gap-12 items-center">
          <div className="flex-1 space-y-5">
            <h3 className="text-xl font-bold">
              Experiment Tracking & Reports
            </h3>
            <p className="text-sm text-[#888] leading-relaxed max-w-md">
              Each training run is an experiment linked to a specific environment
              version. Compare runs side-by-side, inspect hyperparameters,
              and export everything as a detailed PDF report.
            </p>
            <div className="space-y-2">
              {[
                "Side-by-side run comparison with metric diffs",
                "Hyperparameter logging for every experiment",
                "Environment version tracking across runs",
                "PDF export for papers and documentation",
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-start gap-2 text-sm text-[#888]"
                >
                  <CheckCircle
                    size={14}
                    className="text-green-500 mt-0.5 shrink-0"
                  />
                  {item}
                </div>
              ))}
            </div>
          </div>
          <div className="flex-1 w-full">
            <MockExperiments />
          </div>
        </div>
      </section>

      <div className="line-glow" />

      {/* ── Template Environments ─────────────────── */}
      <section id="templates" className="max-w-6xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Template Environments
          </h2>
          <p className="text-[#888] max-w-2xl mx-auto leading-relaxed">
            Explore published environments built with Kualia. Use them as
            starting points or study their design for inspiration.
          </p>
        </div>

        {envs.length === 0 ? (
          <div className="border border-[#1a1a1a] rounded-lg p-12 text-center">
            <Joystick className="w-10 h-10 text-[#333] mx-auto mb-4" />
            <p className="text-[#666] mb-1">No environments published yet.</p>
            <p className="text-[#555] text-sm">
              Environments will appear here as they are developed and validated.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {envs.map((env: any) => (
              <Link
                key={env.id}
                href={`/environments/${env.id}`}
                className="group border border-[#1a1a1a] rounded-lg overflow-hidden hover:border-[#333] hover:bg-[#0a0a0a] transition-all"
              >
                <div className="h-36 bg-[#0a0a0a] border-b border-[#1a1a1a] flex items-center justify-center">
                  <div className="text-[#333]">
                    {categoryIcons[env.category] || (
                      <Joystick className="w-8 h-8" />
                    )}
                  </div>
                </div>
                <div className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    {env.category && (
                      <span className="text-[10px] font-mono uppercase tracking-wider text-[#666] border border-[#222] rounded px-1.5 py-0.5">
                        {env.category}
                      </span>
                    )}
                    {env.difficulty && (
                      <span
                        className={`text-[10px] font-mono uppercase tracking-wider border rounded px-1.5 py-0.5 ${difficultyColor[env.difficulty] || "text-[#666] border-[#222]"}`}
                      >
                        {env.difficulty}
                      </span>
                    )}
                  </div>
                  <h3 className="text-base font-semibold text-white mb-2">
                    {env.name}
                  </h3>
                  {env.description && (
                    <p className="text-sm text-[#888] line-clamp-2 leading-relaxed mb-3">
                      {env.description}
                    </p>
                  )}
                  <div className="flex items-center gap-4 text-xs text-[#666]">
                    {env.observation_space && (
                      <span>Obs: {env.observation_space}</span>
                    )}
                    {env.action_space && (
                      <span>Act: {env.action_space}</span>
                    )}
                  </div>
                  <span className="inline-flex items-center gap-1 text-xs text-[#666] group-hover:text-[#999] mt-3 transition-colors">
                    View details <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <div className="line-glow" />

      {/* ── CTA ──────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-24 text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">
          Ready to build your environment?
        </h2>
        <p className="text-[#666] mb-10 max-w-md mx-auto">
          Describe your RL problem, generate the environment, train an agent,
          and export your results. All in one place.
        </p>
        <Link
          href="/create"
          className="inline-flex items-center gap-2 px-8 py-4 bg-white text-black text-sm font-medium rounded-lg hover:bg-[#e5e5e5] transition-colors"
        >
          Start Building <ArrowRight size={16} />
        </Link>
      </section>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   MOCK UI COMPONENTS
   ═══════════════════════════════════════════════════ */

function FeatureCard({
  icon,
  title,
  description,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a] overflow-hidden">
      <div className="p-6 pb-4">
        <div className="mb-3">{icon}</div>
        <h3 className="text-base font-semibold mb-2">{title}</h3>
        <p className="text-sm text-[#888] leading-relaxed">{description}</p>
      </div>
      <div className="px-4 pb-4">{children}</div>
    </div>
  );
}

/* ── RL Loop Diagram ──────────────────────────────── */

function RLLoopDiagram() {
  return (
    <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a] p-8">
      <div className="flex flex-col items-center gap-6">
        {/* Agent box */}
        <div className="w-full max-w-[200px] border border-blue-900/40 bg-blue-950/20 rounded-xl p-4 text-center">
          <Brain size={24} className="text-blue-400 mx-auto mb-2" />
          <span className="text-sm font-semibold text-blue-400">Agent</span>
          <p className="text-[10px] text-[#666] mt-1">Policy π(a|s)</p>
        </div>

        {/* Arrows */}
        <div className="flex items-center gap-8 w-full max-w-md justify-center">
          <div className="flex flex-col items-center gap-1">
            <span className="text-[10px] text-purple-400 font-mono">
              action
            </span>
            <div className="w-px h-6 bg-gradient-to-b from-purple-500 to-transparent" />
            <ArrowRight
              size={12}
              className="text-purple-400 rotate-90"
            />
          </div>

          <div className="flex-1 border border-[#1a1a1a] rounded-lg p-3 text-center">
            <ArrowRightLeft
              size={16}
              className="text-[#555] mx-auto mb-1"
            />
            <span className="text-[9px] text-[#555] font-mono">
              env.step(action)
            </span>
          </div>

          <div className="flex flex-col items-center gap-1">
            <ArrowRight
              size={12}
              className="text-green-400 -rotate-90"
            />
            <div className="w-px h-6 bg-gradient-to-t from-green-500 to-transparent" />
            <span className="text-[10px] text-green-400 font-mono">
              obs, reward
            </span>
          </div>
        </div>

        {/* Environment box */}
        <div className="w-full max-w-[200px] border border-green-900/40 bg-green-950/20 rounded-xl p-4 text-center">
          <Layers size={24} className="text-green-400 mx-auto mb-2" />
          <span className="text-sm font-semibold text-green-400">
            Environment
          </span>
          <p className="text-[10px] text-[#666] mt-1">
            s&apos;, r = env(s, a)
          </p>
        </div>

        {/* Cycle labels */}
        <div className="flex gap-6 mt-2">
          {[
            { label: "Observation", color: "text-blue-400", bg: "bg-blue-950/30 border-blue-900/30" },
            { label: "Action", color: "text-purple-400", bg: "bg-purple-950/30 border-purple-900/30" },
            { label: "Reward", color: "text-yellow-400", bg: "bg-yellow-950/30 border-yellow-900/30" },
            { label: "Done?", color: "text-red-400", bg: "bg-red-950/30 border-red-900/30" },
          ].map((l) => (
            <span
              key={l.label}
              className={`text-[9px] font-mono px-2 py-0.5 border rounded ${l.bg} ${l.color}`}
            >
              {l.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── Mock: Builder Chat ──────────────────────────── */

function MockBuilderChat() {
  return (
    <div className="border border-[#1a1a1a] rounded-2xl bg-[#0a0a0a] overflow-hidden">
      <div className="border-b border-[#1a1a1a] px-4 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
          <span className="text-xs font-medium text-[#888]">
            drone-navigation-v2
          </span>
          <span className="text-[9px] text-[#555] font-mono">v3</span>
          <span className="text-[9px] px-1.5 py-0.5 bg-[#1a1a1a] rounded text-[#666]">
            robotics
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[9px] px-2 py-0.5 border border-[#1a1a1a] rounded text-[#555]">
            <Download size={9} className="inline mr-1" />
            ZIP
          </span>
          <span className="text-[9px] px-2 py-0.5 bg-white text-black rounded font-medium">
            <Play size={9} className="inline mr-1" />
            Train Agent
          </span>
        </div>
      </div>

      <div className="flex" style={{ height: "320px" }}>
        {/* Chat panel */}
        <div className="w-[40%] border-r border-[#1a1a1a] flex flex-col">
          <div className="flex-1 p-3 space-y-2.5 overflow-hidden">
            <div className="ml-6 bg-[#1a1a1a] rounded-lg p-2.5 text-[10px] text-[#ccc]">
              Create a drone navigation environment with obstacle avoidance
            </div>
            <div className="mr-6 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-2.5 text-[10px] space-y-1.5">
              <p className="text-[#bbb]">
                Created DroneNavEnv with 18-dim observation (position, velocity,
                8 distance sensors). Continuous 4-dim action for thrust.
              </p>
              <div className="flex gap-1 flex-wrap">
                {[
                  "syntax",
                  "import",
                  "reset",
                  "step",
                  "obs",
                  "act",
                  "reward",
                  "determ.",
                ].map((t) => (
                  <span
                    key={t}
                    className="text-[8px] px-1 py-0.5 bg-green-950 text-green-400 rounded"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
            <div className="ml-6 bg-[#1a1a1a] rounded-lg p-2.5 text-[10px] text-[#ccc]">
              Add wind turbulence as random perturbation
            </div>
            <div className="mr-6 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-2.5 text-[10px]">
              <p className="text-[#bbb]">
                Added Gaussian wind N(0, 0.3) each step. New obs: wind_vector.
              </p>
              <div className="flex gap-1 flex-wrap mt-1.5">
                {["syntax", "import", "reset", "step", "obs", "act", "reward"].map(
                  (t) => (
                    <span
                      key={t}
                      className="text-[8px] px-1 py-0.5 bg-green-950 text-green-400 rounded"
                    >
                      {t}
                    </span>
                  ),
                )}
                <span className="text-[8px] px-1 py-0.5 bg-red-950 text-red-400 rounded">
                  determ.
                </span>
              </div>
            </div>
          </div>
          <div className="border-t border-[#1a1a1a] p-2 flex gap-1.5">
            <div className="flex-1 bg-[#0a0a0a] border border-[#1a1a1a] rounded px-2.5 py-1.5 text-[10px] text-[#555]">
              Describe changes...
            </div>
            <div className="px-2 py-1.5 bg-white rounded">
              <Send size={10} className="text-black" />
            </div>
          </div>
        </div>

        {/* Right panel */}
        <div className="w-[60%] flex flex-col overflow-hidden">
          <div className="border-b border-[#1a1a1a] px-3 flex items-center gap-0">
            {[
              { label: "Dashboard", active: true },
              { label: "Code", active: false },
              { label: "Agent", active: false },
              { label: "History", active: false },
            ].map((t) => (
              <span
                key={t.label}
                className={`text-[10px] px-2.5 py-2 border-b-2 ${t.active ? "border-white text-white" : "border-transparent text-[#555]"}`}
              >
                {t.label}
              </span>
            ))}
          </div>
          <div className="flex-1 p-3 overflow-hidden space-y-3">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-[10px] text-[#888]">
                7/8 Tests Passing
              </span>
            </div>
            <div className="grid grid-cols-4 gap-1.5">
              {[
                "syntax",
                "import",
                "reset",
                "step",
                "obs_space",
                "action_space",
                "reward",
                "determinism",
              ].map((t, i) => (
                <div
                  key={t}
                  className={`rounded p-1.5 text-center ${i < 7 ? "bg-green-950/30 border border-green-900/30" : "bg-red-950/30 border border-red-900/30"}`}
                >
                  <div className="flex items-center justify-center gap-1">
                    {i < 7 ? (
                      <CheckCircle size={8} className="text-green-400" />
                    ) : (
                      <XCircle size={8} className="text-red-400" />
                    )}
                    <span className="text-[8px]">{t}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="border border-[#1a1a1a] rounded-lg p-2.5">
                <div className="flex items-center gap-1.5 mb-2">
                  <Eye size={10} className="text-blue-400" />
                  <span className="text-[9px] font-medium">
                    Observation Space
                  </span>
                </div>
                <div className="space-y-1 text-[9px]">
                  <div className="flex justify-between">
                    <span className="text-[#555]">Type</span>
                    <span className="font-mono">Box</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#555]">Shape</span>
                    <span className="font-mono">[18]</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#555]">Range</span>
                    <span className="font-mono">[-1, 1]</span>
                  </div>
                </div>
              </div>
              <div className="border border-[#1a1a1a] rounded-lg p-2.5">
                <div className="flex items-center gap-1.5 mb-2">
                  <Zap size={10} className="text-purple-400" />
                  <span className="text-[9px] font-medium">Action Space</span>
                </div>
                <div className="space-y-1 text-[9px]">
                  <div className="flex justify-between">
                    <span className="text-[#555]">Type</span>
                    <span className="font-mono">Box</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#555]">Shape</span>
                    <span className="font-mono">[4]</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#555]">Range</span>
                    <span className="font-mono">[-1, 1]</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Mock: Version History ────────────────────────── */

function MockVersionHistory() {
  const versions = [
    { v: "v3", msg: "Added wind turbulence", time: "2m ago", tests: "7/8" },
    { v: "v2", msg: "Obstacle avoidance penalty", time: "8m ago", tests: "8/8" },
    { v: "v1", msg: "Initial generation", time: "12m ago", tests: "8/8" },
  ];

  return (
    <div className="border border-[#1a1a1a] rounded-lg overflow-hidden">
      <div className="bg-[#050505] px-3 py-1.5 border-b border-[#1a1a1a] flex items-center gap-2">
        <GitBranch size={10} className="text-[#555]" />
        <span className="text-[9px] text-[#666]">Version History</span>
      </div>
      <div className="divide-y divide-[#1a1a1a]">
        {versions.map((v, i) => (
          <div
            key={v.v}
            className={`flex items-center justify-between px-3 py-2 ${i === 0 ? "bg-[#0a0a0a]" : ""}`}
          >
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-white">{v.v}</span>
              <span className="text-[10px] text-[#888]">{v.msg}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[9px] text-green-400 font-mono">
                {v.tests}
              </span>
              <span className="text-[9px] text-[#555]">{v.time}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Mock: Test Grid ──────────────────────────────── */

function MockTestGrid() {
  const tests = [
    { name: "syntax", pass: true },
    { name: "import", pass: true },
    { name: "reset", pass: true },
    { name: "step", pass: true },
    { name: "obs_space", pass: true },
    { name: "action_space", pass: true },
    { name: "reward_sanity", pass: true },
    { name: "determinism", pass: true },
  ];

  return (
    <div className="border border-[#1a1a1a] rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2.5">
        <div className="w-2 h-2 rounded-full bg-green-500" />
        <span className="text-[10px] text-[#888]">8/8 Tests Passing</span>
        <span className="text-[9px] text-[#555] ml-auto">0.42s</span>
      </div>
      <div className="grid grid-cols-4 gap-1.5">
        {tests.map((t) => (
          <div
            key={t.name}
            className="rounded p-1.5 text-center bg-green-950/30 border border-green-900/30"
          >
            <div className="flex items-center justify-center gap-1">
              <CheckCircle size={8} className="text-green-400" />
              <span className="text-[8px] text-green-300">{t.name}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Mock: Chat Iteration ─────────────────────────── */

function MockChatIteration() {
  return (
    <div className="border border-[#1a1a1a] rounded-lg overflow-hidden">
      <div className="p-3 space-y-2">
        <div className="ml-6 bg-[#1a1a1a] rounded-lg p-2 text-[10px] text-[#ccc]">
          Make the reward sparse — only +1 at goal, 0 otherwise
        </div>
        <div className="mr-6 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-2 text-[10px]">
          <p className="text-[#bbb]">
            Replaced distance-based reward with sparse signal. +1.0 within 0.1m
            of goal, 0.0 otherwise. Added small time penalty (-0.001/step).
          </p>
          <div className="flex gap-1 mt-1.5 flex-wrap">
            {Array(8)
              .fill(0)
              .map((_, i) => (
                <span
                  key={i}
                  className="text-[8px] px-1 py-0.5 bg-green-950 text-green-400 rounded"
                >
                  pass
                </span>
              ))}
          </div>
          <p className="text-[9px] text-[#555] mt-1">
            v4 — reward function rewritten
          </p>
        </div>
      </div>
      <div className="border-t border-[#1a1a1a] p-2 flex gap-1.5">
        <div className="flex-1 bg-[#0a0a0a] border border-[#1a1a1a] rounded px-2.5 py-1.5 text-[10px] text-[#555]">
          Describe changes...
        </div>
        <div className="px-2 py-1.5 bg-white rounded">
          <Send size={10} className="text-black" />
        </div>
      </div>
    </div>
  );
}

/* ── Mock: Export Options ──────────────────────────── */

function MockExportOptions() {
  return (
    <div className="border border-[#1a1a1a] rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between border border-[#1a1a1a] rounded-lg px-3 py-2.5 hover:border-[#333] transition-colors">
        <div className="flex items-center gap-3">
          <Download size={14} className="text-[#888]" />
          <div>
            <span className="text-[11px] font-medium block">
              Download ZIP
            </span>
            <span className="text-[9px] text-[#555]">
              env.py + requirements.txt + README.md
            </span>
          </div>
        </div>
        <ArrowRight size={12} className="text-[#555]" />
      </div>
      <div className="flex items-center justify-between border border-[#1a1a1a] rounded-lg px-3 py-2.5 hover:border-[#333] transition-colors">
        <div className="flex items-center gap-3">
          <GitBranch size={14} className="text-[#888]" />
          <div>
            <span className="text-[11px] font-medium block">
              Push to GitHub
            </span>
            <span className="text-[9px] text-[#555]">
              Auto-creates repo with CI workflow
            </span>
          </div>
        </div>
        <ArrowRight size={12} className="text-[#555]" />
      </div>
      <div className="flex items-center justify-between border border-[#1a1a1a] rounded-lg px-3 py-2.5 hover:border-[#333] transition-colors">
        <div className="flex items-center gap-3">
          <FileCode2 size={14} className="text-[#888]" />
          <div>
            <span className="text-[11px] font-medium block">
              Copy Code
            </span>
            <span className="text-[9px] text-[#555]">
              Raw Python source to clipboard
            </span>
          </div>
        </div>
        <ArrowRight size={12} className="text-[#555]" />
      </div>
    </div>
  );
}

/* ── Mock: Training ──────────────────────────────── */

function MockTraining() {
  const rewardData = [12, 18, 15, 22, 28, 25, 32, 38, 35, 42, 48, 52, 55, 58, 62, 65, 68, 72, 75, 78];
  const lengthData = [200, 185, 190, 170, 155, 160, 140, 125, 130, 110, 95, 85, 80, 75, 72, 68, 65, 60, 58, 55];
  const successData = [0, 0, 0.1, 0.1, 0.2, 0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.88, 0.9, 0.92, 0.95, 0.97];
  const lossData = [2.5, 2.3, 2.1, 1.9, 1.8, 1.6, 1.5, 1.3, 1.2, 1.1, 1.0, 0.9, 0.85, 0.8, 0.75, 0.72, 0.7, 0.68, 0.65, 0.63];

  return (
    <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a] overflow-hidden">
      <div className="px-4 pt-3 pb-2 space-y-1.5">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-[#888] flex items-center gap-1.5">
            <Loader2 size={10} className="animate-spin text-blue-400" />
            Training in progress
          </span>
          <span className="font-mono text-white">73.5%</span>
        </div>
        <div className="relative h-1.5 bg-[#1a1a1a] rounded-full overflow-hidden">
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-600 to-blue-400 rounded-full"
            style={{ width: "73.5%" }}
          />
        </div>
        <div className="flex justify-between text-[9px] text-[#555] font-mono">
          <span>0</span>
          <span>73.5K / 100K</span>
          <span>100K</span>
        </div>
      </div>

      <div className="px-3 pb-3 grid grid-cols-2 gap-2">
        <MiniChart data={rewardData} label="Episode Reward" value="78.2" color="#22c55e" />
        <MiniChart data={lengthData} label="Episode Length" value="55" color="#3b82f6" />
        <MiniChart data={successData} label="Success Rate" value="97%" color="#eab308" />
        <MiniChart data={lossData} label="Policy Loss" value="0.63" color="#ef4444" />
      </div>

      <div className="border-t border-[#1a1a1a] px-4 py-2 flex gap-4 text-[9px] text-[#555]">
        <span>Step: 73,500</span>
        <span>Episodes: 1,247</span>
        <span>FPS: 4,280</span>
        <span>ETA: 6s</span>
        <span className="ml-auto font-mono text-[#888]">PPO</span>
      </div>
    </div>
  );
}

function MiniChart({
  data,
  label,
  value,
  color,
}: {
  data: number[];
  label: string;
  value: string;
  color: string;
}) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const w = 160;
  const h = 40;
  const points = data
    .map(
      (v, i) =>
        `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`,
    )
    .join(" ");

  return (
    <div className="border border-[#1a1a1a] rounded-lg p-2.5">
      <div className="flex justify-between items-center mb-1">
        <span className="text-[9px] text-[#555]">{label}</span>
        <span className="text-[10px] font-mono" style={{ color }}>
          {value}
        </span>
      </div>
      <svg
        width="100%"
        viewBox={`0 0 ${w} ${h}`}
        preserveAspectRatio="none"
        className="overflow-visible"
      >
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          points={points}
          opacity={0.8}
        />
        <circle
          cx={w}
          cy={h - ((data[data.length - 1] - min) / range) * h}
          r="2.5"
          fill={color}
        />
      </svg>
    </div>
  );
}

/* ── Mock: Experiments ────────────────────────────── */

function MockExperiments() {
  const runs = [
    { id: 5, algo: "PPO", ver: "v3", steps: "100K", reward: "78.2", success: "97%", time: "24s", status: "completed" },
    { id: 4, algo: "PPO", ver: "v2", steps: "100K", reward: "45.6", success: "68%", time: "22s", status: "completed" },
    { id: 3, algo: "SAC", ver: "v2", steps: "50K", reward: "38.1", success: "52%", time: "18s", status: "completed" },
    { id: 2, algo: "PPO", ver: "v1", steps: "50K", reward: "12.4", success: "15%", time: "11s", status: "completed" },
  ];

  return (
    <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a] overflow-hidden">
      <div className="border-b border-[#1a1a1a] px-3 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FlaskConical size={12} className="text-[#555]" />
          <span className="text-[10px] text-[#888]">Experiments</span>
        </div>
        <span className="text-[9px] px-2 py-0.5 border border-blue-900 text-blue-400 rounded">
          Compare Runs
        </span>
      </div>

      <div className="px-3 pt-2 pb-1">
        <div className="border border-blue-900/30 rounded-lg overflow-hidden mb-2">
          <div className="bg-blue-950/20 px-2.5 py-1 text-[9px] text-blue-400">
            Comparing Run #5 vs #4
          </div>
          <table className="w-full text-[9px]">
            <thead>
              <tr className="border-b border-[#1a1a1a]">
                <th className="px-2 py-1 text-left text-[#555] font-medium">
                  Metric
                </th>
                <th className="px-2 py-1 text-center font-mono text-[#888]">
                  #5 <span className="text-[#555]">PPO v3</span>
                </th>
                <th className="px-2 py-1 text-center font-mono text-[#888]">
                  #4 <span className="text-[#555]">PPO v2</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {[
                ["Reward", "78.2", "45.6"],
                ["Success", "97%", "68%"],
                ["Length", "55", "120"],
              ].map(([label, v1, v2]) => (
                <tr
                  key={String(label)}
                  className="border-b border-[#1a1a1a]/30"
                >
                  <td className="px-2 py-1 text-[#555]">{label}</td>
                  <td className="px-2 py-1 text-center font-mono text-green-400">
                    {v1}
                  </td>
                  <td className="px-2 py-1 text-center font-mono text-[#888]">
                    {v2}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="px-3 pb-3 space-y-1">
        {runs.map((r) => (
          <div
            key={r.id}
            className="flex items-center justify-between border border-[#1a1a1a] rounded-lg px-2.5 py-1.5"
          >
            <div className="flex items-center gap-2">
              <span className="text-[9px] font-mono text-[#666]">
                #{r.id}
              </span>
              <span className="text-[8px] px-1.5 py-0.5 bg-green-950 text-green-400 rounded">
                {r.status}
              </span>
              <span className="text-[9px] text-[#555]">{r.algo}</span>
              <span className="text-[9px] font-mono text-[#444]">
                {r.ver}
              </span>
              <span className="text-[9px] text-[#555]">{r.steps}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-[9px] font-mono text-green-400">
                R: {r.reward}
              </span>
              <span className="text-[9px] font-mono text-yellow-400">
                {r.success}
              </span>
              <span className="text-[9px] text-[#555]">{r.time}</span>
              <BarChart3 size={10} className="text-[#555]" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
