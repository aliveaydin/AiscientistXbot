import { Terminal, Code, BookOpen } from "lucide-react";

const endpoints = [
  {
    category: "Catalog",
    items: [
      { method: "GET", path: "/api/rlforge/catalog", desc: "List published environments (filter: domain, difficulty, search)" },
      { method: "GET", path: "/api/rlforge/catalog/{slug}", desc: "Get environment detail by slug" },
      { method: "GET", path: "/api/rlforge/templates", desc: "List template environments" },
    ],
  },
  {
    category: "Generation",
    items: [
      { method: "POST", path: "/api/rlforge/generate", desc: "Generate env from NL description (body: {description, domain?, difficulty?})" },
      { method: "POST", path: "/api/rlforge/generate-from-paper", desc: "Generate env from uploaded PDF paper (multipart)" },
      { method: "POST", path: "/api/rlforge/fork/{env_id}", desc: "Fork an existing env with modifications" },
    ],
  },
  {
    category: "Builder",
    items: [
      { method: "POST", path: "/api/rlforge/builder/{id}/chat", desc: "Send iterate message (body: {message})" },
      { method: "GET", path: "/api/rlforge/builder/{id}/history", desc: "Get conversation history" },
      { method: "POST", path: "/api/rlforge/builder/{id}/rollback", desc: "Rollback to version (body: {version})" },
      { method: "POST", path: "/api/rlforge/builder/{id}/export-zip", desc: "Download environment as ZIP" },
    ],
  },
  {
    category: "Training",
    items: [
      { method: "POST", path: "/api/rlforge/train/{env_id}", desc: "Start SB3 training (body: {algorithm?, total_timesteps?})" },
      { method: "GET", path: "/api/rlforge/train/{env_id}/status", desc: "Get training status and results" },
      { method: "GET", path: "/api/rlforge/train/{env_id}/curve", desc: "Get training reward curve" },
      { method: "GET", path: "/api/rlforge/train/{env_id}/model", desc: "Download trained model .zip" },
    ],
  },
  {
    category: "Remote Step",
    items: [
      { method: "POST", path: "/api/rlforge/sessions", desc: "Create environment session (body: {env_id})" },
      { method: "POST", path: "/api/rlforge/sessions/{id}/step", desc: "Step environment (body: {action})" },
      { method: "POST", path: "/api/rlforge/sessions/{id}/reset", desc: "Reset environment (body: {seed?})" },
      { method: "DELETE", path: "/api/rlforge/sessions/{id}", desc: "Close session" },
    ],
  },
  {
    category: "Research",
    items: [
      { method: "POST", path: "/api/rlforge/research/projects", desc: "Create research project" },
      { method: "GET", path: "/api/rlforge/research/projects", desc: "List research projects" },
      { method: "GET", path: "/api/rlforge/research/projects/{id}", desc: "Get project detail with messages" },
      { method: "POST", path: "/api/rlforge/research/projects/{id}/upload-paper", desc: "Upload reference paper (multipart)" },
    ],
  },
];

export default function DocsPage() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-16 fade-in">
      <h1 className="text-3xl font-bold mb-2">API Documentation</h1>
      <p className="text-[#888] mb-12">Everything you need to integrate kualia.ai into your workflow.</p>

      {/* SDK */}
      <section id="sdk" className="mb-16">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Terminal size={18} /> Python SDK
        </h2>
        <div className="code-block mb-4">
          <code>pip install kualia</code>
        </div>
        <div className="code-block">
          <code>
            <span className="text-[#888]">import</span> kualia{"\n\n"}
            <span className="text-[#555]"># Configure (optional, defaults to kualia.ai)</span>{"\n"}
            kualia.configure(api_url=<span className="text-[#aaa]">&quot;https://kualia.ai&quot;</span>){"\n\n"}
            <span className="text-[#555]"># Use a pre-built environment</span>{"\n"}
            env = kualia.make(<span className="text-[#aaa]">&quot;gridworld-maze&quot;</span>){"\n"}
            obs, info = env.reset(seed=<span className="text-[#aaa]">42</span>){"\n\n"}
            <span className="text-[#888]">for</span> _ <span className="text-[#888]">in</span> range(<span className="text-[#aaa]">100</span>):{"\n"}
            {"  "}action = env.action_space.sample(){"\n"}
            {"  "}obs, reward, done, trunc, info = env.step(action){"\n"}
            {"  "}<span className="text-[#888]">if</span> done <span className="text-[#888]">or</span> trunc:{"\n"}
            {"    "}obs, info = env.reset(){"\n\n"}
            env.close(){"\n\n"}
            <span className="text-[#555]"># Generate a custom environment</span>{"\n"}
            result = kualia.generate(<span className="text-[#aaa]">&quot;5-stock trading with transaction costs&quot;</span>){"\n"}
            <span className="text-[#888]">print</span>(result)
          </code>
        </div>
      </section>

      {/* Auth */}
      <section className="mb-16">
        <h2 className="text-xl font-bold mb-4">Authentication</h2>
        <p className="text-sm text-[#888] mb-4">
          Include your API key in the X-API-Key header for authenticated requests.
        </p>
        <div className="code-block">
          <code>
            curl -H <span className="text-[#aaa]">&quot;X-API-Key: your-key&quot;</span> \{"\n"}
            {"  "}https://kualia.ai/api/rlforge/catalog
          </code>
        </div>
      </section>

      {/* Endpoints */}
      <section>
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
          <Code size={18} /> Endpoints
        </h2>
        <div className="space-y-10">
          {endpoints.map((cat) => (
            <div key={cat.category}>
              <h3 className="text-sm font-semibold text-[#888] mb-4">{cat.category}</h3>
              <div className="space-y-3">
                {cat.items.map((ep, i) => (
                  <div key={i} className="border border-[#1a1a1a] rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-1">
                      <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
                        ep.method === "GET" ? "bg-blue-950 text-blue-400" :
                        ep.method === "POST" ? "bg-green-950 text-green-400" :
                        "bg-red-950 text-red-400"
                      }`}>
                        {ep.method}
                      </span>
                      <code className="text-sm font-mono text-[#ccc]">{ep.path}</code>
                    </div>
                    <p className="text-sm text-[#888]">{ep.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Example */}
      <section className="mt-16">
        <h2 className="text-xl font-bold mb-4">Full Example: Generate + Train</h2>
        <div className="code-block">
          <code>
            <span className="text-[#555]"># 1. Generate an environment</span>{"\n"}
            curl -X POST https://kualia.ai/api/rlforge/generate \{"\n"}
            {"  "}-H <span className="text-[#aaa]">&quot;Content-Type: application/json&quot;</span> \{"\n"}
            {"  "}-d <span className="text-[#aaa]">{`'{"description": "Cart-pole with wind", "difficulty": "easy"}'`}</span>{"\n\n"}
            <span className="text-[#555]"># 2. Start training</span>{"\n"}
            curl -X POST https://kualia.ai/api/rlforge/train/1 \{"\n"}
            {"  "}-H <span className="text-[#aaa]">&quot;Content-Type: application/json&quot;</span> \{"\n"}
            {"  "}-d <span className="text-[#aaa]">{`'{"total_timesteps": 50000}'`}</span>{"\n\n"}
            <span className="text-[#555]"># 3. Check training progress</span>{"\n"}
            curl https://kualia.ai/api/rlforge/train/1/status{"\n\n"}
            <span className="text-[#555]"># 4. Download trained model</span>{"\n"}
            curl -o model.zip https://kualia.ai/api/rlforge/train/1/model
          </code>
        </div>
      </section>
    </div>
  );
}
