const SERVER_API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getBaseUrl(): string {
  if (typeof window === "undefined") {
    return SERVER_API;
  }
  return "";
}

async function fetchAPI(path: string) {
  const base = getBaseUrl();
  const res = await fetch(`${base}${path}`, {
    next: { revalidate: 300 },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getPublishedPapers(limit = 20, offset = 0) {
  return fetchAPI(`/api/public/papers?limit=${limit}&offset=${offset}`);
}

export async function getPaper(id: number) {
  return fetchAPI(`/api/public/papers/${id}`);
}

export async function getPublishedBlog(limit = 20, offset = 0) {
  return fetchAPI(`/api/public/blog?limit=${limit}&offset=${offset}`);
}

export async function getBlogPost(id: number) {
  return fetchAPI(`/api/public/blog/${id}`);
}

export async function getPublishedEnvironments(
  limit = 20,
  offset = 0,
  category?: string
) {
  let url = `/api/public/environments?limit=${limit}&offset=${offset}`;
  if (category) url += `&category=${category}`;
  return fetchAPI(url);
}

export async function getEnvironment(id: number) {
  return fetchAPI(`/api/public/environments/${id}`);
}

export async function getPublicStats() {
  return fetchAPI("/api/public/stats");
}
