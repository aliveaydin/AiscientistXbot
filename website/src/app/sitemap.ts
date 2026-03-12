import { MetadataRoute } from "next";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = "https://kualia.ai";

  const staticPages = [
    { url: base, lastModified: new Date(), changeFrequency: "weekly" as const, priority: 1 },
    { url: `${base}/research`, lastModified: new Date(), changeFrequency: "daily" as const, priority: 0.9 },
    { url: `${base}/environments`, lastModified: new Date(), changeFrequency: "daily" as const, priority: 0.9 },
    { url: `${base}/blog`, lastModified: new Date(), changeFrequency: "daily" as const, priority: 0.8 },
    { url: `${base}/about`, lastModified: new Date(), changeFrequency: "monthly" as const, priority: 0.5 },
  ];

  let dynamicPages: MetadataRoute.Sitemap = [];

  try {
    const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    const [papers, posts, envs] = await Promise.all([
      fetch(`${API}/api/public/papers?limit=100`).then((r) => r.ok ? r.json() : { items: [] }).catch(() => ({ items: [] })),
      fetch(`${API}/api/public/blog?limit=100`).then((r) => r.ok ? r.json() : { items: [] }).catch(() => ({ items: [] })),
      fetch(`${API}/api/public/environments?limit=100`).then((r) => r.ok ? r.json() : { items: [] }).catch(() => ({ items: [] })),
    ]);

    dynamicPages = [
      ...papers.items.map((p: { id: number; published_at?: string }) => ({
        url: `${base}/research/${p.id}`,
        lastModified: p.published_at ? new Date(p.published_at) : new Date(),
        changeFrequency: "monthly" as const,
        priority: 0.8,
      })),
      ...posts.items.map((p: { id: number; published_at?: string }) => ({
        url: `${base}/blog/${p.id}`,
        lastModified: p.published_at ? new Date(p.published_at) : new Date(),
        changeFrequency: "monthly" as const,
        priority: 0.7,
      })),
      ...envs.items.map((e: { id: number; published_at?: string }) => ({
        url: `${base}/environments/${e.id}`,
        lastModified: e.published_at ? new Date(e.published_at) : new Date(),
        changeFrequency: "monthly" as const,
        priority: 0.7,
      })),
    ];
  } catch {
    // API might not be available during build
  }

  return [...staticPages, ...dynamicPages];
}
