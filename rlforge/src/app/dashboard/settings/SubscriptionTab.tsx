"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import {
  TrendingUp, Box, FlaskConical, Cpu, Check, X,
  ArrowUpRight, Loader2, Clock, Infinity, Shield,
} from "lucide-react";
import { getSubscription } from "@/lib/api";

interface Plan {
  id: number;
  name: string;
  display_name: string;
  price_monthly: number;
  monthly_credits: number;
  max_environments: number;
  max_training_steps: number;
  pdf_download: boolean;
  github_export: boolean;
  can_buy_credits: boolean;
}

interface Transaction {
  id: number;
  amount: number;
  balance_after: number;
  operation: string;
  created_at: string;
}

interface SubscriptionData {
  is_admin: boolean;
  balance: number;
  plan: Plan | null;
  plan_started_at: string | null;
  plan_period_end: string | null;
  usage: {
    environments: number;
    training_runs: number;
    research_projects: number;
    monthly: {
      total_spent: number;
      by_operation: Record<string, number>;
    };
  };
  limits: {
    max_environments: number;
    max_training_steps: number;
    pdf_download: boolean;
    github_export: boolean;
    can_buy_credits: boolean;
  };
  available_plans: Plan[];
  recent_transactions: Transaction[];
}

const OP_LABELS: Record<string, string> = {
  env_generation: "Environment Generation",
  builder_chat: "Builder Chat",
  training: "Training",
  research_hypothesis: "Research — Hypothesis",
  research_experiment: "Research — Experiment",
  research_paper: "Research — Paper",
  paper_from_env: "Paper from Env",
  reference_search: "Reference Search",
  monthly_grant: "Monthly Credit Grant",
  credit_purchase: "Credit Purchase",
  admin_grant: "Admin Grant",
};

function formatSteps(steps: number): string {
  if (steps === -1) return "Unlimited";
  if (steps >= 1_000_000) return `${(steps / 1_000_000).toFixed(1)}M`;
  if (steps >= 1_000) return `${(steps / 1_000).toFixed(0)}K`;
  return String(steps);
}

export default function SubscriptionTab() {
  const { getToken } = useAuth();
  const [data, setData] = useState<SubscriptionData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const token = await getToken();
        if (token) {
          const res = await getSubscription(token);
          setData(res);
        }
      } catch (e) {
        console.error("Failed to load subscription:", e);
      } finally {
        setLoading(false);
      }
    })();
  }, [getToken]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-5 h-5 animate-spin text-[#555]" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-20 text-[#666]">
        Failed to load subscription data.
      </div>
    );
  }

  const currentPlan = data.plan;
  const isFreePlan = currentPlan?.name === "free";

  return (
    <div className="space-y-8">
      {/* Admin badge */}
      {data.is_admin && (
        <div className="flex items-center gap-2 px-4 py-2.5 bg-[#0a1628] border border-blue-900/50 rounded-lg">
          <Shield className="w-4 h-4 text-blue-400" />
          <span className="text-sm text-blue-300 font-medium">Admin Account — Unlimited access</span>
        </div>
      )}

      {/* Current plan + balance */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl p-5">
          <div className="text-[10px] uppercase tracking-wider text-[#555] mb-2">Current Plan</div>
          <div className="text-2xl font-bold text-white">{currentPlan?.display_name || "Free"}</div>
          <div className="text-xs text-[#666] mt-1">
            {currentPlan && currentPlan.price_monthly > 0
              ? `$${currentPlan.price_monthly}/month`
              : "Free tier"}
          </div>
        </div>
        <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl p-5">
          <div className="text-[10px] uppercase tracking-wider text-[#555] mb-2">Credit Balance</div>
          <div className="text-2xl font-bold text-white">
            {data.is_admin ? "∞" : `$${data.balance.toFixed(2)}`}
          </div>
          <div className="text-xs text-[#666] mt-1">available balance</div>
        </div>
        <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl p-5">
          <div className="text-[10px] uppercase tracking-wider text-[#555] mb-2">This Month</div>
          <div className="text-2xl font-bold text-white">
            ${data.usage.monthly.total_spent.toFixed(2)}
          </div>
          <div className="text-xs text-[#666] mt-1">
            credits used
          </div>
        </div>
      </div>

      {/* Usage overview */}
      <div>
        <h3 className="text-sm font-semibold text-white mb-3">Usage</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <UsageCard
            icon={Box}
            label="Environments"
            current={data.usage.environments}
            limit={data.limits.max_environments}
          />
          <UsageCard
            icon={Cpu}
            label="Max Training Steps"
            current={null}
            limit={data.limits.max_training_steps}
            suffix="per run"
          />
          <UsageCard
            icon={FlaskConical}
            label="Research Projects"
            current={data.usage.research_projects}
            limit={-1}
          />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
          <FeatureChip label="PDF Download" enabled={data.limits.pdf_download} />
          <FeatureChip label="GitHub Export" enabled={data.limits.github_export} />
          <FeatureChip label="Buy Credits" enabled={data.limits.can_buy_credits} />
          <FeatureChip label="Training Runs" enabled={true} value={String(data.usage.training_runs)} />
        </div>
      </div>

      {/* Monthly breakdown */}
      {Object.keys(data.usage.monthly.by_operation).length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-white mb-3">Monthly Breakdown</h3>
          <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl divide-y divide-[#1a1a1a]">
            {Object.entries(data.usage.monthly.by_operation)
              .sort(([, a], [, b]) => b - a)
              .map(([op, spent]) => (
                <div key={op} className="flex items-center justify-between px-4 py-3">
                  <span className="text-sm text-[#aaa]">{OP_LABELS[op] || op}</span>
                  <span className="text-sm font-medium text-white">${spent.toFixed(4)}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Available Plans */}
      <div>
        <h3 className="text-sm font-semibold text-white mb-3">Available Plans</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {data.available_plans.map((plan) => {
            const isCurrent = currentPlan?.name === plan.name;
            return (
              <div
                key={plan.id}
                className={`relative bg-[#0a0a0a] border rounded-xl p-5 transition-colors ${
                  isCurrent ? "border-white" : "border-[#1a1a1a] hover:border-[#333]"
                }`}
              >
                {isCurrent && (
                  <div className="absolute -top-2.5 left-4 px-2 py-0.5 bg-white text-black text-[10px] font-bold uppercase tracking-wider rounded">
                    Current
                  </div>
                )}
                <div className="text-base font-bold text-white mb-1">{plan.display_name}</div>
                <div className="text-2xl font-bold text-white mb-3">
                  {plan.price_monthly === 0 ? "Free" : `$${plan.price_monthly}`}
                  {plan.price_monthly > 0 && <span className="text-xs text-[#666] font-normal">/mo</span>}
                </div>
                <div className="space-y-2 text-xs text-[#888]">
                  <div className="flex items-center gap-2">
                    <Box className="w-3 h-3" />
                    {plan.max_environments === -1 ? "Unlimited" : plan.max_environments} environments
                  </div>
                  <div className="flex items-center gap-2">
                    <Cpu className="w-3 h-3" />
                    {formatSteps(plan.max_training_steps)} steps/run
                  </div>
                  <div className="flex items-center gap-2">
                    {plan.pdf_download ? <Check className="w-3 h-3 text-green-500" /> : <X className="w-3 h-3 text-[#333]" />}
                    PDF Download
                  </div>
                  <div className="flex items-center gap-2">
                    {plan.github_export ? <Check className="w-3 h-3 text-green-500" /> : <X className="w-3 h-3 text-[#333]" />}
                    GitHub Export
                  </div>
                </div>
                {!isCurrent && plan.price_monthly > (currentPlan?.price_monthly || 0) && (
                  <button className="mt-4 w-full flex items-center justify-center gap-1.5 px-3 py-2 bg-white text-black text-xs font-medium rounded-lg hover:bg-[#e5e5e5] transition-colors">
                    Upgrade <ArrowUpRight className="w-3 h-3" />
                  </button>
                )}
                {!isCurrent && plan.price_monthly > 0 && plan.price_monthly <= (currentPlan?.price_monthly || 0) && (
                  <div className="mt-4 text-center text-[10px] text-[#555]">
                    Contact support to change plans
                  </div>
                )}
              </div>
            );
          })}
        </div>
        <p className="text-[10px] text-[#555] mt-3">
          Payment integration coming soon. Upgrades will be processed via Stripe.
        </p>
      </div>

      {/* Recent transactions */}
      {data.recent_transactions.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-white mb-3">Recent Transactions</h3>
          <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[#1a1a1a] text-[#555]">
                  <th className="text-left px-4 py-2.5 font-medium">Operation</th>
                  <th className="text-right px-4 py-2.5 font-medium">Amount</th>
                  <th className="text-right px-4 py-2.5 font-medium">Balance</th>
                  <th className="text-right px-4 py-2.5 font-medium">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#111]">
                {data.recent_transactions.map((tx) => (
                  <tr key={tx.id} className="text-[#aaa]">
                    <td className="px-4 py-2.5">{OP_LABELS[tx.operation] || tx.operation}</td>
                    <td className={`text-right px-4 py-2.5 font-medium ${tx.amount >= 0 ? "text-green-500" : "text-red-400"}`}>
                      {tx.amount >= 0 ? "+" : ""}${Math.abs(tx.amount).toFixed(4)}
                    </td>
                    <td className="text-right px-4 py-2.5">${tx.balance_after.toFixed(4)}</td>
                    <td className="text-right px-4 py-2.5 text-[#666]">
                      {tx.created_at ? new Date(tx.created_at).toLocaleDateString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function UsageCard({
  icon: Icon,
  label,
  current,
  limit,
  suffix,
}: {
  icon: typeof Box;
  label: string;
  current: number | null;
  limit: number;
  suffix?: string;
}) {
  const isUnlimited = limit === -1;
  const pct = isUnlimited || current === null ? 0 : Math.min(100, (current / limit) * 100);
  const isNearLimit = !isUnlimited && current !== null && pct >= 80;

  return (
    <div className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-3.5 h-3.5 text-[#555]" />
        <span className="text-[10px] uppercase tracking-wider text-[#555]">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        {current !== null && (
          <>
            <span className={`text-lg font-bold ${isNearLimit ? "text-amber-400" : "text-white"}`}>
              {current}
            </span>
            <span className="text-xs text-[#555]">/</span>
          </>
        )}
        <span className="text-xs text-[#666]">
          {isUnlimited ? (
            <span className="flex items-center gap-1"><Infinity className="w-3 h-3" /> Unlimited</span>
          ) : (
            `${formatSteps(limit)}${suffix ? ` ${suffix}` : ""}`
          )}
        </span>
      </div>
      {current !== null && !isUnlimited && (
        <div className="mt-2 h-1 bg-[#1a1a1a] rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${isNearLimit ? "bg-amber-500" : "bg-white"}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
    </div>
  );
}

function FeatureChip({ label, enabled, value }: { label: string; enabled: boolean; value?: string }) {
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs ${
      enabled
        ? "border-[#1a1a1a] bg-[#0a0a0a] text-[#aaa]"
        : "border-[#111] bg-[#050505] text-[#444]"
    }`}>
      {enabled ? <Check className="w-3 h-3 text-green-500" /> : <X className="w-3 h-3 text-[#333]" />}
      {label}
      {value && <span className="ml-auto font-medium text-white">{value}</span>}
    </div>
  );
}
