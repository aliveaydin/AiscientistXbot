"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  BookOpen,
  Rocket,
  Key,
  Layers,
  Sparkles,
  MessageSquare,
  GitBranch,
  Download,
  Brain,
  Settings2,
  BarChart3,
  Play,
  FlaskConical,
  FileText,
  Code2,
  Terminal,
  Package,
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
      { id: "authentication", label: "Authentication" },
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
      { id: "training-configuration", label: "Configuration" },
      { id: "monitoring-curves", label: "Monitoring & Curves" },
      { id: "continue-training", label: "Continue Training" },
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
  {
    id: "api-reference",
    label: "API Reference",
    icon: <Code2 size={16} />,
    children: [
      { id: "api-catalog", label: "Catalog" },
      { id: "api-generation", label: "Generation" },
      { id: "api-builder", label: "Builder" },
      { id: "api-training", label: "Training" },
      { id: "api-research", label: "Research" },
    ],
  },
  {
    id: "python-sdk",
    label: "Python SDK",
    icon: <Terminal size={16} />,
    children: [
      { id: "sdk-installation", label: "Installation" },
      { id: "sdk-usage", label: "Usage Examples" },
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
        <span className="text-xs text-[#555] font-mono">{language ?? "shell"}</span>
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
/*  ParamTable                                                         */
/* ------------------------------------------------------------------ */

function ParamTable({ params }: { params: { name: string; type: string; required: boolean; desc: string }[] }) {
  return (
    <div className="my-4 overflow-x-auto border border-[#1a1a1a] rounded-lg">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[#0a0a0a] text-left text-[#888]">
            <th className="px-4 py-2 font-medium">Parameter</th>
            <th className="px-4 py-2 font-medium">Type</th>
            <th className="px-4 py-2 font-medium">Required</th>
            <th className="px-4 py-2 font-medium">Description</th>
          </tr>
        </thead>
        <tbody className="text-[#bbb]">
          {params.map((p) => (
            <tr key={p.name} className="border-t border-[#1a1a1a]">
              <td className="px-4 py-2 font-mono text-white">{p.name}</td>
              <td className="px-4 py-2 font-mono text-blue-400">{p.type}</td>
              <td className="px-4 py-2">{p.required ? <span className="text-orange-400">Yes</span> : "No"}</td>
              <td className="px-4 py-2">{p.desc}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Endpoint                                                           */
/* ------------------------------------------------------------------ */

function Endpoint({ method, path, desc }: { method: string; path: string; desc: string }) {
  const color =
    method === "GET"
      ? "bg-blue-950 text-blue-400"
      : method === "POST"
        ? "bg-green-950 text-green-400"
        : method === "DELETE"
          ? "bg-red-950 text-red-400"
          : "bg-yellow-950 text-yellow-400";

  return (
    <div className="border border-[#1a1a1a] rounded-lg p-4 my-3">
      <div className="flex items-center gap-3 mb-1">
        <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${color}`}>{method}</span>
        <code className="text-sm font-mono text-[#ccc]">{path}</code>
      </div>
      <p className="text-sm text-[#888]">{desc}</p>
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
              Real-time monitoring · Version control · Research pipeline · Python
              SDK · REST API
            </p>
          </div>
        </section>

        <section id="quick-start" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Quick Start</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Get from zero to a trained agent in under five minutes.
          </p>

          <h3 className="text-lg font-semibold text-white mt-8 mb-3">1. Install the Python SDK</h3>
          <CodeBlock language="shell">pip install kualia</CodeBlock>

          <h3 className="text-lg font-semibold text-white mt-8 mb-3">2. Generate an environment</h3>
          <CodeBlock language="python">{`import kualia

# Authenticate (or set KUALIA_API_KEY env var)
kualia.configure(api_key="sk-your-key")

# Describe what you want
result = kualia.generate("Cart-pole with gusty wind and friction")
print(result)
# => { id: 42, slug: "cartpole-wind-friction", status: "ready" }`}</CodeBlock>

          <h3 className="text-lg font-semibold text-white mt-8 mb-3">3. Use it locally</h3>
          <CodeBlock language="python">{`env = kualia.make("cartpole-wind-friction")
obs, info = env.reset(seed=42)

for _ in range(1000):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()

env.close()`}</CodeBlock>

          <h3 className="text-lg font-semibold text-white mt-8 mb-3">4. Train an agent</h3>
          <CodeBlock language="python">{`run = kualia.train(
    env_id=42,
    algorithm="PPO",
    total_timesteps=100_000,
)
print(run.status)  # "running"

# Poll or use the dashboard to watch the curve
run.wait()
run.download_model("model.zip")`}</CodeBlock>
        </section>

        <section id="authentication" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Authentication</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            All API requests require an API key passed via the{" "}
            <code className="text-white bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm">X-API-Key</code> header.
            You can create and manage keys from the{" "}
            <span className="text-white">Dashboard → Settings</span> page.
          </p>

          <CodeBlock language="shell">{`curl -H "X-API-Key: sk-your-key" \\
  https://kualia.ai/api/rlforge/catalog`}</CodeBlock>

          <p className="text-[#bbb] leading-relaxed mb-4">
            For the Python SDK, pass the key directly or use an environment variable:
          </p>
          <CodeBlock language="python">{`import kualia

# Option A: explicit
kualia.configure(api_key="sk-your-key")

# Option B: environment variable
# export KUALIA_API_KEY=sk-your-key
kualia.configure()  # picks up from env automatically`}</CodeBlock>

          <ParamTable
            params={[
              { name: "X-API-Key", type: "string", required: true, desc: "Your API key from the dashboard settings page." },
            ]}
          />

          <div className="border border-[#1a1a1a] rounded-lg p-4 bg-[#0a0a0a] my-6">
            <p className="text-sm text-[#888]">
              <strong className="text-orange-400">Security:</strong> Never commit your API key to version
              control. Use environment variables or a secrets manager in production.
            </p>
          </div>
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
          <p className="text-[#bbb] leading-relaxed mb-2">
            Describe your environment in plain English. kualia&apos;s AI generates the
            full Gymnasium code including observation space, action space, reward
            function, and dynamics.
          </p>
          <CodeBlock language="shell">{`curl -X POST https://kualia.ai/api/rlforge/generate \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: sk-your-key" \\
  -d '{
    "description": "A 2D drone that must land on a moving platform",
    "domain": "robotics",
    "difficulty": "medium"
  }'`}</CodeBlock>

          <h3 className="text-lg font-semibold text-white mt-8 mb-2">From a research paper</h3>
          <p className="text-[#bbb] leading-relaxed mb-2">
            Upload a PDF paper and kualia extracts the environment specification,
            reward structure, and constraints to generate a matching implementation.
          </p>
          <CodeBlock language="shell">{`curl -X POST https://kualia.ai/api/rlforge/generate-from-paper \\
  -H "X-API-Key: sk-your-key" \\
  -F "file=@paper.pdf"`}</CodeBlock>

          <h3 className="text-lg font-semibold text-white mt-8 mb-2">Fork an existing environment</h3>
          <p className="text-[#bbb] leading-relaxed mb-2">
            Start from any published environment in the catalog and fork it with
            your own modifications.
          </p>
          <CodeBlock language="shell">{`curl -X POST https://kualia.ai/api/rlforge/fork/42 \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: sk-your-key" \\
  -d '{ "modifications": "Add obstacles and increase gravity" }'`}</CodeBlock>
        </section>

        <section id="chat-iteration" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Chat Iteration</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            After initial generation, the builder enters chat mode. You can ask
            for any modification — changing the reward function, adjusting the
            observation space, adding visualization, tweaking dynamics — and the AI
            updates the environment code accordingly.
          </p>
          <CodeBlock language="shell">{`curl -X POST https://kualia.ai/api/rlforge/builder/42/chat \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: sk-your-key" \\
  -d '{ "message": "Make the reward sparse: +1 only when the agent reaches the goal" }'`}</CodeBlock>

          <p className="text-[#bbb] leading-relaxed mb-4">
            Each message creates a new version of the environment. You can
            retrieve the full conversation history to understand how the
            environment evolved:
          </p>
          <CodeBlock language="shell">{`curl https://kualia.ai/api/rlforge/builder/42/history \\
  -H "X-API-Key: sk-your-key"`}</CodeBlock>

          <p className="text-[#bbb] leading-relaxed">
            The response includes each message, the code diff, and the version
            number, so you always have full traceability.
          </p>
        </section>

        <section id="version-control" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Version Control</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Every chat iteration creates a new version of your environment. kualia
            stores the full version tree so you can roll back to any previous
            state at any time.
          </p>
          <CodeBlock language="shell">{`# Roll back to version 3
curl -X POST https://kualia.ai/api/rlforge/builder/42/rollback \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: sk-your-key" \\
  -d '{ "version": 3 }'`}</CodeBlock>

          <p className="text-[#bbb] leading-relaxed">
            Rollback does not delete later versions — it creates a new version
            based on the target, so you can always go forward again. Think of it
            like <code className="text-white bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm">git revert</code> rather
            than a hard reset.
          </p>
        </section>

        <section id="export" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Export (ZIP, GitHub)</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            When your environment is ready, you can export it in two ways:
          </p>

          <h3 className="text-lg font-semibold text-white mt-6 mb-2">ZIP download</h3>
          <p className="text-[#bbb] leading-relaxed mb-2">
            Download a self-contained ZIP with the environment code,{" "}
            <code className="text-white bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm">requirements.txt</code>,
            and a README:
          </p>
          <CodeBlock language="shell">{`curl -o env.zip https://kualia.ai/api/rlforge/builder/42/export-zip \\
  -H "X-API-Key: sk-your-key"`}</CodeBlock>

          <h3 className="text-lg font-semibold text-white mt-8 mb-2">GitHub push</h3>
          <p className="text-[#bbb] leading-relaxed">
            From the dashboard, connect your GitHub account and push directly to
            a repository. kualia creates the repo (or pushes to an existing one)
            with proper file structure, CI checks, and a Gymnasium registration
            entry point.
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
        </section>

        <section id="training-configuration" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Training Configuration</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Start a training run by specifying the environment ID, algorithm, and
            hyperparameters. kualia provides sensible defaults for all optional
            fields.
          </p>

          <CodeBlock language="shell">{`curl -X POST https://kualia.ai/api/rlforge/train/42 \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: sk-your-key" \\
  -d '{
    "algorithm": "PPO",
    "total_timesteps": 100000,
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 64,
    "gamma": 0.99
  }'`}</CodeBlock>

          <ParamTable
            params={[
              { name: "algorithm", type: "string", required: false, desc: 'One of "PPO", "SAC", "DQN". Defaults to "PPO".' },
              { name: "total_timesteps", type: "integer", required: false, desc: "Total training steps. Default: 50,000." },
              { name: "learning_rate", type: "float", required: false, desc: "Learning rate. Default: 3e-4." },
              { name: "n_steps", type: "integer", required: false, desc: "Steps per rollout (PPO only). Default: 2048." },
              { name: "batch_size", type: "integer", required: false, desc: "Minibatch size. Default: 64." },
              { name: "gamma", type: "float", required: false, desc: "Discount factor. Default: 0.99." },
              { name: "seed", type: "integer", required: false, desc: "Random seed for reproducibility." },
            ]}
          />
        </section>

        <section id="monitoring-curves" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Monitoring & Curves</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            While training is running, you can poll the status endpoint to get
            real-time metrics. The dashboard also provides a live reward curve
            visualization.
          </p>
          <CodeBlock language="shell">{`# Check training status
curl https://kualia.ai/api/rlforge/train/42/status \\
  -H "X-API-Key: sk-your-key"

# Response
{
  "status": "running",
  "progress": 0.65,
  "current_timestep": 65000,
  "total_timesteps": 100000,
  "mean_reward": 187.3,
  "elapsed_seconds": 42
}`}</CodeBlock>

          <CodeBlock language="shell">{`# Get the full reward curve
curl https://kualia.ai/api/rlforge/train/42/curve \\
  -H "X-API-Key: sk-your-key"

# Response
{
  "timesteps": [1000, 2000, 3000, ...],
  "rewards": [12.5, 34.2, 67.8, ...],
  "episode_lengths": [120, 145, 98, ...]
}`}</CodeBlock>

          <p className="text-[#bbb] leading-relaxed">
            The curve data is suitable for plotting with matplotlib, plotly, or
            any charting library. The dashboard renders it in real-time using a
            streaming connection.
          </p>
        </section>

        <section id="continue-training" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Continue Training</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            If a model needs more training steps, you can resume from the last
            checkpoint without starting over. Pass the{" "}
            <code className="text-white bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm">continue_from</code>{" "}
            parameter with the ID of a completed training run:
          </p>
          <CodeBlock language="shell">{`curl -X POST https://kualia.ai/api/rlforge/train/42 \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: sk-your-key" \\
  -d '{
    "algorithm": "PPO",
    "total_timesteps": 50000,
    "continue_from": "run_abc123"
  }'`}</CodeBlock>
          <p className="text-[#bbb] leading-relaxed">
            The training run inherits all hyperparameters from the previous run
            unless you explicitly override them. This is useful for fine-tuning
            or extending convergence.
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
            Each research project contains a conversational thread where you
            describe your research goals. kualia&apos;s AI assistant helps you design
            experiments, select baselines, and analyze results.
          </p>
          <p className="text-[#bbb] leading-relaxed">
            You can also upload reference papers to ground your research in
            existing literature. kualia extracts key methods, results, and
            experimental setups to inform your experiment design.
          </p>
        </section>

        <section id="phases-pipeline" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Phases & Pipeline</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            A research project progresses through the following phases:
          </p>

          <div className="space-y-3 my-6">
            {[
              { phase: "1. Hypothesis", desc: "Define your research question and expected outcomes." },
              { phase: "2. Experiment Design", desc: "Select environments, algorithms, baselines, and metrics." },
              { phase: "3. Execution", desc: "Run all training experiments with tracking and versioning." },
              { phase: "4. Analysis", desc: "Compare results, generate plots, and run statistical tests." },
              { phase: "5. Paper Generation", desc: "Auto-generate a LaTeX paper from your results and methodology." },
            ].map((p) => (
              <div key={p.phase} className="flex items-start gap-3 border border-[#1a1a1a] rounded-lg p-4 bg-[#0a0a0a]">
                <span className="text-white font-mono font-bold text-sm whitespace-nowrap">{p.phase}</span>
                <p className="text-sm text-[#bbb]">{p.desc}</p>
              </div>
            ))}
          </div>

          <p className="text-[#bbb] leading-relaxed">
            You can move between phases freely — for example, going back to
            experiment design after seeing initial results.
          </p>
        </section>

        <section id="paper-generation" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Paper Generation</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Once your experiments are complete, kualia can auto-generate a research
            paper in LaTeX format. The generated paper includes:
          </p>
          <ul className="list-disc list-inside text-[#bbb] space-y-2 mb-4 ml-2">
            <li>Abstract summarizing the research and key findings</li>
            <li>Introduction with related work from uploaded references</li>
            <li>Methodology section describing environments and algorithms</li>
            <li>Results with auto-generated tables and reward curve figures</li>
            <li>Discussion and conclusion sections</li>
            <li>Bibliography from uploaded reference papers</li>
          </ul>
          <p className="text-[#bbb] leading-relaxed">
            The generated paper is a starting point — you can download the LaTeX
            source and edit it further, or continue iterating through the chat
            interface.
          </p>
        </section>

        {/* ============================================================ */}
        {/*  API REFERENCE                                               */}
        {/* ============================================================ */}

        <section id="api-catalog" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">API Reference — Catalog</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Browse and search published environments in the kualia catalog.
          </p>

          <Endpoint method="GET" path="/api/rlforge/catalog" desc="List published environments. Supports filtering by domain, difficulty, and text search." />
          <ParamTable
            params={[
              { name: "domain", type: "string", required: false, desc: 'Filter by domain (e.g. "robotics", "finance", "games").' },
              { name: "difficulty", type: "string", required: false, desc: 'Filter by difficulty: "easy", "medium", "hard".' },
              { name: "search", type: "string", required: false, desc: "Full-text search across name and description." },
              { name: "page", type: "integer", required: false, desc: "Page number for pagination. Default: 1." },
              { name: "limit", type: "integer", required: false, desc: "Results per page. Default: 20, max: 100." },
            ]}
          />
          <CodeBlock language="json">{`// GET /api/rlforge/catalog?domain=robotics&limit=2
{
  "environments": [
    {
      "id": 42,
      "slug": "drone-landing-v1",
      "name": "Drone Landing",
      "description": "2D drone that must land on a moving platform",
      "domain": "robotics",
      "difficulty": "medium",
      "observation_space": "Box(8,)",
      "action_space": "Box(2,)",
      "created_at": "2025-06-15T10:30:00Z"
    }
  ],
  "total": 127,
  "page": 1
}`}</CodeBlock>

          <Endpoint method="GET" path="/api/rlforge/catalog/{slug}" desc="Get full details for a specific environment by its slug." />
          <Endpoint method="GET" path="/api/rlforge/templates" desc="List template environments that serve as starting points for generation." />
        </section>

        <section id="api-generation" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">API Reference — Generation</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Generate new environments from natural language, papers, or by forking existing ones.
          </p>

          <Endpoint method="POST" path="/api/rlforge/generate" desc="Generate a new Gymnasium environment from a natural-language description." />
          <ParamTable
            params={[
              { name: "description", type: "string", required: true, desc: "Natural-language description of the desired environment." },
              { name: "domain", type: "string", required: false, desc: 'Category hint: "robotics", "finance", "games", etc.' },
              { name: "difficulty", type: "string", required: false, desc: 'Complexity hint: "easy", "medium", "hard".' },
            ]}
          />
          <CodeBlock language="json">{`// POST /api/rlforge/generate
// Request
{
  "description": "Multi-stock trading with transaction costs and portfolio constraints",
  "domain": "finance",
  "difficulty": "hard"
}

// Response
{
  "id": 57,
  "slug": "multi-stock-trading-v1",
  "name": "Multi-Stock Trading",
  "status": "ready",
  "code": "import gymnasium as gym\\nimport numpy as np\\n...",
  "observation_space": "Box(30,)",
  "action_space": "Box(5,)"
}`}</CodeBlock>

          <Endpoint method="POST" path="/api/rlforge/generate-from-paper" desc="Generate an environment from an uploaded PDF research paper. Multipart form data." />
          <Endpoint method="POST" path="/api/rlforge/fork/{env_id}" desc="Fork an existing environment and apply modifications." />
        </section>

        <section id="api-builder" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">API Reference — Builder</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Interact with the conversational environment builder.
          </p>

          <Endpoint method="POST" path="/api/rlforge/builder/{id}/chat" desc="Send an iteration message to modify the environment." />
          <ParamTable
            params={[
              { name: "message", type: "string", required: true, desc: "The modification request in natural language." },
            ]}
          />
          <CodeBlock language="json">{`// POST /api/rlforge/builder/42/chat
// Request
{ "message": "Change the reward to be distance-based: -1 * distance_to_goal" }

// Response
{
  "version": 5,
  "code": "import gymnasium as gym\\n...",
  "diff": "@@ -45,3 +45,3 @@\\n-  reward = 1.0 if done else 0.0\\n+  reward = -1.0 * distance_to_goal",
  "message": "Updated the reward function to be distance-based..."
}`}</CodeBlock>

          <Endpoint method="GET" path="/api/rlforge/builder/{id}/history" desc="Get the full conversation history and version timeline." />
          <Endpoint method="POST" path="/api/rlforge/builder/{id}/rollback" desc="Roll back to a specific version." />
          <Endpoint method="POST" path="/api/rlforge/builder/{id}/export-zip" desc="Download the current environment as a ZIP archive." />
        </section>

        <section id="api-training" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">API Reference — Training</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Launch and monitor agent training runs using Stable-Baselines3.
          </p>

          <Endpoint method="POST" path="/api/rlforge/train/{env_id}" desc="Start a training run. Returns a run ID for tracking." />
          <ParamTable
            params={[
              { name: "algorithm", type: "string", required: false, desc: '"PPO", "SAC", or "DQN". Default: "PPO".' },
              { name: "total_timesteps", type: "integer", required: false, desc: "Total training steps. Default: 50000." },
              { name: "learning_rate", type: "float", required: false, desc: "Learning rate. Default: 3e-4." },
              { name: "seed", type: "integer", required: false, desc: "Random seed for reproducibility." },
              { name: "continue_from", type: "string", required: false, desc: "Run ID to continue training from." },
            ]}
          />
          <CodeBlock language="json">{`// POST /api/rlforge/train/42
// Request
{
  "algorithm": "SAC",
  "total_timesteps": 200000,
  "seed": 42
}

// Response
{
  "run_id": "run_xyz789",
  "status": "queued",
  "env_id": 42,
  "algorithm": "SAC",
  "total_timesteps": 200000
}`}</CodeBlock>

          <Endpoint method="GET" path="/api/rlforge/train/{env_id}/status" desc="Get the current status of the latest training run." />
          <Endpoint method="GET" path="/api/rlforge/train/{env_id}/curve" desc="Get the reward curve data (timesteps, rewards, episode lengths)." />
          <Endpoint method="GET" path="/api/rlforge/train/{env_id}/model" desc="Download the trained model as a .zip file." />
        </section>

        <section id="api-research" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">API Reference — Research</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            Create and manage research projects with the experiment pipeline.
          </p>

          <Endpoint method="POST" path="/api/rlforge/research/projects" desc="Create a new research project." />
          <ParamTable
            params={[
              { name: "title", type: "string", required: true, desc: "Title of the research project." },
              { name: "description", type: "string", required: false, desc: "Brief description of the research goals." },
            ]}
          />
          <CodeBlock language="json">{`// POST /api/rlforge/research/projects
// Request
{
  "title": "Reward Shaping in Sparse Environments",
  "description": "Comparing dense vs sparse reward signals across navigation tasks"
}

// Response
{
  "id": "proj_abc123",
  "title": "Reward Shaping in Sparse Environments",
  "phase": "hypothesis",
  "created_at": "2025-07-20T14:00:00Z"
}`}</CodeBlock>

          <Endpoint method="GET" path="/api/rlforge/research/projects" desc="List all research projects for the authenticated user." />
          <Endpoint method="GET" path="/api/rlforge/research/projects/{id}" desc="Get full project details including conversation messages." />
          <Endpoint method="POST" path="/api/rlforge/research/projects/{id}/upload-paper" desc="Upload a reference paper (PDF) to inform the experiment design." />
        </section>

        {/* ============================================================ */}
        {/*  PYTHON SDK                                                  */}
        {/* ============================================================ */}

        <section id="sdk-installation" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Python SDK — Installation</h2>
          <p className="text-[#bbb] leading-relaxed mb-4">
            The kualia Python SDK wraps the REST API into a clean, Pythonic
            interface. It also provides a Gymnasium-compatible{" "}
            <code className="text-white bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm">make()</code> function
            for using environments directly in your training scripts.
          </p>

          <h3 className="text-lg font-semibold text-white mt-6 mb-3">Requirements</h3>
          <ul className="list-disc list-inside text-[#bbb] space-y-1 mb-4 ml-2">
            <li>Python 3.8+</li>
            <li>pip or conda</li>
          </ul>

          <h3 className="text-lg font-semibold text-white mt-6 mb-3">Install via pip</h3>
          <CodeBlock language="shell">pip install kualia</CodeBlock>

          <h3 className="text-lg font-semibold text-white mt-6 mb-3">Install from source</h3>
          <CodeBlock language="shell">{`git clone https://github.com/kualia/kualia-python.git
cd kualia-python
pip install -e .`}</CodeBlock>

          <h3 className="text-lg font-semibold text-white mt-6 mb-3">Configuration</h3>
          <CodeBlock language="python">{`import kualia

# Set your API key (or use KUALIA_API_KEY environment variable)
kualia.configure(
    api_key="sk-your-key",
    api_url="https://kualia.ai",  # default, can be overridden for self-hosted
)`}</CodeBlock>
        </section>

        <section id="sdk-usage" className="scroll-mt-24 mb-20">
          <h2 className="text-2xl font-bold text-white mb-3">Python SDK — Usage Examples</h2>

          <h3 className="text-lg font-semibold text-white mt-6 mb-3">Using catalog environments</h3>
          <CodeBlock language="python">{`import kualia

kualia.configure(api_key="sk-your-key")

# Browse the catalog
envs = kualia.catalog.list(domain="robotics", limit=5)
for env in envs:
    print(f"{env.slug}: {env.name}")

# Create an environment instance
env = kualia.make("drone-landing-v1")
obs, info = env.reset(seed=42)

for step in range(1000):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()

env.close()`}</CodeBlock>

          <h3 className="text-lg font-semibold text-white mt-8 mb-3">Generating a custom environment</h3>
          <CodeBlock language="python">{`result = kualia.generate(
    description="A warehouse robot that picks and places items on shelves",
    domain="robotics",
    difficulty="hard",
)
print(f"Created: {result.slug} (id={result.id})")

# Iterate on the environment
kualia.builder.chat(result.id, "Add a battery mechanic: the robot must recharge at a station")
kualia.builder.chat(result.id, "Make the observation include the battery level")`}</CodeBlock>

          <h3 className="text-lg font-semibold text-white mt-8 mb-3">Training with the SDK</h3>
          <CodeBlock language="python">{`run = kualia.train(
    env_id=result.id,
    algorithm="PPO",
    total_timesteps=200_000,
    learning_rate=3e-4,
)

# Wait for training to complete (polls automatically)
run.wait(poll_interval=5)

print(f"Final mean reward: {run.mean_reward}")
print(f"Training time: {run.elapsed_seconds}s")

# Download the trained model
run.download_model("trained_agent.zip")

# Get reward curve for plotting
curve = run.get_curve()
# curve.timesteps, curve.rewards, curve.episode_lengths`}</CodeBlock>

          <h3 className="text-lg font-semibold text-white mt-8 mb-3">Full pipeline example</h3>
          <CodeBlock language="python">{`import kualia
import matplotlib.pyplot as plt

kualia.configure(api_key="sk-your-key")

# 1. Generate environment
env_result = kualia.generate("Inverted pendulum with variable mass")

# 2. Refine it
kualia.builder.chat(env_result.id, "Add Gaussian noise to observations")

# 3. Train multiple algorithms
runs = {}
for algo in ["PPO", "SAC"]:
    runs[algo] = kualia.train(
        env_id=env_result.id,
        algorithm=algo,
        total_timesteps=100_000,
        seed=42,
    )

# 4. Wait and compare
for algo, run in runs.items():
    run.wait()
    curve = run.get_curve()
    plt.plot(curve.timesteps, curve.rewards, label=algo)

plt.xlabel("Timesteps")
plt.ylabel("Mean Reward")
plt.legend()
plt.title("Algorithm Comparison")
plt.savefig("comparison.png")
plt.show()`}</CodeBlock>
        </section>

        {/* Bottom spacer */}
        <div className="h-32" />
      </div>
    </div>
  );
}
