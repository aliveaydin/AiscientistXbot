"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FlaskConical, Plus, Loader2, X, Sparkles, Trash2, ChevronDown, ChevronRight } from "lucide-react";
import {
  getMyResearch,
  createResearchProject,
  deleteLabProject,
  type EnvVariant,
  type ExperimentConfig,
} from "@/lib/api";

export default function DashboardResearchPage() {
  const { getToken } = useAuth();
  const router = useRouter();
  const [projects, setProjects] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const perPage = 10;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) return;
      const data = await getMyResearch(token, perPage, page * perPage);
      setProjects(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [getToken, page]);

  useEffect(() => { load(); }, [load]);

  const totalPages = Math.ceil(total / perPage);

  const phaseLabels: Record<string, string> = {
    hypothesis: "Hypothesis",
    research: "Research",
    design: "Design",
    experiment: "Experiment",
    analyze: "Analyze",
    write: "Research & Write",
    review: "Review",
    brainstorm: "Brainstorm",
    completed: "Completed",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Research Projects</h1>
          <p className="text-sm text-[#888] mt-1">{total} project{total !== 1 ? "s" : ""} total</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-white text-black px-4 py-2 rounded-md text-sm font-medium hover:bg-[#e0e0e0] transition-colors"
        >
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      {showCreate && (
        <CreateProjectInline
          onClose={() => setShowCreate(false)}
          onCreated={(id) => { router.push(`/research/${id}`); }}
        />
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-6 h-6 text-[#555] animate-spin" />
        </div>
      ) : projects.length === 0 && !showCreate ? (
        <div className="border border-dashed border-[#1a1a1a] rounded-lg p-12 text-center">
          <FlaskConical className="w-10 h-10 text-[#333] mx-auto mb-4" />
          <p className="text-[#888] mb-2">No research projects yet.</p>
          <p className="text-sm text-[#666] mb-6">
            Start an AI-powered research project with the multi-agent research lab.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-2 bg-white text-black px-5 py-2.5 rounded-md text-sm font-medium hover:bg-[#e0e0e0] transition-colors"
          >
            <Plus className="w-4 h-4" /> New Research Project
          </button>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {projects.map((project: any) => (
              <div key={project.id} className="border border-[#1a1a1a] rounded-lg p-5 hover:border-[#333] hover:bg-[#0a0a0a] transition-all group relative">
                <Link href={`/research/${project.id}`} className="block">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-sm font-semibold text-white group-hover:underline pr-8">{project.title}</h3>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={project.status} />
                      <span className="text-[10px] text-[#555] font-mono">{phaseLabels[project.current_phase] || project.current_phase}</span>
                    </div>
                  </div>
                  {project.description && (
                    <p className="text-xs text-[#888] line-clamp-2">{project.description}</p>
                  )}
                  {project.created_at && (
                    <p className="text-[10px] text-[#555] mt-2">{new Date(project.created_at).toLocaleDateString()}</p>
                  )}
                </Link>
                <button
                  onClick={async (e) => {
                    e.stopPropagation();
                    if (!confirm("Delete this research project and all its data?")) return;
                    try {
                      await deleteLabProject(project.id);
                      load();
                    } catch (err) { console.error(err); }
                  }}
                  className="absolute top-4 right-4 text-[#333] hover:text-red-500 transition-colors p-1"
                  title="Delete project"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className="text-xs text-[#888] hover:text-white disabled:opacity-30 px-3 py-1 border border-[#1a1a1a] rounded">Previous</button>
              <span className="text-xs text-[#666]">{page + 1} / {totalPages}</span>
              <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1} className="text-xs text-[#888] hover:text-white disabled:opacity-30 px-3 py-1 border border-[#1a1a1a] rounded">Next</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

const SUPPORTED_ALGORITHMS = ["PPO", "SAC", "DQN", "A2C", "TD3", "QRDQN"] as const;

type PresetKey = "auto" | "quick" | "standard" | "rigorous" | "custom";

const PRESETS: Record<Exclude<PresetKey, "auto" | "custom">, ExperimentConfig> = {
  quick: {
    env_variants: [{ label: "Canonical", role: "treatment", modifier: "" }],
    algorithms: ["PPO"],
    n_seeds: 1,
    timesteps: 20000,
    n_eval_episodes: 5,
  },
  standard: {
    env_variants: [
      { label: "With hypothesis applied", role: "treatment", modifier: "" },
      { label: "Without hypothesis (baseline)", role: "baseline", modifier: "Same env, but remove the hypothesis-specific mechanism." },
    ],
    algorithms: ["PPO", "SAC"],
    n_seeds: 1,
    timesteps: 50000,
    n_eval_episodes: 10,
  },
  rigorous: {
    env_variants: [
      { label: "With hypothesis applied", role: "treatment", modifier: "" },
      { label: "Without hypothesis (baseline)", role: "baseline", modifier: "Same env, but remove the hypothesis-specific mechanism." },
      { label: "Partial ablation", role: "control", modifier: "Keep some but not all of the hypothesis mechanisms; describe which ones." },
    ],
    algorithms: ["PPO", "SAC", "DQN"],
    n_seeds: 3,
    timesteps: 100000,
    n_eval_episodes: 10,
  },
};

function defaultExperimentConfig(): ExperimentConfig {
  return JSON.parse(JSON.stringify(PRESETS.standard));
}

function CreateProjectInline({ onClose, onCreated }: { onClose: () => void; onCreated: (id: number) => void }) {
  const { getToken } = useAuth();
  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [preset, setPreset] = useState<PresetKey>("auto");
  const [cfg, setCfg] = useState<ExperimentConfig>(defaultExperimentConfig);

  function applyPreset(next: PresetKey) {
    setPreset(next);
    if (next === "auto") return;                 // no override sent
    if (next === "custom") return;               // keep current cfg
    setCfg(JSON.parse(JSON.stringify(PRESETS[next])));
  }

  function updateCfg(patch: Partial<ExperimentConfig>) {
    setPreset("custom");
    setCfg(prev => ({ ...prev, ...patch }));
  }

  function updateVariant(idx: number, patch: Partial<EnvVariant>) {
    setPreset("custom");
    setCfg(prev => ({
      ...prev,
      env_variants: prev.env_variants.map((v, i) => (i === idx ? { ...v, ...patch } : v)),
    }));
  }

  function addVariant() {
    setPreset("custom");
    setCfg(prev => ({
      ...prev,
      env_variants: [
        ...prev.env_variants,
        { label: `Variant ${prev.env_variants.length + 1}`, role: "control", modifier: "" },
      ],
    }));
  }

  function removeVariant(idx: number) {
    setPreset("custom");
    setCfg(prev => ({ ...prev, env_variants: prev.env_variants.filter((_, i) => i !== idx) }));
  }

  function toggleAlgorithm(algo: string) {
    setPreset("custom");
    setCfg(prev => {
      const has = prev.algorithms.includes(algo);
      const next = has ? prev.algorithms.filter(a => a !== algo) : [...prev.algorithms, algo];
      return { ...prev, algorithms: next.length ? next : ["PPO"] };
    });
  }

  async function handleCreate() {
    if (!title.trim()) return;
    setCreating(true); setError("");
    try {
      const token = await getToken();
      const experimentConfig: ExperimentConfig | null =
        preset === "auto"
          ? null
          : {
              ...cfg,
              algorithms: cfg.algorithms.length ? cfg.algorithms : ["PPO"],
              env_variants: cfg.env_variants.length
                ? cfg.env_variants
                : [{ label: "Canonical", role: "treatment", modifier: "" }],
            };
      const data = await createResearchProject(title, description, topic, token, experimentConfig);
      onCreated(data.id);
    } catch (e: unknown) {
      const err = e as { code?: string; message?: string; balance?: number };
      if (err.code === "INSUFFICIENT_CREDITS") {
        setError(`Not enough credits (balance: $${err.balance?.toFixed(2) || '0.00'}). Visit Settings → Subscription to manage your plan.`);
      } else {
        setError(err.message || "Failed to create project");
      }
    } finally { setCreating(false); }
  }

  return (
    <div className="border border-[#1a1a1a] rounded-lg p-5 bg-[#0a0a0a]">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">New Research Project</h3>
        <button onClick={onClose} className="text-[#555] hover:text-white"><X size={16} /></button>
      </div>
      <div className="space-y-3">
        <div>
          <label className="text-[11px] text-[#555] block mb-1">Title *</label>
          <input value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Reward Shaping for Drone Navigation" className="w-full bg-[#111] border border-[#1a1a1a] rounded px-3 py-2 text-sm text-white outline-none focus:border-[#333]" />
        </div>
        <div>
          <label className="text-[11px] text-[#555] block mb-1">Topic / Keywords</label>
          <input value={topic} onChange={e => setTopic(e.target.value)} placeholder="e.g. reward shaping, target following, drone control" className="w-full bg-[#111] border border-[#1a1a1a] rounded px-3 py-2 text-sm text-white outline-none focus:border-[#333]" />
        </div>
        <div>
          <label className="text-[11px] text-[#555] block mb-1">Description</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)} rows={2} placeholder="Brief description of the research direction..." className="w-full bg-[#111] border border-[#1a1a1a] rounded px-3 py-2 text-sm text-white outline-none focus:border-[#333] resize-none" />
        </div>

        <AdvancedSettings
          open={showAdvanced}
          onToggle={() => setShowAdvanced(o => !o)}
          preset={preset}
          onPresetChange={applyPreset}
          cfg={cfg}
          updateCfg={updateCfg}
          updateVariant={updateVariant}
          addVariant={addVariant}
          removeVariant={removeVariant}
          toggleAlgorithm={toggleAlgorithm}
        />

        {error && <p className="text-xs text-red-400">{error}</p>}
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-1.5 text-xs text-[#888] hover:text-white border border-[#1a1a1a] rounded">Cancel</button>
          <button onClick={handleCreate} disabled={creating || !title.trim()} className="flex items-center gap-1.5 px-4 py-1.5 text-xs bg-white text-black rounded font-medium hover:bg-[#ddd] disabled:opacity-40">
            {creating ? <><Loader2 size={12} className="animate-spin" /> Creating...</> : <><Sparkles size={12} /> Create & Start</>}
          </button>
        </div>
      </div>
    </div>
  );
}

function AdvancedSettings(props: {
  open: boolean;
  onToggle: () => void;
  preset: PresetKey;
  onPresetChange: (k: PresetKey) => void;
  cfg: ExperimentConfig;
  updateCfg: (patch: Partial<ExperimentConfig>) => void;
  updateVariant: (idx: number, patch: Partial<EnvVariant>) => void;
  addVariant: () => void;
  removeVariant: (idx: number) => void;
  toggleAlgorithm: (algo: string) => void;
}) {
  const { open, onToggle, preset, onPresetChange, cfg, updateCfg, updateVariant, addVariant, removeVariant, toggleAlgorithm } = props;

  const totalRuns =
    preset === "auto"
      ? "auto"
      : `${Math.max(cfg.env_variants.length, 1)} × ${cfg.algorithms.length} × ${cfg.n_seeds} = ${
          Math.max(cfg.env_variants.length, 1) * cfg.algorithms.length * cfg.n_seeds
        }`;

  return (
    <div className="border border-[#1a1a1a] rounded">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-3 py-2 text-[11px] text-[#888] hover:text-white"
      >
        <span className="flex items-center gap-2">
          {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          Advanced settings
          <span className="text-[#555]">— preset: {preset}, total runs: {totalRuns}</span>
        </span>
      </button>

      {open && (
        <div className="px-3 pb-3 space-y-4 border-t border-[#1a1a1a] pt-3">
          {/* Presets */}
          <div>
            <label className="text-[11px] text-[#555] block mb-1.5">Preset</label>
            <div className="flex flex-wrap gap-1.5">
              {([
                ["auto", "Auto (LLM-decided)"],
                ["quick", "Quick (1 env, 1 algo)"],
                ["standard", "Standard (treatment + baseline)"],
                ["rigorous", "Rigorous (3 envs, 3 algos, 3 seeds)"],
                ["custom", "Custom"],
              ] as [PresetKey, string][]).map(([k, label]) => (
                <button
                  key={k}
                  type="button"
                  onClick={() => onPresetChange(k)}
                  className={`px-2.5 py-1 text-[11px] rounded border ${
                    preset === k
                      ? "border-white bg-white text-black"
                      : "border-[#1a1a1a] text-[#888] hover:text-white hover:border-[#333]"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {preset !== "auto" && (
            <>
              {/* Env variants */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-[11px] text-[#555]">Environment variants (ablation)</label>
                  <button
                    type="button"
                    onClick={addVariant}
                    className="text-[11px] text-[#888] hover:text-white inline-flex items-center gap-1"
                  >
                    <Plus size={10} /> Add variant
                  </button>
                </div>
                <div className="space-y-2">
                  {cfg.env_variants.map((v, idx) => (
                    <div key={idx} className="border border-[#1a1a1a] rounded p-2 space-y-1.5">
                      <div className="flex gap-2 items-start">
                        <input
                          value={v.label}
                          onChange={e => updateVariant(idx, { label: e.target.value })}
                          placeholder="Variant label (e.g. with self-observation)"
                          className="flex-1 bg-[#111] border border-[#1a1a1a] rounded px-2 py-1 text-xs text-white outline-none focus:border-[#333]"
                        />
                        <select
                          value={v.role}
                          onChange={e => updateVariant(idx, { role: e.target.value as EnvVariant["role"] })}
                          className="bg-[#111] border border-[#1a1a1a] rounded px-2 py-1 text-xs text-white outline-none focus:border-[#333]"
                        >
                          <option value="treatment">treatment</option>
                          <option value="baseline">baseline</option>
                          <option value="control">control</option>
                        </select>
                        <button
                          type="button"
                          onClick={() => removeVariant(idx)}
                          disabled={cfg.env_variants.length <= 1}
                          className="text-[#555] hover:text-red-500 disabled:opacity-30"
                          title="Remove variant"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                      <textarea
                        value={v.modifier || ""}
                        onChange={e => updateVariant(idx, { modifier: e.target.value })}
                        rows={2}
                        placeholder="Modifier — exactly what differs vs. siblings. Leave empty for the canonical/treatment version."
                        className="w-full bg-[#111] border border-[#1a1a1a] rounded px-2 py-1 text-[11px] text-white outline-none focus:border-[#333] resize-none"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Algorithms */}
              <div>
                <label className="text-[11px] text-[#555] block mb-1.5">Algorithms</label>
                <div className="flex flex-wrap gap-1.5">
                  {SUPPORTED_ALGORITHMS.map(a => {
                    const active = cfg.algorithms.includes(a);
                    return (
                      <button
                        key={a}
                        type="button"
                        onClick={() => toggleAlgorithm(a)}
                        className={`px-2.5 py-1 text-[11px] rounded border ${
                          active
                            ? "border-white bg-white text-black"
                            : "border-[#1a1a1a] text-[#888] hover:text-white hover:border-[#333]"
                        }`}
                      >
                        {a === "QRDQN" ? "QR-DQN" : a}
                      </button>
                    );
                  })}
                </div>
                <p className="text-[10px] text-[#555] mt-1">
                  Notes: SAC/TD3 require continuous actions; DQN/QR-DQN require discrete actions.
                  Incompatible combinations are skipped automatically per environment.
                </p>
              </div>

              {/* Numerics */}
              <div className="grid grid-cols-3 gap-2">
                <NumberField label="Seeds / cell" value={cfg.n_seeds} min={1} max={10}
                  onChange={n => updateCfg({ n_seeds: n })} />
                <NumberField label="Timesteps" value={cfg.timesteps} min={1000} max={2_000_000} step={1000}
                  onChange={n => updateCfg({ timesteps: n })} />
                <NumberField label="Eval episodes" value={cfg.n_eval_episodes} min={1} max={100}
                  onChange={n => updateCfg({ n_eval_episodes: n })} />
              </div>

              <p className="text-[10px] text-[#555]">
                Total training runs that will be launched: <span className="text-white font-mono">{totalRuns}</span>
              </p>
            </>
          )}

          {preset === "auto" && (
            <p className="text-[11px] text-[#666]">
              The lab will let the planning agent decide env count, algorithms, and timesteps based on your hypothesis.
              Use a preset for a controlled baseline-vs-treatment comparison.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function NumberField({ label, value, min, max, step = 1, onChange }: {
  label: string; value: number; min: number; max: number; step?: number;
  onChange: (n: number) => void;
}) {
  return (
    <div>
      <label className="text-[11px] text-[#555] block mb-1">{label}</label>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={e => {
          const n = Number(e.target.value);
          if (!Number.isFinite(n)) return;
          onChange(Math.max(min, Math.min(max, n)));
        }}
        className="w-full bg-[#111] border border-[#1a1a1a] rounded px-2 py-1 text-xs text-white outline-none focus:border-[#333]"
      />
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    active: "text-blue-400 bg-blue-400/10 border-blue-400/20",
    completed: "text-green-500 bg-green-500/10 border-green-500/20",
    paused: "text-yellow-500 bg-yellow-500/10 border-yellow-500/20",
    failed: "text-red-500 bg-red-500/10 border-red-500/20",
  };
  return (
    <span className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded border ${styles[status] || "text-[#888] bg-[#888]/10 border-[#888]/20"}`}>
      {status}
    </span>
  );
}
