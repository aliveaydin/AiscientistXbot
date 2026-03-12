import Link from "next/link";
import {
  FlaskConical,
  Cpu,
  BookOpen,
  ArrowRight,
  Boxes,
  BrainCircuit,
  Joystick,
  FileText,
} from "lucide-react";
import { getPublicStats, getPublishedPapers, getPublishedBlog } from "@/lib/api";

export default async function Home() {
  let stats = { papers: 0, blog_posts: 0, environments: 0 };
  let latestPapers: any[] = [];
  let latestBlog: any[] = [];

  try {
    [stats, latestPapers, latestBlog] = await Promise.all([
      getPublicStats().catch(() => ({ papers: 0, blog_posts: 0, environments: 0 })),
      getPublishedPapers(3, 0).then((r: any) => r.items || []).catch(() => []),
      getPublishedBlog(3, 0).then((r: any) => r.items || []).catch(() => []),
    ]);
  } catch {
    // graceful fallback
  }

  const latestItems = [
    ...latestPapers.map((p: any) => ({ type: "paper", id: p.id, title: p.title, date: p.published_at || p.created_at, href: `/research/${p.id}` })),
    ...latestBlog.filter((b: any) => b.language === "en").map((b: any) => ({ type: "blog", id: b.id, title: b.title, date: b.published_at || b.created_at, href: `/blog/${b.id}` })),
  ].sort((a, b) => (b.date || "").localeCompare(a.date || "")).slice(0, 4);

  return (
    <div className="fade-in">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(255,255,255,0.03)_0%,_transparent_60%)]" />
        <div className="mx-auto max-w-6xl px-6 pt-24 pb-20 md:pt-36 md:pb-28">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#222] px-3 py-1 mb-6">
              <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
              <span className="text-xs text-[#888] font-mono">
                Robotics &middot; RL &middot; Research
              </span>
            </div>

            <h1 className="text-4xl md:text-6xl font-bold tracking-tight leading-[1.1] text-white mb-6">
              Building intelligent systems
              <br />
              <span className="text-[#666]">that learn to act.</span>
            </h1>

            <p className="text-lg md:text-xl text-[#888] leading-relaxed max-w-xl mb-10">
              We design reinforcement learning environments, conduct autonomous
              AI research, and develop robots that learn from interaction. Every
              component is built to advance embodied intelligence.
            </p>

            <div className="flex flex-wrap gap-4">
              <Link
                href="/research"
                className="inline-flex items-center gap-2 bg-white text-black px-5 py-2.5 rounded-md text-sm font-medium hover:bg-[#e5e5e5] transition-colors"
              >
                View Research
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/environments"
                className="inline-flex items-center gap-2 border border-[#333] text-white px-5 py-2.5 rounded-md text-sm font-medium hover:border-[#555] hover:bg-[#0a0a0a] transition-colors"
              >
                Explore Environments
              </Link>
            </div>
          </div>
        </div>
      </section>

      <div className="line-glow" />

      {/* What We Do */}
      <section className="mx-auto max-w-6xl px-6 py-20 md:py-28">
        <div className="mb-12">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-3">
            What we build
          </h2>
          <p className="text-[#888] max-w-lg">
            Three pillars of our work, each feeding into the others.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <PillarCard
            icon={<Joystick className="w-5 h-5" />}
            title="RL Environments"
            description="Custom reinforcement learning environments for robotics, locomotion, manipulation, and navigation. Each one is designed to push the boundaries of agent capabilities."
            href="/environments"
          />
          <PillarCard
            icon={<FlaskConical className="w-5 h-5" />}
            title="Research Lab"
            description="Multi-agent AI research system that discovers ideas, runs experiments, and produces publication-ready papers. Autonomous science at scale."
            href="/research"
          />
          <PillarCard
            icon={<Cpu className="w-5 h-5" />}
            title="Robotics"
            description="Embodied agents trained in simulation, transferred to physical hardware. From locomotion to fine manipulation, bridging the sim-to-real gap."
            href="/about"
            badge="Coming Soon"
          />
        </div>
      </section>

      <div className="line-glow" />

      {/* Numbers */}
      <section className="mx-auto max-w-6xl px-6 py-20 md:py-28">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <StatBlock label="Research Papers" value={stats.papers > 0 ? String(stats.papers) : "—"} />
          <StatBlock label="RL Environments" value={stats.environments > 0 ? String(stats.environments) : "—"} />
          <StatBlock label="Blog Articles" value={stats.blog_posts > 0 ? String(stats.blog_posts) : "—"} />
          <StatBlock label="Open Source" value="100%" />
        </div>
      </section>

      <div className="line-glow" />

      {/* Philosophy */}
      <section className="mx-auto max-w-6xl px-6 py-20 md:py-28">
        <div className="max-w-2xl mx-auto text-center">
          <BrainCircuit className="w-8 h-8 text-[#555] mx-auto mb-6" />
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
            Intelligence through interaction
          </h2>
          <p className="text-[#888] leading-relaxed mb-4">
            We believe the path to general intelligence runs through embodiment.
            Agents that can perceive, decide, and act in complex environments
            develop richer representations than those trained on static data
            alone.
          </p>
          <p className="text-[#666] leading-relaxed">
            Every environment we build, every paper we publish, and every robot
            we train moves us closer to systems that genuinely understand the
            world they inhabit.
          </p>
        </div>
      </section>

      <div className="line-glow" />

      {/* Latest */}
      <section className="mx-auto max-w-6xl px-6 py-20 md:py-28">
        <div className="flex items-center justify-between mb-10">
          <h2 className="text-2xl md:text-3xl font-bold text-white">Latest</h2>
          <Link
            href="/blog"
            className="text-sm text-[#888] hover:text-white transition-colors flex items-center gap-1"
          >
            View all <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {latestItems.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {latestItems.map((item) => (
              <Link
                key={`${item.type}-${item.id}`}
                href={item.href}
                className="group border border-[#1a1a1a] rounded-lg p-5 hover:border-[#333] hover:bg-[#0a0a0a] transition-all"
              >
                <div className="flex items-start gap-3">
                  <div className="h-8 w-8 rounded-md border border-[#222] flex items-center justify-center text-[#666] group-hover:text-white group-hover:border-[#444] transition-colors flex-shrink-0 mt-0.5">
                    {item.type === "paper" ? <FileText className="w-4 h-4" /> : <BookOpen className="w-4 h-4" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#555]">
                      {item.type === "paper" ? "Research" : "Blog"}
                    </span>
                    <h3 className="text-sm font-medium text-white mt-0.5 line-clamp-2 group-hover:text-[#e5e5e5]">
                      {item.title}
                    </h3>
                    {item.date && (
                      <time className="text-xs text-[#555] mt-1 block">
                        {new Date(item.date).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}
                      </time>
                    )}
                  </div>
                  <ArrowRight className="w-4 h-4 text-[#333] group-hover:text-[#888] transition-colors flex-shrink-0 mt-1" />
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="border border-[#1a1a1a] rounded-lg p-8 text-center">
            <Boxes className="w-8 h-8 text-[#333] mx-auto mb-3" />
            <p className="text-[#666] text-sm">
              Content will appear here as research and articles are published.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}

function PillarCard({
  icon,
  title,
  description,
  href,
  badge,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  href: string;
  badge?: string;
}) {
  return (
    <Link
      href={href}
      className="group border border-[#1a1a1a] rounded-lg p-6 hover:border-[#333] hover:bg-[#0a0a0a] transition-all"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="h-9 w-9 rounded-md border border-[#222] flex items-center justify-center text-[#888] group-hover:text-white group-hover:border-[#444] transition-colors">
          {icon}
        </div>
        {badge && (
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#555] border border-[#222] rounded px-1.5 py-0.5">
            {badge}
          </span>
        )}
      </div>
      <h3 className="text-base font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm text-[#888] leading-relaxed">{description}</p>
    </Link>
  );
}

function StatBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center md:text-left">
      <div className="text-3xl md:text-4xl font-bold font-mono text-white mb-1">
        {value}
      </div>
      <div className="text-xs text-[#666] uppercase tracking-wider">
        {label}
      </div>
    </div>
  );
}
