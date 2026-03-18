const API_BASE =
  typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_API_URL || "http://bot:8000"
    : process.env.NEXT_PUBLIC_BACKEND_URL || "";

interface FetchOptions extends RequestInit {
  revalidate?: number;
}

async function fetchAPI(path: string, options: FetchOptions = {}) {
  const { revalidate = 60, ...init } = options;
  const url = `${API_BASE}${path}`;
  const isServer = typeof window === "undefined";
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fetchOpts: any = { ...init };
  if (isServer && (!init.method || init.method === "GET")) {
    fetchOpts.next = { revalidate };
  } else {
    fetchOpts.cache = "no-store";
  }
  const res = await fetch(url, fetchOpts);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export async function getCatalog(params?: {
  domain?: string;
  difficulty?: string;
  search?: string;
  limit?: number;
  offset?: number;
}) {
  const sp = new URLSearchParams();
  if (params?.domain) sp.set("domain", params.domain);
  if (params?.difficulty) sp.set("difficulty", params.difficulty);
  if (params?.search) sp.set("search", params.search);
  if (params?.limit) sp.set("limit", String(params.limit));
  if (params?.offset) sp.set("offset", String(params.offset));
  const qs = sp.toString();
  return fetchAPI(`/api/rlforge/catalog${qs ? `?${qs}` : ""}`);
}

export async function getEnvBySlug(slug: string) {
  return fetchAPI(`/api/rlforge/catalog/${slug}`);
}

export async function getEnvById(id: number) {
  return fetchAPI(`/api/rlforge/envs/${id}`);
}

export async function getTemplates() {
  return fetchAPI("/api/rlforge/templates");
}

export async function generateEnv(
  description: string,
  domain?: string,
  difficulty?: string,
  token?: string | null
) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return fetchAPI("/api/rlforge/generate", {
    method: "POST",
    headers,
    body: JSON.stringify({ description, domain, difficulty }),
  });
}

export async function getBuilderHistory(envId: number) {
  return fetchAPI(`/api/rlforge/builder/${envId}/history`);
}

export async function builderChat(envId: number, message: string, token?: string | null) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return fetchAPI(`/api/rlforge/builder/${envId}/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify({ message }),
  });
}

export async function builderRollback(envId: number, version: number) {
  return fetchAPI(`/api/rlforge/builder/${envId}/rollback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ version }),
  });
}

export async function exportZip(envId: number) {
  const url = `${API_BASE}/api/rlforge/builder/${envId}/export-zip`;
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) throw new Error("Export failed");
  return res.blob();
}

export async function getResearchProjects(limit = 20, offset = 0) {
  return fetchAPI(`/api/rlforge/research/projects?limit=${limit}&offset=${offset}`);
}

export async function getResearchProject(id: number) {
  return fetchAPI(`/api/rlforge/research/projects/${id}`);
}

export async function createResearchProject(title: string, description?: string, topic?: string, token?: string | null) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return fetchAPI("/api/rlforge/research/projects", {
    method: "POST",
    headers,
    body: JSON.stringify({ title, description, topic }),
  });
}

export async function startTraining(envId: number, config?: Record<string, unknown>, token?: string | null) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return fetchAPI(`/api/rlforge/train/${envId}`, {
    method: "POST",
    headers,
    body: JSON.stringify(config || {}),
  });
}

export async function getTrainingStatus(envId: number) {
  return fetchAPI(`/api/rlforge/train/${envId}/status`, { revalidate: 5 });
}

export async function getTrainingCurve(envId: number) {
  return fetchAPI(`/api/rlforge/train/${envId}/curve`, { revalidate: 5 });
}

export async function getTrainingReplay(envId: number) {
  return fetchAPI(`/api/rlforge/train/${envId}/replay`, { revalidate: 5 });
}

export async function getTrainingHistory(envId: number) {
  return fetchAPI(`/api/rlforge/train/${envId}/history`, { revalidate: 5 });
}

export async function getEnvVersions(envId: number) {
  return fetchAPI(`/api/rlforge/envs/${envId}/versions`);
}

export async function getTrainingReport(envId: number, runId: number) {
  return fetchAPI(`/api/rlforge/train/${envId}/report/${runId}`, { revalidate: 30 });
}

// --- Public API (blog, environments, papers, stats) ---

export async function getPublicBlogPosts(limit = 20, offset = 0) {
  return fetchAPI(`/api/public/blog?limit=${limit}&offset=${offset}`, { revalidate: 300 });
}

export async function getPublicBlogPost(id: number) {
  return fetchAPI(`/api/public/blog/${id}`, { revalidate: 300 });
}

export async function getPublicEnvironments(limit = 20, offset = 0, category?: string) {
  const sp = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (category) sp.set("category", category);
  return fetchAPI(`/api/public/environments?${sp}`, { revalidate: 300 });
}

export async function getPublicEnvironment(id: number) {
  return fetchAPI(`/api/public/environments/${id}`, { revalidate: 300 });
}

export async function getPublicPapers(limit = 20, offset = 0) {
  return fetchAPI(`/api/public/papers?limit=${limit}&offset=${offset}`, { revalidate: 300 });
}

export async function getPublicStats() {
  return fetchAPI("/api/public/stats", { revalidate: 600 });
}

// --- Authenticated User API ---

export async function authFetch(path: string, token: string, options: FetchOptions = {}) {
  return fetchAPI(path, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function syncUser(token: string, data: Record<string, string>) {
  return authFetch("/api/users/sync", token, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function getMe(token: string) {
  return authFetch("/api/users/me", token);
}

export async function updateMe(token: string, data: Record<string, string>) {
  return authFetch("/api/users/me", token, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function getMyEnvironments(token: string, limit = 50, offset = 0) {
  return authFetch(`/api/users/me/environments?limit=${limit}&offset=${offset}`, token);
}

export async function getMyTraining(token: string, limit = 50, offset = 0) {
  return authFetch(`/api/users/me/training?limit=${limit}&offset=${offset}`, token);
}

export async function getMyResearch(token: string, limit = 50, offset = 0) {
  return authFetch(`/api/users/me/research?limit=${limit}&offset=${offset}`, token);
}

export async function getPublicProfile(username: string) {
  return fetchAPI(`/api/users/${username}`, { revalidate: 120 });
}
