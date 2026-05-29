"use client";
import { useAuth } from "@clerk/nextjs";
import { Check, X, ArrowRight } from "lucide-react";
import Link from "next/link";

const plans = [
  {
    name: "Free",
    price: 0,
    color: "gray",
    description: "Try the platform — explore and experiment",
    features: [
      { text: "1 environment", included: true },
      { text: "50K max training steps", included: true },
      { text: "Builder chat", included: true },
      { text: "PDF download", included: false },
      { text: "GitHub export", included: false },
      { text: "Buy additional credits", included: false },
    ],
    cta: "Get Started",
    popular: false,
  },
  {
    name: "Starter",
    price: 19,
    color: "blue",
    description: "For individual researchers and students",
    features: [
      { text: "5 environments", included: true },
      { text: "500K max training steps", included: true },
      { text: "Builder chat", included: true },
      { text: "PDF download", included: true },
      { text: "GitHub export", included: true },
      { text: "Buy additional credits", included: true },
    ],
    cta: "Start Building",
    popular: false,
  },
  {
    name: "Pro",
    price: 49,
    color: "emerald",
    description: "For active researchers and teams",
    features: [
      { text: "20 environments", included: true },
      { text: "2M max training steps", included: true },
      { text: "Builder chat", included: true },
      { text: "PDF download", included: true },
      { text: "GitHub export", included: true },
      { text: "Buy additional credits", included: true },
    ],
    cta: "Go Pro",
    popular: true,
  },
  {
    name: "Lab",
    price: 149,
    color: "purple",
    description: "For research labs and organizations",
    features: [
      { text: "100 environments", included: true },
      { text: "5M max training steps", included: true },
      { text: "Builder chat", included: true },
      { text: "PDF download", included: true },
      { text: "GitHub export", included: true },
      { text: "Buy additional credits", included: true },
    ],
    cta: "Get Started",
    popular: false,
  },
];

const borderColors: Record<string, string> = {
  gray: "border-gray-700",
  blue: "border-blue-500/40",
  emerald: "border-emerald-500/50",
  purple: "border-purple-500/40",
};
const bgColors: Record<string, string> = {
  gray: "bg-gray-900",
  blue: "bg-blue-950/30",
  emerald: "bg-emerald-950/30",
  purple: "bg-purple-950/30",
};
const btnColors: Record<string, string> = {
  gray: "bg-gray-700 hover:bg-gray-600",
  blue: "bg-blue-600 hover:bg-blue-500",
  emerald: "bg-emerald-600 hover:bg-emerald-500",
  purple: "bg-purple-600 hover:bg-purple-500",
};

export default function PricingPage() {
  const { isSignedIn } = useAuth();

  return (
    <div className="min-h-screen bg-black text-white">
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
            Simple, Credit-Based Pricing
          </h1>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            Pay only for what you use. Credits cover all operations:
            environment generation, training, research, and paper writing.
          </p>
        </div>
      </section>

      <section className="pb-20 px-4">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl border-2 ${borderColors[plan.color]} ${bgColors[plan.color]} p-6 flex flex-col`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-emerald-500 text-black text-xs font-bold rounded-full">
                  Most Popular
                </div>
              )}
              <h3 className="text-xl font-bold mb-1">{plan.name}</h3>
              <p className="text-sm text-gray-400 mb-4">{plan.description}</p>
              <div className="mb-6">
                <span className="text-4xl font-bold">${plan.price}</span>
                <span className="text-gray-500 text-sm">/month</span>
              </div>
              
              <ul className="space-y-3 flex-1 mb-6">
                {plan.features.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    {f.included ? (
                      <Check className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                    ) : (
                      <X className="w-4 h-4 text-gray-600 mt-0.5 flex-shrink-0" />
                    )}
                    <span className={f.included ? "text-gray-300" : "text-gray-600"}>
                      {f.text}
                    </span>
                  </li>
                ))}
              </ul>
              <Link
                href={isSignedIn ? "/dashboard" : "/sign-up"}
                className={`w-full py-2.5 rounded-lg text-sm font-medium text-center text-white ${btnColors[plan.color]} transition-colors`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      <section className="pb-20 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-4">Need More Credits?</h2>
          <p className="text-gray-400 mb-6">
            Starter, Pro, and Lab plans can purchase additional credits at any time.
            Credits never expire and roll over month to month.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link
              href={isSignedIn ? "/dashboard" : "/sign-up"}
              className="inline-flex items-center gap-2 px-6 py-3 bg-white text-black font-medium rounded-lg hover:bg-gray-100 transition-colors"
            >
              Get Started <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
}
