import { Metadata } from "next";
import { BrainCircuit, Target, Lightbulb, ArrowRight } from "lucide-react";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About",
  description:
    "About Kualia.ai — our mission, approach, and vision for the future of robotics and AI research.",
};

export default function AboutPage() {
  return (
    <div className="fade-in mx-auto max-w-4xl px-6 py-16 md:py-24">
      <div className="mb-16">
        <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
          About Kualia.ai
        </h1>
        <p className="text-lg text-[#888] leading-relaxed max-w-2xl">
          We are an independent AI research lab focused on building intelligent
          systems that learn through interaction with the physical world.
        </p>
      </div>

      <div className="line-glow mb-16" />

      {/* Mission */}
      <section className="mb-16">
        <div className="flex items-center gap-3 mb-6">
          <div className="h-9 w-9 rounded-md border border-[#222] flex items-center justify-center text-[#888]">
            <Target className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-white">Mission</h2>
        </div>
        <div className="space-y-4 text-[#888] leading-relaxed max-w-2xl">
          <p>
            Our mission is to advance embodied intelligence through
            reinforcement learning and robotics. We believe that agents which
            can perceive, reason, and act in complex environments develop
            fundamentally deeper understanding than systems trained on static
            datasets alone.
          </p>
          <p>
            We build RL environments that capture the essential challenges of
            real-world robotics. We run autonomous research experiments. We
            publish our findings openly. And we are working toward robots that
            learn general-purpose skills from simulation and transfer them to
            hardware.
          </p>
        </div>
      </section>

      {/* Approach */}
      <section className="mb-16">
        <div className="flex items-center gap-3 mb-6">
          <div className="h-9 w-9 rounded-md border border-[#222] flex items-center justify-center text-[#888]">
            <Lightbulb className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-white">Approach</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <ApproachCard
            number="01"
            title="Environment Design"
            description="We design custom RL environments that capture the key challenges of robotics: contact dynamics, partial observability, multi-objective rewards, and sim-to-real transfer."
          />
          <ApproachCard
            number="02"
            title="Autonomous Research"
            description="Our multi-agent research lab identifies promising ideas, designs experiments, runs simulations, and writes papers with minimal human supervision."
          />
          <ApproachCard
            number="03"
            title="Open Publication"
            description="Every paper, every environment, and every trained policy is published openly. Reproducibility is not optional; it is a requirement."
          />
          <ApproachCard
            number="04"
            title="Sim-to-Real Transfer"
            description="Policies trained in simulation must work on hardware. We develop domain randomization, system identification, and adaptation methods to close the reality gap."
          />
        </div>
      </section>

      <div className="line-glow mb-16" />

      {/* Vision */}
      <section className="mb-16">
        <div className="flex items-center gap-3 mb-6">
          <div className="h-9 w-9 rounded-md border border-[#222] flex items-center justify-center text-[#888]">
            <BrainCircuit className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-white">Vision</h2>
        </div>
        <div className="space-y-4 text-[#888] leading-relaxed max-w-2xl">
          <p>
            We envision a future where intelligent robots are as common as
            smartphones. Robots that learn to cook, clean, build, repair, assist
            in surgery, explore disaster zones, and work alongside humans in
            factories and homes.
          </p>
          <p>
            Getting there requires solving some of the hardest problems in AI:
            sample-efficient learning, robust sim-to-real transfer,
            multi-task generalization, safe exploration, and human-robot
            interaction. We are tackling these problems one environment, one
            paper, and one robot at a time.
          </p>
        </div>
      </section>

      {/* CTA */}
      <div className="border border-[#1a1a1a] rounded-lg p-8 text-center">
        <p className="text-[#888] mb-4">
          Interested in our work? Explore our latest research and environments.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link
            href="/research"
            className="inline-flex items-center gap-2 bg-white text-black px-4 py-2 rounded-md text-sm font-medium hover:bg-[#e5e5e5] transition-colors"
          >
            Research <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <Link
            href="/environments"
            className="inline-flex items-center gap-2 border border-[#333] text-white px-4 py-2 rounded-md text-sm font-medium hover:border-[#555] transition-colors"
          >
            Environments
          </Link>
        </div>
      </div>
    </div>
  );
}

function ApproachCard({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="border border-[#1a1a1a] rounded-lg p-5">
      <span className="text-xs font-mono text-[#555] mb-3 block">{number}</span>
      <h3 className="text-base font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm text-[#888] leading-relaxed">{description}</p>
    </div>
  );
}
