import type { MetadataRoute } from "next";

const BASE = "https://kualia.ai";
const API = process.env.NEXT_PUBLIC_API_URL || "http://bot:8000";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticPages: MetadataRoute.Sitemap = [
    { url: BASE, lastModified: new Date(), changeFrequency: "weekly", priority: 1.0 },
    { url: `${BASE}/environments`, lastModified: new Date(), changeFrequency: "daily", priority: 0.9 },
    { url: `${BASE}/blog`, lastModified: new Date(), changeFrequency: "daily", priority: 0.9 },
    { url: `${BASE}/catalog`, lastModified: new Date(), changeFrequency: "daily", priority: 0.8 },
    { url: `${BASE}/create`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.8 },
    { url: `${BASE}/research`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.7 },
    { url: `${BASE}/docs`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.7 },
  ];

  let envPages: MetadataRoute.Sitemap = [];
  try {
    const res = await fetch(`${API}/api/public/environments?limit=100`, { next: { revalidate: 3600 } });
    if (res.ok) {
      const data = await res.json();
      envPages = (data.items || []).map((e: any) => ({
        url: `${BASE}/environments/${e.id}`,
        lastModified: new Date(e.published_at || Date.now()),
        changeFrequency: "weekly" as const,
        priority: 0.6,
      }));
    }
  } catch {}

  let blogPages: MetadataRoute.Sitemap = [];
  try {
    const res = await fetch(`${API}/api/public/blog?limit=100`, { next: { revalidate: 3600 } });
    if (res.ok) {
      const data = await res.json();
      blogPages = (data.items || []).map((p: any) => ({
        url: `${BASE}/blog/${p.id}`,
        lastModified: new Date(p.published_at || Date.now()),
        changeFrequency: "monthly" as const,
        priority: 0.5,
      }));
    }
  } catch {}

  let catalogPages: MetadataRoute.Sitemap = [];
  try {
    const res = await fetch(`${API}/api/rlforge/catalog?limit=100`, { next: { revalidate: 3600 } });
    if (res.ok) {
      const data = await res.json();
      catalogPages = (data.items || []).map((e: any) => ({
        url: `${BASE}/catalog/${e.slug}`,
        lastModified: new Date(e.updated_at || e.created_at || Date.now()),
        changeFrequency: "weekly" as const,
        priority: 0.6,
      }));
    }
  } catch {}

  return [...staticPages, ...envPages, ...blogPages, ...catalogPages];
}
