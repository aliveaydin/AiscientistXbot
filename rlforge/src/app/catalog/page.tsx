import Link from "next/link";
import { getCatalog } from "@/lib/api";
import { CheckCircle, XCircle, Star } from "lucide-react";

const domains = ["all", "finance", "game", "control", "optimization", "robotics"];
const difficulties = ["all", "easy", "medium", "hard"];

interface Props {
  searchParams: Promise<{ domain?: string; difficulty?: string; search?: string }>;
}

export default async function CatalogPage({ searchParams }: Props) {
  const params = await searchParams;
  const domain = params.domain && params.domain !== "all" ? params.domain : undefined;
  const difficulty = params.difficulty && params.difficulty !== "all" ? params.difficulty : undefined;

  let data = { items: [], total: 0 };
  try {
    data = await getCatalog({ domain, difficulty, search: params.search, limit: 40 });
  } catch {
    /* API unavailable */
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-16 fade-in">
      <h1 className="text-3xl font-bold mb-2">Environment Catalog</h1>
      <p className="text-[#888] mb-8">Browse published RL environments. {data.total} available.</p>

      {/* Filters */}
      <div className="flex flex-wrap gap-6 mb-10">
        <div className="flex flex-wrap gap-2">
          {domains.map((d) => (
            <Link
              key={d}
              href={`/catalog?domain=${d}${difficulty ? `&difficulty=${difficulty}` : ""}${params.search ? `&search=${params.search}` : ""}`}
              className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
                (d === "all" && !domain) || d === domain
                  ? "border-white text-white"
                  : "border-[#1a1a1a] text-[#888] hover:border-[#333]"
              }`}
            >
              {d.charAt(0).toUpperCase() + d.slice(1)}
            </Link>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          {difficulties.map((d) => (
            <Link
              key={d}
              href={`/catalog?difficulty=${d}${domain ? `&domain=${domain}` : ""}${params.search ? `&search=${params.search}` : ""}`}
              className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
                (d === "all" && !difficulty) || d === difficulty
                  ? "border-white text-white"
                  : "border-[#1a1a1a] text-[#888] hover:border-[#333]"
              }`}
            >
              {d.charAt(0).toUpperCase() + d.slice(1)}
            </Link>
          ))}
        </div>
      </div>

      {/* Grid */}
      {data.items.length === 0 ? (
        <p className="text-[#555] text-center py-20">No environments found. Try creating one!</p>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.items.map((env: any) => (
            <Link
              key={env.slug || env.id}
              href={`/catalog/${env.slug || env.id}`}
              className="border border-[#1a1a1a] rounded-xl p-5 hover:border-[#333] transition-colors group"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold group-hover:text-white transition-colors">{env.name}</h3>
                {env.is_template && <Star size={14} className="text-[#555] mt-1" />}
              </div>
              <p className="text-sm text-[#888] mb-4 line-clamp-2">{env.description}</p>
              <div className="flex items-center gap-2 flex-wrap">
                {env.domain && (
                  <span className="text-xs px-2 py-0.5 rounded-full border border-[#1a1a1a] text-[#888]">
                    {env.domain}
                  </span>
                )}
                {env.difficulty && (
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${
                    env.difficulty === "easy" ? "border-green-900 text-green-500" :
                    env.difficulty === "hard" ? "border-red-900 text-red-500" :
                    "border-yellow-900 text-yellow-500"
                  }`}>
                    {env.difficulty}
                  </span>
                )}
                {env.test_results && (
                  <span className="text-xs text-[#555] flex items-center gap-1">
                    {env.test_results.passed === env.test_results.total ? (
                      <CheckCircle size={12} className="text-green-600" />
                    ) : (
                      <XCircle size={12} className="text-red-600" />
                    )}
                    {env.test_results.passed}/{env.test_results.total}
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
