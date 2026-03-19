import Link from "next/link";
import {
  ArrowRight, Sparkles, IterationCcw, Play, FlaskConical,
  BarChart3, GitBranch, FileDown, Cpu, Terminal,
  Layers, Zap, Brain, TestTubeDiagonal,
  Send, CheckCircle, XCircle, Bot, Loader2,
  Download, RefreshCw, Eye, Target,
} from "lucide-react";
import { AuthRedirect } from "@/components/AuthRedirect";

/* ── Static Data ───────────────────────────────── */

const pipeline = [
  { num: "01", title: "Describe", desc: "Tell the AI what environment you need in plain English.", icon: <Sparkles size={18} /> },
  { num: "02", title: "Generate", desc: "Architect Agent writes Gymnasium code, validated by 8 tests.", icon: <Cpu size={18} /> },
  { num: "03", title: "Iterate", desc: "Chat to refine rewards, observations, dynamics. Every change versioned.", icon: <IterationCcw size={18} /> },
  { num: "04", title: "Train", desc: "One-click agent training. Live curves, metrics, and ETA.", icon: <Play size={18} /> },
  { num: "05", title: "Experiment", desc: "Compare runs across env versions. Export PDF reports.", icon: <FlaskConical size={18} /> },
];

const capabilities = [
  { label: "Gymnasium v0.29+", icon: <Layers size={14} /> },
  { label: "8 Automated Tests", icon: <TestTubeDiagonal size={14} /> },
  { label: "PPO / SAC / DQN", icon: <Zap size={14} /> },
  { label: "PDF Reports", icon: <FileDown size={14} /> },
  { label: "Version Control", icon: <GitBranch size={14} /> },
  { label: "Python SDK", icon: <Terminal size={14} /> },
];

/* ── Page ──────────────────────────────────────── */

export default function Home() {
  return (
    <div className="fade-in">
      <AuthRedirect to="/dashboard" />

      {/* ── Hero ──────────────────────────── */}
      <section className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center px-6 text-center">
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.05] max-w-4xl">
          Design the Experience.<br />
          <span className="text-[#888]">Train the Intelligence.</span>
        </h1>
        <p className="text-xl md:text-2xl text-[#888] mt-6 max-w-2xl leading-relaxed">
          Design, Train, and Experiment with RL
        </p>
        <p className="text-sm text-[#555] mt-4 max-w-xl leading-relaxed">
          Generate Gymnasium environments with AI, iterate through chat,
          train agents, and track experiments with version-controlled reports.
        </p>
        <div className="flex flex-wrap gap-4 mt-10 justify-center">
          <Link href="/create" className="px-7 py-3.5 bg-white text-black text-sm font-medium rounded-lg hover:bg-[#e5e5e5] transition-colors">
            Start Building
          </Link>
          <Link href="/catalog" className="px-7 py-3.5 border border-[#333] text-sm rounded-lg hover:border-[#555] transition-colors text-[#888] hover:text-white">
            Browse Environments
          </Link>
        </div>
        <div className="flex flex-wrap gap-3 mt-12 justify-center">
          {capabilities.map((c) => (
            <span key={c.label} className="flex items-center gap-1.5 text-[11px] text-[#555] px-3 py-1.5 border border-[#1a1a1a] rounded-full">
              {c.icon} {c.label}
            </span>
          ))}
        </div>
      </section>

      {/* ── Hero Preview: Builder ─────────── */}
      <section className="max-w-6xl mx-auto px-6 pb-16">
        <MockBuilder />
      </section>

      <div className="line-glow" />

      {/* ── Pipeline ──────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <h2 className="text-2xl font-bold mb-3">From idea to trained agent</h2>
        <p className="text-[#666] text-sm mb-14 max-w-lg">Five steps. One platform. No boilerplate.</p>
        <div className="relative">
          <div className="hidden md:block absolute top-6 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#1a1a1a] to-transparent" />
          <div className="grid md:grid-cols-5 gap-8 md:gap-4">
            {pipeline.map((s, i) => (
              <div key={s.num} className="relative group">
                <div className="flex items-center gap-3 mb-3 md:flex-col md:items-start md:gap-2">
                  <div className="w-10 h-10 rounded-lg bg-[#0a0a0a] border border-[#1a1a1a] flex items-center justify-center text-[#555] group-hover:text-white group-hover:border-[#333] transition-colors shrink-0">
                    {s.icon}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-[#333] font-mono">{s.num}</span>
                    <h3 className="font-semibold text-sm">{s.title}</h3>
                  </div>
                </div>
                <p className="text-xs text-[#666] leading-relaxed">{s.desc}</p>
                {i < pipeline.length - 1 && (
                  <ArrowRight size={14} className="hidden md:block absolute -right-2 top-3 text-[#333]" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="line-glow" />

      {/* ── Feature 1: AI Environment Builder ── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="flex flex-col md:flex-row gap-8 md:gap-12 items-center">
          <div className="flex-1 space-y-4">
            <div className="text-[#555]"><Terminal size={20} /></div>
            <h3 className="text-xl font-bold">AI Environment Builder</h3>
            <p className="text-sm text-[#888] leading-relaxed max-w-md">
              Describe your RL environment in natural language. The Architect Agent generates
              Gymnasium-compatible code, validates it with 8 automated tests, and lets you
              iterate through chat. Every change is versioned.
            </p>
            <Link href="/create" className="inline-flex items-center gap-1.5 text-sm text-white hover:text-[#ccc] transition-colors mt-2">
              Start Building <ArrowRight size={14} />
            </Link>
          </div>
          <div className="flex-1 w-full">
            <MockBuilderChat />
          </div>
        </div>
      </section>

      <div className="line-glow" />

      {/* ── Feature 2: Agent Training ──────── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="flex flex-col md:flex-row-reverse gap-8 md:gap-12 items-center">
          <div className="flex-1 space-y-4">
            <div className="text-[#555]"><BarChart3 size={20} /></div>
            <h3 className="text-xl font-bold">Agent Training & Monitoring</h3>
            <p className="text-sm text-[#888] leading-relaxed max-w-md">
              Train agents with Stable Baselines3 in a single click. Live progress bar with ETA,
              real-time reward curves, episode metrics, loss functions, and post-training
              agent replay visualization.
            </p>
            <Link href="/create" className="inline-flex items-center gap-1.5 text-sm text-white hover:text-[#ccc] transition-colors mt-2">
              See How It Works <ArrowRight size={14} />
            </Link>
          </div>
          <div className="flex-1 w-full">
            <MockTraining />
          </div>
        </div>
      </section>

      <div className="line-glow" />

      {/* ── Feature 3: Experiment Tracking ─── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="flex flex-col md:flex-row gap-8 md:gap-12 items-center">
          <div className="flex-1 space-y-4">
            <div className="text-[#555]"><GitBranch size={20} /></div>
            <h3 className="text-xl font-bold">Experiment Tracking</h3>
            <p className="text-sm text-[#888] leading-relaxed max-w-md">
              Each training run is an experiment linked to an environment version.
              Compare runs side-by-side, view detailed reports with hyperparameters,
              and export everything as PDF for papers and documentation.
            </p>
          </div>
          <div className="flex-1 w-full">
            <MockExperiments />
          </div>
        </div>
      </section>

      <div className="line-glow" />

      {/* ── Feature 4: Research Lab ────────── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="flex flex-col md:flex-row-reverse gap-8 md:gap-12 items-center">
          <div className="flex-1 space-y-4">
            <div className="text-[#555]"><Brain size={20} /></div>
            <h3 className="text-xl font-bold">AI Research Lab</h3>
            <p className="text-sm text-[#888] leading-relaxed max-w-md">
              A multi-agent AI research team collaborates on ideas, finds consensus,
              and writes PhD-level papers with simulated experiments, code, and charts.
              All in ArXiv-ready format.
            </p>
            <Link href="/research" className="inline-flex items-center gap-1.5 text-sm text-white hover:text-[#ccc] transition-colors mt-2">
              Explore Research Lab <ArrowRight size={14} />
            </Link>
          </div>
          <div className="flex-1 w-full">
            <MockResearchLab />
          </div>
        </div>
      </section>

      <div className="line-glow" />

      {/* ── SDK ───────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold mb-3 text-center">Use anywhere</h2>
          <p className="text-[#666] text-sm mb-8 text-center">Access your environments programmatically with the Python SDK.</p>
          <div className="code-block">
            <p className="text-[#555] text-xs mb-3 font-sans">Python SDK</p>
            <code>
              <span className="text-[#888]">import</span> kualia{"\n\n"}
              <span className="text-[#555]"># Generate an environment from description</span>{"\n"}
              env = kualia.make(<span className="text-[#aaa]">&quot;gridworld-maze&quot;</span>, api_key=<span className="text-[#aaa]">&quot;...&quot;</span>){"\n"}
              obs, info = env.reset(seed=<span className="text-[#aaa]">42</span>){"\n\n"}
              <span className="text-[#888]">for</span> step <span className="text-[#888]">in</span> range(<span className="text-[#aaa]">1000</span>):{"\n"}
              {"  "}action = env.action_space.sample(){"\n"}
              {"  "}obs, reward, done, trunc, info = env.step(action){"\n"}
              {"  "}<span className="text-[#888]">if</span> done <span className="text-[#888]">or</span> trunc:{"\n"}
              {"    "}obs, info = env.reset()
            </code>
          </div>
        </div>
      </section>

      <div className="line-glow" />

      {/* ── CTA ───────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-24 text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready to build?</h2>
        <p className="text-[#666] mb-10 max-w-md mx-auto">
          Describe your environment, train an agent, and track your experiments. All in one place.
        </p>
        <div className="flex flex-wrap gap-4 justify-center">
          <Link href="/create" className="inline-flex items-center gap-2 px-7 py-3.5 bg-white text-black text-sm font-medium rounded-lg hover:bg-[#e5e5e5] transition-colors">
            Create Your First Environment <ArrowRight size={16} />
          </Link>
          <Link href="/research" className="inline-flex items-center gap-2 px-7 py-3.5 border border-[#333] text-sm rounded-lg hover:border-[#555] transition-colors text-[#888] hover:text-white">
            Explore Research Lab
          </Link>
        </div>
      </section>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   MOCK UI COMPONENTS
   Coded previews of the actual product UI
   ═══════════════════════════════════════════════════ */

/* ── Hero: Full Builder Layout ─────────────────── */

function MockBuilder() {
  return (
    <div className="border border-[#1a1a1a] rounded-2xl bg-[#0a0a0a] overflow-hidden">
      {/* Top bar */}
      <div className="border-b border-[#1a1a1a] px-4 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-[#333]" />
          <span className="text-xs font-medium text-[#888]">drone-navigation-v2</span>
          <span className="text-[9px] text-[#555] font-mono">v3</span>
          <span className="text-[9px] px-1.5 py-0.5 bg-[#1a1a1a] rounded text-[#666]">robotics</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[9px] px-2 py-0.5 border border-[#1a1a1a] rounded text-[#555]"><Download size={9} className="inline mr-1" />ZIP</span>
          <span className="text-[9px] px-2 py-0.5 bg-white text-black rounded font-medium"><Play size={9} className="inline mr-1" />Train Agent</span>
        </div>
      </div>

      <div className="flex" style={{ height: "340px" }}>
        {/* Chat panel */}
        <div className="w-[40%] border-r border-[#1a1a1a] flex flex-col">
          <div className="flex-1 p-3 space-y-2.5 overflow-hidden">
            <div className="ml-6 bg-[#1a1a1a] rounded-lg p-2.5 text-[10px] text-[#ccc]">
              Make the drone avoid obstacles using a penalty-based reward
            </div>
            <div className="mr-6 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-2.5 text-[10px] space-y-1.5">
              <p className="text-[#bbb]">Added obstacle avoidance with -5.0 collision penalty. Observation now includes 8 distance sensors.</p>
              <div className="flex gap-1">
                {["syntax","import","reset","step","obs_space","action_space","reward","determ."].map(t => (
                  <span key={t} className="text-[8px] px-1 py-0.5 bg-green-950 text-green-400 rounded">{t}</span>
                ))}
              </div>
            </div>
            <div className="ml-6 bg-[#1a1a1a] rounded-lg p-2.5 text-[10px] text-[#ccc]">
              Add wind turbulence as random force perturbation
            </div>
            <div className="mr-6 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-2.5 text-[10px]">
              <p className="text-[#bbb]">Added Gaussian wind perturbation N(0, 0.3) applied each step. New obs component: wind_vector.</p>
              <div className="flex gap-1 mt-1.5">
                {["syntax","import","reset","step","obs_space","action_space","reward"].map(t => (
                  <span key={t} className="text-[8px] px-1 py-0.5 bg-green-950 text-green-400 rounded">{t}</span>
                ))}
                <span className="text-[8px] px-1 py-0.5 bg-red-950 text-red-400 rounded">determ.</span>
              </div>
            </div>
          </div>
          <div className="border-t border-[#1a1a1a] p-2 flex gap-1.5">
            <div className="flex-1 bg-[#0a0a0a] border border-[#1a1a1a] rounded px-2.5 py-1.5 text-[10px] text-[#555]">Describe changes...</div>
            <div className="px-2 py-1.5 bg-white rounded"><Send size={10} className="text-black" /></div>
          </div>
        </div>

        {/* Right panel: tabs + dashboard */}
        <div className="w-[60%] flex flex-col overflow-hidden">
          <div className="border-b border-[#1a1a1a] px-3 flex items-center gap-0">
            {[
              { label: "Dashboard", active: true },
              { label: "Code", active: false },
              { label: "Agent", active: false },
              { label: "History", active: false },
              { label: "Docs", active: false },
            ].map(t => (
              <span key={t.label} className={`text-[10px] px-2.5 py-2 border-b-2 ${t.active ? "border-white text-white" : "border-transparent text-[#555]"}`}>
                {t.label}
              </span>
            ))}
          </div>
          <div className="flex-1 p-3 overflow-hidden space-y-3">
            {/* Test results */}
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-[10px] text-[#888]">7/8 Tests Passing</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5">
              {["syntax","import","reset","step","obs_space","action_space","reward_sanity","determinism"].map((t, i) => (
                <div key={t} className={`rounded p-1.5 text-center ${i < 7 ? "bg-green-950/30 border border-green-900/30" : "bg-red-950/30 border border-red-900/30"}`}>
                  <div className="flex items-center justify-center gap-1">
                    {i < 7 ? <CheckCircle size={8} className="text-green-400" /> : <XCircle size={8} className="text-red-400" />}
                    <span className="text-[8px]">{t}</span>
                  </div>
                </div>
              ))}
            </div>
            {/* Spaces */}
            <div className="grid grid-cols-2 gap-2">
              <div className="border border-[#1a1a1a] rounded-lg p-2.5">
                <div className="flex items-center gap-1.5 mb-2"><Eye size={10} className="text-blue-400" /><span className="text-[9px] font-medium">Observation Space</span></div>
                <div className="space-y-1 text-[9px]">
                  <div className="flex justify-between"><span className="text-[#555]">Type</span><span className="font-mono">Box</span></div>
                  <div className="flex justify-between"><span className="text-[#555]">Shape</span><span className="font-mono">[18]</span></div>
                  <div className="flex justify-between"><span className="text-[#555]">Range</span><span className="font-mono">[-1, 1]</span></div>
                </div>
              </div>
              <div className="border border-[#1a1a1a] rounded-lg p-2.5">
                <div className="flex items-center gap-1.5 mb-2"><Zap size={10} className="text-purple-400" /><span className="text-[9px] font-medium">Action Space</span></div>
                <div className="space-y-1 text-[9px]">
                  <div className="flex justify-between"><span className="text-[#555]">Type</span><span className="font-mono">Box</span></div>
                  <div className="flex justify-between"><span className="text-[#555]">Shape</span><span className="font-mono">[4]</span></div>
                  <div className="flex justify-between"><span className="text-[#555]">Range</span><span className="font-mono">[-1, 1]</span></div>
                </div>
              </div>
            </div>
            <div className="border border-[#1a1a1a] rounded-lg p-2.5">
              <div className="flex items-center gap-1.5 mb-1.5"><Target size={10} className="text-yellow-400" /><span className="text-[9px] font-medium">Reward Function</span></div>
              <p className="text-[9px] text-[#888]">Distance-based + collision penalty (-5.0) + goal bonus (+50.0)</p>
              <div className="flex gap-1 mt-1.5">
                {["distance_reward","collision_penalty","goal_bonus","time_penalty"].map(c => (
                  <span key={c} className="text-[8px] px-1.5 py-0.5 bg-yellow-950/30 text-yellow-400 rounded">{c}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Feature: Builder Chat ─────────────────────── */

function MockBuilderChat() {
  return (
    <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a] overflow-hidden">
      <div className="border-b border-[#1a1a1a] px-3 py-2 flex items-center gap-2">
        <IterationCcw size={12} className="text-[#555]" />
        <span className="text-[10px] text-[#888]">Builder Chat</span>
        <span className="text-[9px] text-[#555] ml-auto font-mono">v1 → v2 → v3</span>
      </div>
      <div className="p-3 space-y-2.5" style={{ minHeight: "240px" }}>
        <div className="ml-8 bg-[#1a1a1a] rounded-lg p-2.5 text-[10px] text-[#ccc]">
          Create a stock trading environment with 5 assets and transaction costs
        </div>
        <div className="mr-8 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-2.5 text-[10px]">
          <p className="text-[#bbb]">Created multi-asset trading env with portfolio tracking, 0.1% transaction costs, and Sharpe ratio reward.</p>
          <div className="flex gap-1 mt-1.5">
            {Array(8).fill(0).map((_, i) => (
              <span key={i} className="text-[8px] px-1 py-0.5 bg-green-950 text-green-400 rounded">pass</span>
            ))}
          </div>
          <p className="text-[9px] text-[#555] mt-1">v1</p>
        </div>
        <div className="ml-8 bg-[#1a1a1a] rounded-lg p-2.5 text-[10px] text-[#ccc]">
          Add market impact: large orders should move the price against us
        </div>
        <div className="mr-8 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-2.5 text-[10px]">
          <p className="text-[#bbb]">Added non-linear market impact model. Orders above 5% of volume incur slippage proportional to order&sup2;.</p>
          <div className="flex gap-1 mt-1.5">
            {Array(8).fill(0).map((_, i) => (
              <span key={i} className="text-[8px] px-1 py-0.5 bg-green-950 text-green-400 rounded">pass</span>
            ))}
          </div>
          <p className="text-[9px] text-[#555] mt-1">v2</p>
        </div>
      </div>
    </div>
  );
}

/* ── Feature: Agent Training ───────────────────── */

function MockTraining() {
  const rewardData = [12, 18, 15, 22, 28, 25, 32, 38, 35, 42, 48, 52, 55, 58, 62, 65, 68, 72, 75, 78];
  const lengthData = [200, 185, 190, 170, 155, 160, 140, 125, 130, 110, 95, 85, 80, 75, 72, 68, 65, 60, 58, 55];
  const successData = [0, 0, 0.1, 0.1, 0.2, 0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.88, 0.9, 0.92, 0.95, 0.97];
  const lossData = [2.5, 2.3, 2.1, 1.9, 1.8, 1.6, 1.5, 1.3, 1.2, 1.1, 1.0, 0.9, 0.85, 0.8, 0.75, 0.72, 0.7, 0.68, 0.65, 0.63];

  return (
    <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a] overflow-hidden">
      {/* Progress bar */}
      <div className="px-4 pt-3 pb-2 space-y-1.5">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-[#888] flex items-center gap-1.5"><Loader2 size={10} className="animate-spin text-blue-400" /> Training in progress</span>
          <span className="font-mono text-white">73.5%</span>
        </div>
        <div className="relative h-1.5 bg-[#1a1a1a] rounded-full overflow-hidden">
          <div className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-600 to-blue-400 rounded-full" style={{ width: "73.5%" }} />
        </div>
        <div className="flex justify-between text-[9px] text-[#555] font-mono">
          <span>0</span>
          <span>73.5K / 100K</span>
          <span>100K</span>
        </div>
      </div>

      {/* Charts grid */}
      <div className="px-3 pb-3 grid grid-cols-2 gap-2">
        <MiniMockChart data={rewardData} label="Episode Reward" value="78.2" color="#22c55e" />
        <MiniMockChart data={lengthData} label="Episode Length" value="55" color="#3b82f6" />
        <MiniMockChart data={successData} label="Success Rate" value="97%" color="#eab308" />
        <MiniMockChart data={lossData} label="Policy Loss" value="0.63" color="#ef4444" />
      </div>

      {/* Footer stats */}
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

function MiniMockChart({ data, label, value, color }: { data: number[]; label: string; value: string; color: string }) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const w = 160;
  const h = 40;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`).join(" ");

  return (
    <div className="border border-[#1a1a1a] rounded-lg p-2.5">
      <div className="flex justify-between items-center mb-1">
        <span className="text-[9px] text-[#555]">{label}</span>
        <span className="text-[10px] font-mono" style={{ color }}>{value}</span>
      </div>
      <svg width="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="overflow-visible">
        <polyline fill="none" stroke={color} strokeWidth="1.5" points={points} opacity={0.8} />
        <circle cx={w} cy={h - ((data[data.length - 1] - min) / range) * h} r="2.5" fill={color} />
      </svg>
    </div>
  );
}

/* ── Feature: Experiment Tracking ──────────────── */

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
        <span className="text-[9px] px-2 py-0.5 border border-blue-900 text-blue-400 rounded">Compare Runs</span>
      </div>

      {/* Comparison table */}
      <div className="px-3 pt-2 pb-1">
        <div className="border border-blue-900/30 rounded-lg overflow-hidden mb-2">
          <div className="bg-blue-950/20 px-2.5 py-1 text-[9px] text-blue-400">Comparing Run #5 vs #4</div>
          <table className="w-full text-[9px]">
            <thead><tr className="border-b border-[#1a1a1a]">
              <th className="px-2 py-1 text-left text-[#555] font-medium">Metric</th>
              <th className="px-2 py-1 text-center font-mono text-[#888]">#5 <span className="text-[#555]">PPO v3</span></th>
              <th className="px-2 py-1 text-center font-mono text-[#888]">#4 <span className="text-[#555]">PPO v2</span></th>
            </tr></thead>
            <tbody>
              {[
                ["Reward", "78.2", "45.6", true],
                ["Success", "97%", "68%", true],
                ["Length", "55", "120", false],
              ].map(([label, v1, v2, higherBetter]) => (
                <tr key={String(label)} className="border-b border-[#1a1a1a]/30">
                  <td className="px-2 py-1 text-[#555]">{label}</td>
                  <td className="px-2 py-1 text-center font-mono text-green-400">{v1}</td>
                  <td className="px-2 py-1 text-center font-mono text-[#888]">{v2}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Run list */}
      <div className="px-3 pb-3 space-y-1">
        {runs.map(r => (
          <div key={r.id} className="flex items-center justify-between border border-[#1a1a1a] rounded-lg px-2.5 py-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[9px] font-mono text-[#666]">#{r.id}</span>
              <span className="text-[8px] px-1.5 py-0.5 bg-green-950 text-green-400 rounded">{r.status}</span>
              <span className="text-[9px] text-[#555]">{r.algo}</span>
              <span className="text-[9px] font-mono text-[#444]">{r.ver}</span>
              <span className="text-[9px] text-[#555]">{r.steps}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-[9px] font-mono text-green-400">R: {r.reward}</span>
              <span className="text-[9px] font-mono text-yellow-400">{r.success}</span>
              <span className="text-[9px] text-[#555]">{r.time}</span>
              <BarChart3 size={10} className="text-[#555]" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Feature: Research Lab ─────────────────────── */

function MockResearchLab() {
  return (
    <div className="border border-[#1a1a1a] rounded-xl bg-[#0a0a0a] overflow-hidden">
      <div className="border-b border-[#1a1a1a] px-3 py-2 flex items-center gap-2">
        <Brain size={12} className="text-[#555]" />
        <span className="text-[10px] text-[#888]">Research Lab — Multi-Agent Discussion</span>
      </div>

      <div className="p-3 space-y-2.5" style={{ minHeight: "260px" }}>
        {/* Agent messages */}
        <div className="flex gap-2">
          <div className="w-6 h-6 rounded-full bg-blue-950 flex items-center justify-center shrink-0">
            <span className="text-[8px] text-blue-400 font-bold">PA</span>
          </div>
          <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-2.5 text-[10px] flex-1">
            <p className="text-[9px] text-blue-400 font-medium mb-1">Prof. Aria — Principal Investigator</p>
            <p className="text-[#bbb]">I propose we investigate hierarchical reward shaping for multi-goal navigation. The gap between flat rewards and structured curricula remains underexplored.</p>
          </div>
        </div>

        <div className="flex gap-2">
          <div className="w-6 h-6 rounded-full bg-green-950 flex items-center justify-center shrink-0">
            <span className="text-[8px] text-green-400 font-bold">DM</span>
          </div>
          <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-2.5 text-[10px] flex-1">
            <p className="text-[9px] text-green-400 font-medium mb-1">Dr. Marcus — ML Engineer</p>
            <p className="text-[#bbb]">I can set up the experiment pipeline. We should test across 3 domains: grid-world, continuous control, and a custom robotics env. PPO with and without reward shaping as baseline.</p>
          </div>
        </div>

        <div className="flex gap-2">
          <div className="w-6 h-6 rounded-full bg-purple-950 flex items-center justify-center shrink-0">
            <span className="text-[8px] text-purple-400 font-bold">DE</span>
          </div>
          <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg p-2.5 text-[10px] flex-1">
            <p className="text-[9px] text-purple-400 font-medium mb-1">Dr. Elena — Academic Writer</p>
            <p className="text-[#bbb]">I found 12 relevant papers on ArXiv. The most cited approach uses potential-based shaping, but none combine it with hierarchical goals. This is a clear contribution angle.</p>
          </div>
        </div>

        {/* Phase indicator */}
        <div className="flex items-center gap-2 pt-1">
          <div className="flex-1 h-1 rounded-full bg-[#1a1a1a] overflow-hidden">
            <div className="h-full bg-gradient-to-r from-blue-600 via-green-600 to-purple-600 rounded-full" style={{ width: "35%" }} />
          </div>
          <span className="text-[9px] text-[#555]">Phase 2/7 — Ideation</span>
        </div>
      </div>
    </div>
  );
}
