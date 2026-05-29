import Link from "next/link";
import {
  ArrowRight, Sparkles, Play, FlaskConical,
  BarChart3, FileDown, Cpu, Terminal,
  Layers, Zap, Brain, TestTubeDiagonal,
  Send, CheckCircle, XCircle, Loader2,
  Download, Eye, Target, RefreshCw,
  GitBranch,
} from "lucide-react";
import { AuthRedirect } from "@/components/AuthRedirect";

export default function Home() {
  return (
    <div className="fade-in">
      <AuthRedirect to="/dashboard" />

      {/* ── Hero with grid background ── */}
      <section className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center px-4 md:px-6 text-center relative overflow-hidden">
        <HeroGrid />
        <div className="relative z-10">
          <h1 className="text-3xl sm:text-5xl md:text-7xl font-bold tracking-tight leading-[1.05] max-w-4xl">
            Design the Experience.<br />
            <span className="text-[#888]">Train the Intelligence.</span>
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-[#888] mt-6 max-w-2xl mx-auto leading-relaxed">
            Generate RL environments. Train agents. Run experiments. Create papers.
          </p>
          <p className="text-sm text-[#555] mt-4 max-w-xl mx-auto leading-relaxed">
            Describe what you need in plain English. The AI builds Gymnasium-compatible code,
            trains agents with SB3, tracks experiments, and writes research papers with real data.
          </p>
          <div className="flex flex-wrap gap-4 mt-10 justify-center">
            <Link href="/create" className="group px-7 py-3.5 bg-white text-black text-sm font-medium hover:bg-[#e5e5e5] transition-colors inline-flex items-center gap-2">
              START BUILDING <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
            </Link>
            <Link href="/environments" className="px-7 py-3.5 border border-[#333] text-sm hover:border-[#555] transition-colors text-[#888] hover:text-white">
              Learn More
            </Link>
          </div>
        </div>
      </section>

      {/* ── Pipeline: 3-col grid ── */}
      <section className="max-w-6xl mx-auto px-4 md:px-6 pb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-[#1a1a1a]">
          {[
            { num: "01", label: "Generate.", desc: "Describe your RL environment in plain English — including agent behavior. AI writes validated Gymnasium code.", color: "text-emerald-400" },
            { num: "02", label: "Train.", desc: "Continue, Fine-Tune, or Curriculum modes. Live charts, real metrics, configurable hyperparameters.", color: "text-blue-400" },
            { num: "03", label: "Research.", desc: "Hypothesis-first pipeline — design experiments, train agents, write academic papers with real data.", color: "text-amber-400" },
          ].map(s => (
            <div key={s.num} className="bg-[#0a0a0a] p-6 md:p-8">
              <p className="text-[11px] font-mono text-[#444] mb-3">{s.num}</p>
              <h3 className={`text-lg font-bold mb-2 ${s.color}`}>{s.label}</h3>
              <p className="text-sm text-[#888] leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Builder Section ── */}
      <section className="max-w-6xl mx-auto px-4 md:px-6 py-16">
        <div className="border border-emerald-900/40 rounded-sm">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-emerald-900/20">
            <div className="bg-[#0a0a0a] p-6 md:p-8 flex flex-col justify-between md:row-span-2">
              <div>
                <p className="text-emerald-400 text-sm font-mono mb-1">Builder.</p>
                <h2 className="text-2xl font-bold mb-4">AI Environment Builder</h2>
                <p className="text-sm text-[#888] leading-relaxed mb-6">
                  Describe your RL environment in natural language — including agent behavior,
                  self-observation, and adaptive mechanisms. The Architect Agent generates
                  Gymnasium-compatible code, validates with 8 automated tests, and offers
                  AI-powered suggestions for your next iteration.
                </p>
              </div>
              <Link href="/create" className="group inline-flex items-center gap-2 text-sm text-white hover:text-[#ccc] transition-colors">
                START BUILDING <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
            <div className="bg-[#0a0a0a] p-4 md:col-span-2">
              <MockChat />
            </div>
            <div className="bg-[#0a0a0a] p-4 md:col-span-2">
              <MockDashboard />
            </div>
          </div>
        </div>
      </section>

      {/* ── Training Section ── */}
      <section className="max-w-6xl mx-auto px-4 md:px-6 py-16">
        <div className="border border-blue-900/40 rounded-sm">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-blue-900/20">
            <div className="bg-[#0a0a0a] p-4 md:col-span-2 md:row-span-2">
              <MockTrainingCharts />
            </div>
            <div className="bg-[#0a0a0a] p-6 md:p-8 flex flex-col justify-between">
              <div>
                <p className="text-blue-400 text-sm font-mono mb-1">Training.</p>
                <h2 className="text-2xl font-bold mb-4">Agent Training & Advanced Modes</h2>
                <p className="text-sm text-[#888] leading-relaxed mb-6">
                  Train with <strong className="text-white">Continue</strong>, <strong className="text-white">Fine-Tune</strong>,
                  or <strong className="text-white">Curriculum Learning</strong>. Configurable hyperparameters,
                  live training curves, evaluation metrics, and ETA.
                </p>
              </div>
              <Link href="/create" className="group inline-flex items-center gap-2 text-sm text-white hover:text-[#ccc] transition-colors">
                SEE HOW IT WORKS <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
            <div className="bg-[#0a0a0a] p-4">
              <MockTrainingModes />
            </div>
          </div>
        </div>
      </section>

      {/* ── Experiments Section ── */}
      <section className="max-w-6xl mx-auto px-4 md:px-6 py-16">
        <div className="border border-purple-900/40 rounded-sm">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-purple-900/20">
            <div className="bg-[#0a0a0a] p-6 md:p-8 flex flex-col justify-between md:row-span-2">
              <div>
                <p className="text-purple-400 text-sm font-mono mb-1">Experiments.</p>
                <h2 className="text-2xl font-bold mb-4">Track & Compare</h2>
                <p className="text-sm text-[#888] leading-relaxed mb-6">
                  Every training run is versioned. Compare runs side-by-side,
                  expand experiment history with full metrics, training curves,
                  evaluation episodes, and hyperparameter details. Export to GitHub or download reports.
                </p>
              </div>
              <Link href="/create" className="group inline-flex items-center gap-2 text-sm text-white hover:text-[#ccc] transition-colors">
                VIEW EXPERIMENTS <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
            <div className="bg-[#0a0a0a] p-4 md:col-span-2">
              <MockExperiments />
            </div>
            <div className="bg-[#0a0a0a] p-4 md:col-span-2">
              <MockComparison />
            </div>
          </div>
        </div>
      </section>

      {/* ── Research Lab Section ── */}
      <section className="max-w-6xl mx-auto px-4 md:px-6 py-16">
        <div className="border border-amber-900/40 rounded-sm">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-amber-900/20">
            <div className="bg-[#0a0a0a] p-4 md:col-span-2 md:row-span-2">
              <MockResearchLab />
            </div>
            <div className="bg-[#0a0a0a] p-6 md:p-8 flex flex-col justify-between">
              <div>
                <p className="text-amber-400 text-sm font-mono mb-1">Research Lab.</p>
                <h2 className="text-2xl font-bold mb-4">Hypothesis to Paper</h2>
                <p className="text-sm text-[#888] leading-relaxed mb-6">
                  Two AI agents formulate a hypothesis, design experiments, train real agents,
                  analyze results, and write academic papers with inline figures and literature
                  references — downloadable as PDF.
                </p>
              </div>
              <Link href="/research" className="group inline-flex items-center gap-2 text-sm text-white hover:text-[#ccc] transition-colors">
                EXPLORE LAB <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
            <div className="bg-[#0a0a0a] p-4">
              <MockPaperPreview />
            </div>
          </div>
        </div>
      </section>

      {/* ── Capabilities strip ── */}
      <section className="max-w-6xl mx-auto px-4 md:px-6 py-12">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-px bg-[#1a1a1a]">
          {[
            { icon: <Layers size={16} />, label: "Gymnasium v0.29+", desc: "Industry-standard RL framework" },
            { icon: <TestTubeDiagonal size={16} />, label: "8 Automated Tests", desc: "Every environment validated" },
            { icon: <Zap size={16} />, label: "PPO / SAC / DQN", desc: "Leading RL algorithms" },
            { icon: <Play size={16} />, label: "Curriculum Learning", desc: "Auto-increase difficulty" },
            { icon: <Brain size={16} />, label: "AI Smart Suggestions", desc: "Next-step recommendations" },
            { icon: <FileDown size={16} />, label: "Research Papers", desc: "Academic quality, PDF export" },
            { icon: <GitBranch size={16} />, label: "Version Control", desc: "Every iteration tracked" },
            { icon: <Terminal size={16} />, label: "GitHub Export", desc: "Push to your repository" },
          ].map(c => (
            <div key={c.label} className="bg-[#0a0a0a] p-5">
              <div className="text-[#555] mb-2">{c.icon}</div>
              <p className="text-xs font-medium text-white mb-0.5">{c.label}</p>
              <p className="text-[11px] text-[#555]">{c.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="max-w-6xl mx-auto px-4 md:px-6 py-24 text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready to build?</h2>
        <p className="text-[#666] mb-10 max-w-md mx-auto">
          Describe your environment, train an agent, and publish your research. All in one platform.
        </p>
        <div className="flex flex-wrap gap-4 justify-center">
          <Link href="/create" className="group inline-flex items-center gap-2 px-7 py-3.5 bg-white text-black text-sm font-medium hover:bg-[#e5e5e5] transition-colors">
            Create Your First Environment <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <Link href="/research" className="inline-flex items-center gap-2 px-7 py-3.5 border border-[#333] text-sm hover:border-[#555] transition-colors text-[#888] hover:text-white">
            Explore Research Lab
          </Link>
        </div>
      </section>
    </div>
  );
}

/* ═══════════════════════════════════════════
   HERO GRID BACKGROUND
   ═══════════════════════════════════════════ */

function HeroGrid() {
  const cols = 20;
  const rows = 12;
  const cell = 60;
  const w = cols * cell;
  const h = rows * cell;

  const dotColors = ["#34d399", "#60a5fa", "#a78bfa", "#fbbf24"];

  const dots: { cx: number; cy: number; color: string; r: number; opacity: number }[] = [];
  const rng = (seed: number) => {
    let s = seed;
    return () => { s = (s * 16807 + 0) % 2147483647; return s / 2147483647; };
  };
  const rand = rng(42);
  for (let row = 0; row <= rows; row++) {
    for (let col = 0; col <= cols; col++) {
      if (rand() < 0.12) {
        dots.push({
          cx: col * cell,
          cy: row * cell,
          color: dotColors[Math.floor(rand() * dotColors.length)],
          r: 2 + rand() * 3,
          opacity: 0.4 + rand() * 0.5,
        });
      }
    }
  }

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none flex items-center justify-center">
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="opacity-100" style={{ minWidth: w, minHeight: h }}>
        {/* Grid lines — white */}
        {Array.from({ length: rows + 1 }, (_, i) => (
          <line key={`h${i}`} x1={0} y1={i * cell} x2={w} y2={i * cell} stroke="white" strokeWidth="0.5" opacity={0.18} />
        ))}
        {Array.from({ length: cols + 1 }, (_, i) => (
          <line key={`v${i}`} x1={i * cell} y1={0} x2={i * cell} y2={h} stroke="white" strokeWidth="0.5" opacity={0.18} />
        ))}
        {/* Colored dots at intersections */}
        {dots.map((d, i) => (
          <g key={i}>
            <circle cx={d.cx} cy={d.cy} r={d.r * 3} fill={d.color} opacity={d.opacity * 0.15} />
            <circle cx={d.cx} cy={d.cy} r={d.r} fill={d.color} opacity={d.opacity} />
            <circle cx={d.cx} cy={d.cy} r={d.r * 0.4} fill="white" opacity={d.opacity * 0.8} />
          </g>
        ))}
      </svg>
      {/* Fade edges to black */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-transparent to-black/80" />
      <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-transparent to-black/70" />
    </div>
  );
}

/* ═══════════════════════════════════════════
   MOCK UI COMPONENTS
   ═══════════════════════════════════════════ */

function MockChat() {
  return (
    <div className="space-y-3" style={{ minHeight: 280 }}>
      <div className="flex items-center gap-2 mb-3">
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
        <span className="text-[10px] font-mono text-[#555]">builder / drone-navigation-v3</span>
      </div>
      <div className="ml-8 bg-[#111] rounded-lg p-3 text-[11px] text-[#ccc]">
        Create a drone navigation environment with obstacle avoidance and wind perturbation
      </div>
      <div className="mr-8 border border-[#1a1a1a] rounded-lg p-3 text-[11px]">
        <p className="text-[#bbb] mb-2">Created DroneNav-v1 with 8 distance sensors, -5.0 collision penalty, and goal bonus +50.0. Gaussian wind perturbation N(0, 0.3) applied each step.</p>
        <div className="flex gap-1 flex-wrap">
          {["syntax","import","reset","step","obs","action","reward","determ."].map(t => (
            <span key={t} className="text-[8px] px-1.5 py-0.5 bg-emerald-950/50 text-emerald-400 rounded font-mono">{t}</span>
          ))}
        </div>
      </div>
      <div className="ml-8 bg-[#111] rounded-lg p-3 text-[11px] text-[#ccc]">
        The agent should store its last 5 actions and observe its own strategy effectiveness
      </div>
      <div className="mr-8 border border-[#1a1a1a] rounded-lg p-3 text-[11px]">
        <p className="text-[#bbb] mb-2">Added self-observation: action history buffer [5x4], strategy effectiveness metric, and stagnation detection. Obs space expanded to [32].</p>
        <div className="flex gap-1 flex-wrap">
          {["syntax","import","reset","step","obs","action","reward"].map(t => (
            <span key={t} className="text-[8px] px-1.5 py-0.5 bg-emerald-950/50 text-emerald-400 rounded font-mono">{t}</span>
          ))}
          <span className="text-[8px] px-1.5 py-0.5 bg-red-950/50 text-red-400 rounded font-mono">determ.</span>
        </div>
      </div>
      <div className="flex gap-1.5 pt-1 flex-wrap">
        {["Add penalty shaping","Increase obs dims","Train with SAC","Raise difficulty"].map(s => (
          <span key={s} className="text-[8px] px-2.5 py-1 border border-[#222] rounded-full text-[#555] font-mono">{s}</span>
        ))}
      </div>
    </div>
  );
}

function MockDashboard() {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <div className="w-2 h-2 rounded-full bg-emerald-500" />
        <span className="text-[10px] text-[#888]">7/8 Tests Passing</span>
        <span className="text-[10px] text-[#555] ml-auto font-mono">v3 · Box[32] → Box[4]</span>
      </div>
      <div className="grid grid-cols-4 gap-1.5 mb-4">
        {["syntax","import","reset","step","obs_space","action_space","reward","determinism"].map((t, i) => (
          <div key={t} className={`rounded p-2 text-center ${i < 7 ? "bg-emerald-950/20 border border-emerald-900/20" : "bg-red-950/20 border border-red-900/20"}`}>
            <div className="flex items-center justify-center gap-1">
              {i < 7 ? <CheckCircle size={9} className="text-emerald-400" /> : <XCircle size={9} className="text-red-400" />}
              <span className="text-[9px] font-mono">{t}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-2">
        <div className="border border-[#1a1a1a] rounded-lg p-3">
          <div className="flex items-center gap-1.5 mb-2"><Eye size={11} className="text-blue-400" /><span className="text-[10px] font-medium">Observation</span></div>
          <div className="space-y-1 text-[10px]">
            <div className="flex justify-between"><span className="text-[#555]">Type</span><span className="font-mono">Box</span></div>
            <div className="flex justify-between"><span className="text-[#555]">Shape</span><span className="font-mono">[32]</span></div>
            <div className="flex justify-between"><span className="text-[#555]">Range</span><span className="font-mono">[-1, 1]</span></div>
          </div>
        </div>
        <div className="border border-[#1a1a1a] rounded-lg p-3">
          <div className="flex items-center gap-1.5 mb-2"><Zap size={11} className="text-purple-400" /><span className="text-[10px] font-medium">Action</span></div>
          <div className="space-y-1 text-[10px]">
            <div className="flex justify-between"><span className="text-[#555]">Type</span><span className="font-mono">Box</span></div>
            <div className="flex justify-between"><span className="text-[#555]">Shape</span><span className="font-mono">[4]</span></div>
            <div className="flex justify-between"><span className="text-[#555]">Range</span><span className="font-mono">[-1, 1]</span></div>
          </div>
        </div>
        <div className="border border-[#1a1a1a] rounded-lg p-3">
          <div className="flex items-center gap-1.5 mb-2"><Target size={11} className="text-yellow-400" /><span className="text-[10px] font-medium">Reward</span></div>
          <p className="text-[10px] text-[#888] mb-1.5">Distance + collision + goal</p>
          <div className="flex flex-wrap gap-1">
            {["dist","collision","goal"].map(c => (
              <span key={c} className="text-[8px] px-1.5 py-0.5 bg-yellow-950/30 text-yellow-400 rounded font-mono">{c}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function MockTrainingCharts() {
  const rewardData = [12, 18, 15, 22, 28, 25, 32, 38, 35, 42, 48, 52, 55, 58, 62, 65, 68, 72, 75, 78];
  const lengthData = [200, 185, 190, 170, 155, 160, 140, 125, 130, 110, 95, 85, 80, 75, 72, 68, 65, 60, 58, 55];
  const successData = [0, 0, 0.1, 0.1, 0.2, 0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.88, 0.9, 0.92, 0.95, 0.97];
  const lossData = [2.5, 2.3, 2.1, 1.9, 1.8, 1.6, 1.5, 1.3, 1.2, 1.1, 1.0, 0.9, 0.85, 0.8, 0.75, 0.72, 0.7, 0.68, 0.65, 0.63];

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Loader2 size={12} className="animate-spin text-blue-400" />
          <span className="text-[11px] text-[#888]">Training in progress</span>
        </div>
        <span className="text-[11px] font-mono text-white">73.5K / 100K</span>
      </div>
      <div className="relative h-1 bg-[#1a1a1a] rounded-full overflow-hidden mb-4">
        <div className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-600 to-blue-400 rounded-full" style={{ width: "73.5%" }} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <ChartCard data={rewardData} label="Episode Reward" value="78.2" color="#22c55e" />
        <ChartCard data={lengthData} label="Episode Length" value="55" color="#3b82f6" />
        <ChartCard data={successData} label="Success Rate" value="97%" color="#eab308" />
        <ChartCard data={lossData} label="Policy Loss" value="0.63" color="#ef4444" />
      </div>
      <div className="flex gap-5 mt-3 text-[10px] text-[#555] font-mono">
        <span>Step: 73,500</span>
        <span>Episodes: 1,247</span>
        <span>FPS: 4,280</span>
        <span>ETA: 6s</span>
        <span className="ml-auto text-[#888]">PPO</span>
      </div>
    </div>
  );
}

function ChartCard({ data, label, value, color }: { data: number[]; label: string; value: string; color: string }) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const w = 200, h = 50;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`).join(" ");

  return (
    <div className="border border-[#1a1a1a] rounded-lg p-3">
      <div className="flex justify-between items-center mb-2">
        <span className="text-[10px] text-[#555]">{label}</span>
        <span className="text-[11px] font-mono font-medium" style={{ color }}>{value}</span>
      </div>
      <svg width="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="overflow-visible">
        <polyline fill="none" stroke={color} strokeWidth="1.5" points={points} opacity={0.7} />
        <circle cx={w} cy={h - ((data[data.length - 1] - min) / range) * h} r="3" fill={color} />
      </svg>
    </div>
  );
}

function MockTrainingModes() {
  return (
    <div>
      <p className="text-[10px] font-mono text-[#555] mb-3">Training Modes</p>
      <div className="space-y-2">
        {[
          { label: "Continue", desc: "Same settings, resume training", active: true, icon: <Play size={12} /> },
          { label: "Fine-Tune", desc: "Low LR, short training", active: false, icon: <RefreshCw size={12} /> },
          { label: "Curriculum", desc: "Auto-increase difficulty", active: false, icon: <Sparkles size={12} /> },
        ].map(m => (
          <div key={m.label} className={`rounded-lg p-3 border flex items-center gap-3 ${m.active ? "border-white/20 bg-[#111]" : "border-[#1a1a1a]"}`}>
            <div className={`${m.active ? "text-white" : "text-[#444]"}`}>{m.icon}</div>
            <div>
              <p className={`text-[11px] font-medium ${m.active ? "text-white" : "text-[#555]"}`}>{m.label}</p>
              <p className="text-[10px] text-[#444]">{m.desc}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-2 mt-3 text-[10px]">
        <div className="border border-[#1a1a1a] rounded p-2">
          <p className="text-[#555] text-[9px] mb-0.5">Algorithm</p>
          <p className="font-mono text-white">PPO</p>
        </div>
        <div className="border border-[#1a1a1a] rounded p-2">
          <p className="text-[#555] text-[9px] mb-0.5">Timesteps</p>
          <p className="font-mono text-white">100K</p>
        </div>
        <div className="border border-[#1a1a1a] rounded p-2">
          <p className="text-[#555] text-[9px] mb-0.5">LR</p>
          <p className="font-mono text-white">3e-4</p>
        </div>
      </div>
    </div>
  );
}

function MockExperiments() {
  const runs = [
    { id: 5, algo: "PPO", ver: "v3", steps: "100K", reward: "78.2", success: "97%", status: "completed" },
    { id: 4, algo: "PPO", ver: "v2", steps: "100K", reward: "45.6", success: "68%", status: "completed" },
    { id: 3, algo: "SAC", ver: "v2", steps: "50K", reward: "38.1", success: "52%", status: "completed" },
    { id: 2, algo: "PPO", ver: "v1", steps: "50K", reward: "12.4", success: "15%", status: "completed" },
  ];

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <FlaskConical size={12} className="text-purple-400" />
        <span className="text-[10px] font-mono text-[#555]">experiments / 4 runs</span>
        <span className="text-[9px] px-2 py-0.5 border border-purple-900/50 text-purple-400 rounded ml-auto font-mono">Compare</span>
      </div>
      <div className="space-y-1.5">
        {runs.map(r => (
          <div key={r.id} className="flex items-center justify-between border border-[#1a1a1a] rounded-lg px-3 py-2">
            <div className="flex items-center gap-2.5">
              <span className="text-[10px] font-mono text-[#666]">#{r.id}</span>
              <span className="text-[9px] px-1.5 py-0.5 bg-emerald-950/50 text-emerald-400 rounded font-mono">{r.status}</span>
              <span className="text-[10px] text-[#888]">{r.algo}</span>
              <span className="text-[10px] font-mono text-[#444]">{r.ver}</span>
              <span className="text-[10px] text-[#555]">{r.steps}</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-[10px] font-mono text-emerald-400">R: {r.reward}</span>
              <span className="text-[10px] font-mono text-yellow-400">{r.success}</span>
              <BarChart3 size={11} className="text-[#555]" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MockComparison() {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <BarChart3 size={12} className="text-purple-400" />
        <span className="text-[10px] font-mono text-[#555]">comparison / #5 vs #4</span>
      </div>
      <div className="border border-purple-900/20 rounded-lg overflow-hidden">
        <div className="bg-purple-950/10 px-3 py-1.5 text-[10px] text-purple-400 font-mono">Run #5 (PPO v3) vs Run #4 (PPO v2)</div>
        <table className="w-full text-[10px]">
          <thead><tr className="border-b border-[#1a1a1a]">
            <th className="px-3 py-1.5 text-left text-[#555] font-medium">Metric</th>
            <th className="px-3 py-1.5 text-center font-mono text-[#888]">#5</th>
            <th className="px-3 py-1.5 text-center font-mono text-[#888]">#4</th>
            <th className="px-3 py-1.5 text-center text-[#555]">Delta</th>
          </tr></thead>
          <tbody>
            {[
              ["Reward", "78.2", "45.6", "+71.5%"],
              ["Success Rate", "97%", "68%", "+42.6%"],
              ["Ep. Length", "55", "120", "-54.2%"],
              ["Policy Loss", "0.63", "1.24", "-49.2%"],
            ].map(([label, v1, v2, delta]) => (
              <tr key={String(label)} className="border-b border-[#1a1a1a]/30">
                <td className="px-3 py-1.5 text-[#555]">{label}</td>
                <td className="px-3 py-1.5 text-center font-mono text-emerald-400">{v1}</td>
                <td className="px-3 py-1.5 text-center font-mono text-[#888]">{v2}</td>
                <td className="px-3 py-1.5 text-center font-mono text-emerald-400">{delta}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function MockResearchLab() {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Brain size={12} className="text-amber-400" />
        <span className="text-[10px] font-mono text-[#555]">research / curriculum-nav-study</span>
      </div>

      <div className="space-y-3">
        <div className="flex gap-2.5">
          <div className="w-7 h-7 rounded-full bg-amber-950 flex items-center justify-center shrink-0 mt-0.5">
            <span className="text-[10px] text-amber-400 font-bold">S</span>
          </div>
          <div className="border border-[#1a1a1a] rounded-lg p-3 text-[11px] flex-1">
            <p className="text-[10px] text-amber-400 font-mono mb-1">Sage — Hypothesis</p>
            <p className="text-[#bbb]">&ldquo;Does curriculum reward shaping outperform flat rewards in multi-goal navigation?&rdquo; Defined env specs: 2D grid, 4 goals, progressive difficulty scaling. Agent must generalize across difficulty levels.</p>
          </div>
        </div>
        <div className="flex gap-2.5">
          <div className="w-7 h-7 rounded-full bg-blue-950 flex items-center justify-center shrink-0 mt-0.5">
            <span className="text-[10px] text-blue-400 font-bold">A</span>
          </div>
          <div className="border border-[#1a1a1a] rounded-lg p-3 text-[11px] flex-1">
            <p className="text-[10px] text-blue-400 font-mono mb-1">Atlas — Design & Experiment</p>
            <p className="text-[#bbb]">Built <span className="text-emerald-400 font-mono">CurriculumNav-v1</span> — 8/8 tests passed. Training PPO across Continue → Fine-Tune → Curriculum. Results: 92% success, mean reward 78.2, episode length 55.</p>
          </div>
        </div>
        <div className="flex gap-2.5">
          <div className="w-7 h-7 rounded-full bg-amber-950 flex items-center justify-center shrink-0 mt-0.5">
            <span className="text-[10px] text-amber-400 font-bold">S</span>
          </div>
          <div className="border border-[#1a1a1a] rounded-lg p-3 text-[11px] flex-1">
            <p className="text-[10px] text-amber-400 font-mono mb-1">Sage — Research & Write</p>
            <p className="text-[#bbb]">Found 14 supporting papers via academic literature search. Writing paper with inline training curves, evaluation tables, and hyperparameter appendix. PDF download ready.</p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-1.5 mt-4">
        {["Hypothesis","Design","Experiment","Analyze","Write","Review"].map((p, i) => (
          <div key={p} className="flex items-center flex-1 gap-1">
            <div className={`h-1.5 flex-1 rounded-full ${i < 5 ? "bg-amber-800" : "bg-amber-500 animate-pulse"}`} />
          </div>
        ))}
        <span className="text-[9px] text-[#555] font-mono ml-1 shrink-0">6/6</span>
      </div>
    </div>
  );
}

function MockPaperPreview() {
  return (
    <div>
      <p className="text-[10px] font-mono text-[#555] mb-3">Generated Paper</p>
      <div className="border border-[#1a1a1a] rounded-lg p-4 space-y-3">
        <div>
          <p className="text-[11px] font-bold text-white leading-tight">Curriculum Reward Shaping for Multi-Goal Navigation: A Comparative Study</p>
          <p className="text-[9px] text-[#555] mt-1 font-mono">Sage & Atlas — kualia.ai Research Lab</p>
        </div>
        <div className="border-t border-[#1a1a1a] pt-2">
          <p className="text-[9px] text-[#888] leading-relaxed">
            <span className="text-[#555] font-medium">Abstract:</span> We investigate whether curriculum-based reward
            shaping improves agent performance in multi-goal navigation tasks compared to flat reward structures...
          </p>
        </div>
        <div className="flex gap-3 text-[9px] text-[#555]">
          <span className="flex items-center gap-1"><BarChart3 size={9} />4 figures</span>
          <span className="flex items-center gap-1"><FlaskConical size={9} />3 experiments</span>
          <span className="flex items-center gap-1"><FileDown size={9} />14 refs</span>
        </div>
        <div className="flex items-center gap-2 pt-1">
          <span className="text-[8px] px-2 py-0.5 bg-amber-950/50 text-amber-400 rounded font-mono">PDF Ready</span>
          <span className="text-[8px] px-2 py-0.5 border border-[#222] text-[#555] rounded font-mono">Download</span>
        </div>
      </div>
    </div>
  );
}
