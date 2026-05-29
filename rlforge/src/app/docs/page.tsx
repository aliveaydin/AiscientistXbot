"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  BookOpen,
  Layers,
  Brain,
  FlaskConical,
  ChevronRight,
  ChevronDown,
  Menu,
  X,
  Clipboard,
  Check,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface SidebarItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  children?: SidebarItem[];
}

/* ------------------------------------------------------------------ */
/*  Sidebar tree                                                       */
/* ------------------------------------------------------------------ */

const sidebarTree: SidebarItem[] = [
  {
    id: "getting-started",
    label: "Getting Started",
    icon: <BookOpen size={16} />,
    children: [
      { id: "introduction", label: "Introduction" },
      { id: "quick-start", label: "Quick Start" },
    ],
  },
  {
    id: "environment-builder",
    label: "Environment Builder",
    icon: <Layers size={16} />,
    children: [
      { id: "builder-overview", label: "Overview" },
      { id: "generating-environments", label: "Generating Environments" },
      { id: "chat-iteration", label: "Chat Iteration" },
      { id: "version-control", label: "Version Control" },
      { id: "export", label: "Export (ZIP, GitHub)" },
    ],
  },
  {
    id: "agent-training",
    label: "Agent Training",
    icon: <Brain size={16} />,
    children: [
      { id: "algorithms", label: "Algorithms (PPO, SAC, DQN)" },
      { id: "training-configuration", label: "Configuration & Hyperparameters" },
      { id: "training-modes", label: "Training Modes" },
      { id: "monitoring-curves", label: "Monitoring & Curves" },
    ],
  },
  {
    id: "research-lab",
    label: "Research Lab",
    icon: <FlaskConical size={16} />,
    children: [
      { id: "research-overview", label: "Overview" },
      { id: "phases-pipeline", label: "Phases & Pipeline" },
      { id: "paper-generation", label: "Paper Generation" },
    ],
  },
];

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function allIds(items: SidebarItem[]): string[] {
  const out: string[] = [];
  for (const item of items) {
    if (item.children) {
      for (const child of item.children) out.push(child.id);
    }
  }
  return out;
}

/* ------------------------------------------------------------------ */
/*  CodeBlock                                                          */
/* ------------------------------------------------------------------ */

function CodeBlock({ children, language }: { children: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(() => {
    navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [children]);

  return (
    <div className="relative group my-4">
      <div className="flex items-center justify-between px-4 py-2 bg-[#111] border border-[#1a1a1a] rounded-t-lg">
        <span className="text-xs text-[#555] font-mono">{language ?? "python"}</span>
        <button
          onClick={copy}
          className="text-[#555] hover:text-white transition-colors"
          aria-label="Copy code"
        >
          {copied ? <Check size={14} /> : <Clipboard size={14} />}
        </button>
      </div>
      <pre className="bg-[#0a0a0a] border border-t-0 border-[#1a1a1a] rounded-b-lg p-4 overflow-x-auto text-sm leading-relaxed font-mono text-[#ccc]">
        <code>{children}</code>
      </pre>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Sidebar item                                                       */
/* ------------------------------------------------------------------ */

function SidebarNode({
  item,
  activeId,
  onNavigate,
  expandedSections,
  toggleSection,
}: {
  item: SidebarItem;
  activeId: string;
  onNavigate: (id: string) => void;
  expandedSections: Record<string, boolean>;
  toggleSection: (id: string) => void;
}) {
  const hasChildren = !!item.children?.length;
  const isExpanded = expandedSections[item.id] ?? false;
  const isChildActive = hasChildren && item.children!.some((c) => c.id === activeId);

  return (
    <div>
      <button
        onClick={() => {
          if (hasChildren) toggleSection(item.id);
          else onNavigate(item.id);
        }}
        className={`w-full flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors ${
          !hasChildren && activeId === item.id
            ? "bg-white/10 text-white"
            : isChildActive
              ? "text-white"
              : "text-[#888] hover:text-white hover:bg-white/5"
        }`}
      >
        {item.icon && <span className="shrink-0">{item.icon}</span>}
        <span className="truncate flex-1 text-left">{item.label}</span>
        {hasChildren && (
          <span className="shrink-0 text-[#555]">
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </span>
        )}
      </button>

      {hasChildren && isExpanded && (
        <div className="ml-5 mt-0.5 border-l border-[#1a1a1a] pl-2 space-y-0.5">
          {item.children!.map((child) => (
            <SidebarNode
              key={child.id}
              item={child}
              activeId={activeId}
              onNavigate={onNavigate}
              expandedSections={expandedSections}
              toggleSection={toggleSection}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */

export default function DocsPage() {
  const [activeId, setActiveId] = useState("introduction");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = {};
    sidebarTree.forEach((s) => (init[s.id] = true));
    return init;
  });

  const contentRef = useRef<HTMLDivElement>(null);

  const toggleSection = useCallback((id: string) => {
    setExpandedSections((prev) => ({ ...prev, [id]: !prev[id] }));
  }, []);

  const navigateTo = useCallback(
    (id: string) => {
      setActiveId(id);
      setMobileOpen(false);
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    },
    [],
  );

  useEffect(() => {
    const ids = allIds(sidebarTree);
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
            break;
          }
        }
      },
      { rootMargin: "-80px 0px -60% 0px", threshold: 0.1 },
    );

    ids.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  /* ---------------------------------------------------------------- */
  /*  Render                                                           */
  /* ---------------------------------------------------------------- */

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      {/* Mobile toggle */}
      <button
        className="fixed top-[72px] left-4 z-50 lg:hidden bg-[#111] border border-[#1a1a1a] rounded-lg p-2"
        onClick={() => setMobileOpen((v) => !v)}
        aria-label="Toggle docs sidebar"
      >
        {mobileOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed top-[64px] left-0 z-40 h-[calc(100vh-64px)] w-[260px] bg-[#0a0a0a] border-r border-[#1a1a1a] overflow-y-auto transition-transform duration-200 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0 lg:sticky lg:top-[64px] lg:shrink-0`}
      >
        <nav className="p-4 space-y-1">
          <div className="flex items-center gap-2 px-3 py-3 mb-2">
            <BookOpen size={18} className="text-white" />
            <span className="text-sm font-semibold text-white">Documentation</span>
          </div>
          {sidebarTree.map((item) => (
            <SidebarNode
              key={item.id}
              item={item}
              activeId={activeId}
              onNavigate={navigateTo}
              expandedSections={expandedSections}
              toggleSection={toggleSection}
            />
          ))}
        </nav>
      </aside>

      {/* Overlay on mobile */}
      {mobileOpen && (
        <div className="fixed inset-0 z-30 bg-black/60 lg:hidden" onClick={() => setMobileOpen(false)} />
      )}

      {/* Main content */}
      <div ref={contentRef} className="flex-1 min-w-0 px-6 md:px-12 lg:px-16 py-12 max-w-4xl mx-auto">
        {/* ============================================================ */}
        {/*  GETTING STARTED                                             */}
        {/* ============================================================ */}

        <section id="introduction" className="scroll-mt-24 mb-20">
          <h1 className="text-3xl font-bold text-white mb-3">Introduction</h1>
          <p className="text-[#bbb] leading-relaxed mb-4">
            kualia.ai is an end-to-end reinforcement learning experiment platform.
            It lets you describe an environment in plain English, generates a fully
            compliant Gymnasium environment, and gives you a visual builder to
            iterate on reward functions, observation spaces, and dynamics — all
            through a conversational interface.
          </p>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Once your environment is ready, kualia trains agents using
            state-of-the-art algorithms from Stable-Baselines3, streams real-time
            training curves, and lets you download or continue training your models.
          </p>
          <p className="text-[#bbb] leading-relaxed mb-4">
            The Research Lab extends the platform into a full experiment pipeline:
            define hypotheses, run multi-phase experiments, and auto-generate
            publishable papers from your results.
          </p>
          <div className="border border-[#1a1a1a] rounded-lg p-4 bg-[#0a0a0a] my-6">
            <p className="text-sm text-[#888]">
              <strong className="text-white">Core capabilities:</strong> Environment generation from text or
              papers · Conversational builder · PPO / SAC / DQN training ·
              Real-time monitoring · Version control · Research pipeline ·
              Paper generation with inline figures
            </p>
          </div>
        </section>

        <section id="quick-start" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Quick Start</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Get from zero to a trained agent in under five minutes.
          </p>

          <h3 className="text-lg font-semibold text-white mt-8 mb-3">1. Create an account</h3>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Sign up with Google or GitHub. You&apos;ll land on your Dashboard immediately.
          </p>

          <h3 className="text-lg font-semibold text-white mt-8 mb-3">2. Describe your environment</h3>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Use the Environment Builder to describe what you need in plain English.
            The AI Architect Agent generates Gymnasium-compatible code, validates it with 8 automated tests,
            and lets you iterate through chat. AI smart suggestions help you refine.
          </p>

          <h3 className="text-lg font-semibold text-white mt-8 mb-3">3. Train an agent</h3>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Choose an algorithm (PPO, SAC, DQN), configure hyperparameters, and hit train.
            Use Continue, Fine-Tune, or Curriculum modes to improve your agent.
            Watch live progress with real-time reward curves.
          </p>

          <h3 className="text-lg font-semibold text-white mt-8 mb-3">4. Run research (optional)</h3>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Use the Research Lab to formulate a hypothesis, run real experiments,
            and generate a complete academic paper with inline training figures —
            downloadable as PDF.
          </p>
        </section>

        {/* ============================================================ */}
        {/*  ENVIRONMENT BUILDER                                         */}
        {/* ============================================================ */}

        <section id="builder-overview" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Environment Builder — Overview</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            The Environment Builder is a conversational interface that lets you
            create, modify, and refine Gymnasium-compatible RL environments without
            writing code manually. It combines an AI code generation backend with a
            live preview of the environment code.
          </p>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Every environment generated through kualia follows the standard
            Gymnasium interface — <code className="text-white bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm">reset()</code>,{" "}
            <code className="text-white bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm">step(action)</code>,{" "}
            <code className="text-white bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm">render()</code> — so it is compatible with
            every major RL library (Stable-Baselines3, RLlib, CleanRL, etc.).
          </p>
          <p className="text-[#bbb] leading-relaxed">
            The builder stores a full version history of every change, so you
            can roll back at any time.
          </p>
        </section>

        <section id="generating-environments" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Generating Environments</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            There are three ways to create an environment on kualia:
          </p>

          <h3 className="text-lg font-semibold text-white mt-6 mb-2">Natural-language description</h3>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Describe your environment in plain English. kualia&apos;s AI generates the
            full Gymnasium code including observation space, action space, reward
            function, and dynamics. You can specify the domain (robotics, finance,
            games, etc.) and difficulty level.
          </p>

          <h3 className="text-lg font-semibold text-white mt-8 mb-2">From a research paper</h3>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Upload a PDF paper and kualia extracts the environment specification,
            reward structure, and constraints to generate a matching implementation.
            This is useful for reproducing environments from published research.
          </p>

          <h3 className="text-lg font-semibold text-white mt-8 mb-2">Fork an existing environment</h3>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Start from any published environment in the catalog and fork it with
            your own modifications. This is the fastest way to create a variant
            of an existing environment.
          </p>

          <div className="border border-[#1a1a1a] rounded-lg p-4 bg-[#0a0a0a] my-6">
            <p className="text-sm text-[#888]">
              <strong className="text-white">Validation:</strong> Every generated environment goes through 8 automated tests
              covering initialization, reset, step execution, observation/action space compliance, reward
              structure, and Gymnasium compatibility. If any test fails, kualia auto-fixes the code.
            </p>
          </div>
        </section>

        <section id="chat-iteration" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Chat Iteration</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            After initial generation, the builder enters chat mode. You can ask
            for any modification — changing the reward function, adjusting the
            observation space, adding visualization, tweaking dynamics — and the AI
            updates the environment code accordingly.
          </p>
          <p className="text-[#bbb] leading-relaxed mb-4">
            <strong className="text-white">Example requests you can make:</strong>
          </p>
          <ul className="list-disc list-inside text-[#bbb] space-y-2 mb-4 ml-2">
            <li>&quot;Make the reward sparse: +1 only when the agent reaches the goal&quot;</li>
            <li>&quot;Add obstacles that move randomly every 100 steps&quot;</li>
            <li>&quot;Increase the observation space to include velocity information&quot;</li>
            <li>&quot;Change the action space from discrete to continuous&quot;</li>
            <li>&quot;Add a time penalty to encourage faster solutions&quot;</li>
          </ul>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Each message creates a new version of the environment. The AI also provides
            smart suggestions after each change, helping you think about what to iterate
            on next — like adjusting reward shaping, adding curriculum difficulty, or
            refining termination conditions.
          </p>
          <p className="text-[#bbb] leading-relaxed">
            You can view the full conversation history to understand how the
            environment evolved over time.
          </p>
        </section>

        <section id="version-control" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Version Control</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Every chat iteration creates a new version of your environment. kualia
            stores the full version tree so you can roll back to any previous
            state at any time.
          </p>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Rollback does not delete later versions — it creates a new version
            based on the target, so you can always go forward again. Think of it
            like <code className="text-white bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm">git revert</code> rather
            than a hard reset.
          </p>
          <p className="text-[#bbb] leading-relaxed">
            The Code tab in the builder shows your current environment code with
            annotated sections for each major component: observation space, action space,
            reward function, step logic, and reset logic.
          </p>
        </section>

        <section id="export" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Export (ZIP, GitHub)</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            When your environment is ready, you can export it in two ways:
          </p>

          <h3 className="text-lg font-semibold text-white mt-6 mb-2">ZIP download</h3>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Download a self-contained ZIP with the environment code,{" "}
            <code className="text-white bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm">requirements.txt</code>,
            and a README. You can use this package directly with Stable-Baselines3
            or any other RL framework on your local machine.
          </p>

          <h3 className="text-lg font-semibold text-white mt-8 mb-2">GitHub push</h3>
          <p className="text-[#bbb] leading-relaxed">
            Connect your GitHub account from the builder and push directly to
            a repository. kualia creates proper file structure and a Gymnasium
            registration entry point so your environment is importable as a
            Python package.
          </p>
        </section>

        {/* ============================================================ */}
        {/*  AGENT TRAINING                                              */}
        {/* ============================================================ */}

        <section id="algorithms" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Algorithms</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            kualia supports three proven algorithms from Stable-Baselines3. Each
            is suited for different environment characteristics:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-6">
            {[
              {
                name: "PPO",
                full: "Proximal Policy Optimization",
                desc: "General-purpose on-policy algorithm. Works well across most environments and is the recommended default.",
                best: "Discrete & continuous actions, most use cases",
              },
              {
                name: "SAC",
                full: "Soft Actor-Critic",
                desc: "Off-policy algorithm optimized for continuous action spaces. Sample-efficient and stable.",
                best: "Continuous actions (robotics, control)",
              },
              {
                name: "DQN",
                full: "Deep Q-Network",
                desc: "Value-based off-policy algorithm for discrete action spaces. Simple and effective for smaller problems.",
                best: "Discrete actions (grid worlds, games)",
              },
            ].map((algo) => (
              <div key={algo.name} className="border border-[#1a1a1a] rounded-lg p-4 bg-[#0a0a0a]">
                <h4 className="text-white font-bold font-mono mb-1">{algo.name}</h4>
                <p className="text-xs text-[#555] mb-2">{algo.full}</p>
                <p className="text-sm text-[#bbb] mb-3">{algo.desc}</p>
                <p className="text-xs text-[#888]">
                  <strong className="text-[#aaa]">Best for:</strong> {algo.best}
                </p>
              </div>
            ))}
          </div>

          <div className="border border-[#1a1a1a] rounded-lg p-4 bg-[#0a0a0a] my-6">
            <p className="text-sm text-[#888]">
              <strong className="text-white">Auto-detect:</strong> If you&apos;re unsure which algorithm to use,
              kualia can automatically select the best one based on your environment&apos;s
              action and observation spaces.
            </p>
          </div>
        </section>

        <section id="training-configuration" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Configuration & Hyperparameters</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            kualia provides sensible defaults for all training parameters, but you
            can customize everything for advanced experiments.
          </p>

          <h3 className="text-lg font-semibold text-white mt-6 mb-3">Basic settings</h3>
          <ul className="list-disc list-inside text-[#bbb] space-y-2 mb-6 ml-2">
            <li><strong className="text-white">Algorithm</strong> — PPO, SAC, or DQN (or Auto-detect)</li>
            <li><strong className="text-white">Timesteps</strong> — Total training steps (e.g. 10K for a quick test, 100K–500K for meaningful results)</li>
            <li><strong className="text-white">Learning Rate</strong> — Controls how fast the agent updates its policy. Default is usually good.</li>
          </ul>

          <h3 className="text-lg font-semibold text-white mt-6 mb-3">Advanced settings</h3>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Expand &quot;Advanced Settings&quot; in the training panel to access:
          </p>
          <ul className="list-disc list-inside text-[#bbb] space-y-2 mb-6 ml-2">
            <li><strong className="text-white">Batch Size</strong> — Number of samples per gradient update</li>
            <li><strong className="text-white">Gamma (γ)</strong> — Discount factor. Higher values (0.99) make the agent more far-sighted</li>
            <li><strong className="text-white">GAE Lambda</strong> — Generalized Advantage Estimation parameter (PPO)</li>
            <li><strong className="text-white">Entropy Coefficient</strong> — Encourages exploration. Increase if the agent converges too early</li>
            <li><strong className="text-white">N Steps</strong> — Rollout length per update (PPO). Larger values capture longer-term dependencies</li>
            <li><strong className="text-white">Tau</strong> — Soft update coefficient for target networks (SAC)</li>
            <li><strong className="text-white">Network Architecture</strong> — Configure hidden layer sizes for the policy and value networks</li>
            <li><strong className="text-white">Random Seed</strong> — Set for reproducible experiments</li>
          </ul>

          <div className="border border-[#1a1a1a] rounded-lg p-4 bg-[#0a0a0a] my-6">
            <p className="text-sm text-[#888]">
              <strong className="text-white">Recommended timesteps:</strong> Quick test: 5K–10K steps (1–3 min).
              Meaningful results: 50K–100K steps (5–15 min). Strong performance: 500K–1M steps (20–60 min).
              Complex environments with high-dimensional observations or sparse rewards need more steps.
            </p>
          </div>
        </section>

        <section id="training-modes" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Training Modes</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            After completing a training run, you can continue improving your agent
            using three distinct modes:
          </p>

          <div className="space-y-4 my-6">
            <div className="border border-[#1a1a1a] rounded-lg p-5 bg-[#0a0a0a]">
              <h4 className="text-white font-bold mb-2">Continue (Same Settings)</h4>
              <p className="text-sm text-[#bbb]">
                Resume training from the last checkpoint with the same hyperparameters.
                Useful when the reward curve is still improving and you want more
                steps to reach convergence.
              </p>
            </div>
            <div className="border border-[#1a1a1a] rounded-lg p-5 bg-[#0a0a0a]">
              <h4 className="text-white font-bold mb-2">Fine-Tune (Low Learning Rate)</h4>
              <p className="text-sm text-[#bbb]">
                Continue from the checkpoint but with a reduced learning rate and
                shorter training run. Ideal for making small adjustments to an
                already-trained agent without destabilizing its learned behavior.
              </p>
            </div>
            <div className="border border-[#1a1a1a] rounded-lg p-5 bg-[#0a0a0a]">
              <h4 className="text-white font-bold mb-2">Curriculum (Auto-Increase Difficulty)</h4>
              <p className="text-sm text-[#bbb]">
                The environment difficulty automatically increases during training.
                The agent first masters the easier version and gradually faces harder
                challenges. This is effective for complex environments where learning
                from scratch at full difficulty is too hard.
              </p>
            </div>
          </div>
        </section>

        <section id="monitoring-curves" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Monitoring & Curves</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            While training is running, the dashboard provides real-time feedback:
          </p>
          <ul className="list-disc list-inside text-[#bbb] space-y-2 mb-6 ml-2">
            <li><strong className="text-white">Reward curve</strong> — Live plot showing mean episode reward over training steps</li>
            <li><strong className="text-white">Episode length</strong> — Tracks how long episodes last (decreasing length often means faster problem-solving)</li>
            <li><strong className="text-white">Loss metrics</strong> — Policy loss, value loss, and entropy for diagnosing training health</li>
            <li><strong className="text-white">Progress bar</strong> — Current step, total steps, estimated time remaining</li>
          </ul>
          <p className="text-[#bbb] leading-relaxed mb-4">
            After training completes, you get a full evaluation report with:
          </p>
          <ul className="list-disc list-inside text-[#bbb] space-y-2 mb-4 ml-2">
            <li>Mean and standard deviation of rewards across evaluation episodes</li>
            <li>Best and worst episode performance</li>
            <li>Training hyperparameters used</li>
            <li>Reproducibility info (seed, algorithm version)</li>
          </ul>
          <p className="text-[#bbb] leading-relaxed">
            All experiment data is saved so you can compare runs side-by-side
            in the Experiments table.
          </p>
        </section>

        {/* ============================================================ */}
        {/*  RESEARCH LAB                                                */}
        {/* ============================================================ */}

        <section id="research-overview" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Research Lab — Overview</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            The Research Lab is a structured experiment pipeline for running
            reproducible RL research. It guides you through the full research
            lifecycle: from hypothesis formation to paper generation.
          </p>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Two AI research agents collaborate on your project:
          </p>
          <ul className="list-disc list-inside text-[#bbb] space-y-2 mb-4 ml-2">
            <li><strong className="text-white">Sage</strong> — Formulates hypotheses, conducts literature research, and writes the final paper</li>
            <li><strong className="text-white">Atlas</strong> — Designs and generates environments, runs training experiments, and analyzes results</li>
          </ul>
          <p className="text-[#bbb] leading-relaxed">
            You provide a research topic and brief description. The agents handle
            the rest — designing experiments, training agents, analyzing results,
            and producing a paper with real data and inline training figures.
          </p>
        </section>

        <section id="phases-pipeline" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Phases & Pipeline</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            A research project progresses through the following phases:
          </p>

          <div className="space-y-3 my-6">
            {[
              { phase: "1. Hypothesis", desc: "AI formulates a research question, defines the hypothesis, and outlines the experimental approach based on your topic." },
              { phase: "2. Environment Design", desc: "The Architect Agent generates a custom Gymnasium environment tailored to test the hypothesis." },
              { phase: "3. Experiments", desc: "Agents are trained in the generated environment. Multiple runs with different configurations provide robust data." },
              { phase: "4. Literature & Paper", desc: "The system searches for relevant academic literature, analyzes all experimental results, and writes a complete research paper with inline training figures." },
            ].map((p) => (
              <div key={p.phase} className="flex items-start gap-3 border border-[#1a1a1a] rounded-lg p-4 bg-[#0a0a0a]">
                <span className="text-white font-mono font-bold text-sm whitespace-nowrap">{p.phase}</span>
                <p className="text-sm text-[#bbb]">{p.desc}</p>
              </div>
            ))}
          </div>

          <p className="text-[#bbb] leading-relaxed">
            You can re-run any phase if the results aren&apos;t satisfactory. For example,
            re-run experiments with different hyperparameters, or regenerate the
            environment with additional constraints.
          </p>
        </section>

        <section id="paper-generation" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Paper Generation</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Once your experiments are complete, kualia auto-generates a research
            paper. The generated paper includes:
          </p>
          <ul className="list-disc list-inside text-[#bbb] space-y-2 mb-4 ml-2">
            <li>Abstract summarizing the research and key findings</li>
            <li>Introduction with related work from literature research</li>
            <li>Methodology section describing the environment and algorithms</li>
            <li>Results with inline training curves and evaluation metrics</li>
            <li>Discussion and conclusion sections</li>
            <li>Bibliography from referenced literature</li>
          </ul>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Papers include real training data — reward curves, convergence
            plots, evaluation statistics — directly from your experiments.
            No simulated or hallucinated results.
          </p>
          <p className="text-[#bbb] leading-relaxed">
            You can download the paper as PDF from the Research Lab interface.
            You can also generate a paper directly from any environment in the
            Builder using the &quot;Create Paper&quot; button.
          </p>
        </section>

        {/* Bottom spacer */}
        <div className="h-32" />
      </div>
    </div>
  );
}
