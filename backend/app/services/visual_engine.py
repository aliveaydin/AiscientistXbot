"""
Visual Content Engine for kualia.ai marketing.
Renders HTML/CSS templates and AI-designed visuals to PNG using Playwright.
"""
import logging
import os
import re
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger("visual_engine")

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "marketing")


def _ensure_templates_dir():
    os.makedirs(TEMPLATES_DIR, exist_ok=True)


# ─────────────────────────────────────────────────
# AI VISUAL DESIGNER PROMPT
# ─────────────────────────────────────────────────

VISUAL_DESIGNER_PROMPT = """You are a world-class graphic designer creating marketing visuals for kualia.ai — an AI platform for RL environment generation, agent training, and research.

Your job: write a COMPLETE HTML document with inline CSS that will be screenshot at 1200x675px.

CRITICAL RULES — FOLLOW EXACTLY:
1. Canvas: body must be exactly width:1200px; height:675px; overflow:hidden;
2. Background: WHITE (#ffffff). All backgrounds must be white or very light gray (#f8fafc).
3. Text: BLACK (#111827) for headings, dark gray (#374151) for body, medium gray (#6b7280) for labels.
4. Accent colors: #2563eb (blue), #7c3aed (purple), #059669 (green), #d97706 (amber), #dc2626 (red).
5. Font: font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
6. Branding: always put "kualia.ai" in bottom-right corner, blue (#2563eb), font-weight:700.
7. NO external resources. No images, no CDN, no scripts. Pure HTML+CSS+inline SVG only.
8. YOU MUST GENERATE ACTUAL CONTENT. The visual must contain real text, real boxes, real elements. NEVER return just a title with empty space.

ELEMENT TECHNIQUES:
- Boxes: use border:2px solid #e5e7eb; border-radius:12px; padding:20px; background:#f9fafb;
- Arrows between boxes: use Unicode → or ➜ at font-size:28px, or a connecting div with border
- Numbered circles: width:36px;height:36px;border-radius:50%;background:#2563eb;color:white;display:flex;align-items:center;justify-content:center;font-weight:700;
- Bar charts: div elements with varying heights and colored backgrounds inside a flex container
- SVG curves: inline <svg> with <polyline> or <path> for training curves
- Icons: use Unicode emoji or symbols (⚡🎯🧠📊🔬💡✅❌🎮🏗️📈)
- Grid layouts: CSS grid or flexbox to arrange multiple items

VISUAL TYPES:
- flow_diagram: 3-5 step process shown left-to-right or top-to-bottom. Each step is a bordered box with a number, title, and description. Steps are connected with arrows (→). Example layout: [Step 1] → [Step 2] → [Step 3]
- comparison: Two or three columns side by side comparing features. Use a header row and feature rows with ✅/❌ marks.
- training_curve: An inline SVG chart showing a learning curve going up. Include Y-axis label (reward), X-axis label (steps), a colored polyline, and key metric callouts.
- architecture: System diagram with layered boxes. Top layer, middle layer, bottom layer connected by vertical arrows.
- step_guide: Vertical list of 3-5 steps, each with a colored number circle, bold title, and description paragraph.
- infographic: Large hero number at top, 3-4 stat cards below, then a key insight text.
- tip_card: A highlighted tip box with an icon, bold title, explanation text, and a code example or formula.

EXAMPLE STRUCTURE for a flow_diagram:
<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1200px;height:675px;background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:40px}
h1{font-size:32px;color:#111827;margin-bottom:30px;text-align:center}
.flow{display:flex;align-items:center;justify-content:center;gap:16px;margin-top:20px}
.step{border:2px solid #e5e7eb;border-radius:12px;padding:24px;width:280px;background:#f9fafb}
.step .num{width:36px;height:36px;border-radius:50%;background:#2563eb;color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;margin-bottom:12px}
.step h3{font-size:18px;color:#111827;margin-bottom:8px}
.step p{font-size:13px;color:#6b7280;line-height:1.5}
.arrow{font-size:28px;color:#2563eb}
.brand{position:absolute;bottom:20px;right:40px;font-size:16px;font-weight:700;color:#2563eb}
</style></head><body>
<h1>How to Generate an RL Environment</h1>
<div class="flow">
  <div class="step"><div class="num">1</div><h3>Describe</h3><p>Write what your environment should do in plain English</p></div>
  <div class="arrow">→</div>
  <div class="step"><div class="num">2</div><h3>Generate</h3><p>AI creates Gymnasium-compatible Python code</p></div>
  <div class="arrow">→</div>
  <div class="step"><div class="num">3</div><h3>Train</h3><p>Pick PPO, SAC, or DQN and start training</p></div>
</div>
<div class="brand">kualia.ai</div>
</body></html>

Follow that structure but CREATE YOUR OWN CONTENT based on the concept given.
Output ONLY the complete HTML document. No explanation. Start with <!DOCTYPE html>."""


SCREENSHOT_BASE_URL = os.getenv("SCREENSHOT_BASE_URL", "http://rlforge:3001")


# ─────────────────────────────────────────────────
# STATIC TEMPLATES (kept for backward compatibility)
# ─────────────────────────────────────────────────

FEATURE_CARD_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1200px; height: 675px; display: flex; align-items: center; justify-content: center;
       background: #ffffff;
       font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
.card { width: 1080px; padding: 60px; }
.badge { display: inline-block; background: #eff6ff; color: #2563eb;
         padding: 8px 20px; border-radius: 20px; font-size: 16px; font-weight: 600;
         border: 1px solid #bfdbfe; margin-bottom: 24px; }
h1 { font-size: 48px; font-weight: 800; color: #111827; line-height: 1.2; margin-bottom: 20px; }
p { font-size: 24px; color: #6b7280; line-height: 1.6; max-width: 800px; }
.footer { margin-top: 40px; display: flex; align-items: center; gap: 12px; }
.logo { font-size: 20px; font-weight: 700; color: #2563eb; }
.url { font-size: 18px; color: #9ca3af; }
</style></head><body>
<div class="card">
  <div class="badge">{{BADGE}}</div>
  <h1>{{TITLE}}</h1>
  <p>{{DESCRIPTION}}</p>
  <div class="footer">
    <span class="logo">kualia.ai</span>
    <span class="url">— Generate. Train. Experiment. Publish.</span>
  </div>
</div>
</body></html>"""

TRAINING_RESULT_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1200px; height: 675px; display: flex; align-items: center; justify-content: center;
       background: #ffffff;
       font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
.card { width: 1080px; padding: 50px; }
.header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; }
.title-section h2 { font-size: 36px; color: #111827; font-weight: 700; }
.title-section .sub { font-size: 18px; color: #6b7280; margin-top: 8px; }
.algo-badge { background: #f3f0ff; color: #7c3aed; padding: 10px 24px;
              border-radius: 12px; font-size: 18px; font-weight: 700;
              border: 1px solid #ddd6fe; }
.metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 20px; }
.metric { background: #f9fafb; border: 1px solid #e5e7eb;
          border-radius: 16px; padding: 24px; text-align: center; }
.metric .value { font-size: 36px; font-weight: 800; color: #059669; }
.metric .label { font-size: 14px; color: #6b7280; margin-top: 8px; text-transform: uppercase;
                 letter-spacing: 1px; }
.footer { margin-top: 30px; display: flex; justify-content: space-between; align-items: center; }
.logo { font-size: 20px; font-weight: 700; color: #2563eb; }
.generated { font-size: 14px; color: #9ca3af; }
</style></head><body>
<div class="card">
  <div class="header">
    <div class="title-section">
      <h2>{{ENV_NAME}}</h2>
      <div class="sub">{{DOMAIN}} • {{STEPS}} training steps</div>
    </div>
    <div class="algo-badge">{{ALGORITHM}}</div>
  </div>
  <div class="metrics">
    <div class="metric"><div class="value">{{MEAN_REWARD}}</div><div class="label">Mean Reward</div></div>
    <div class="metric"><div class="value">{{SUCCESS_RATE}}</div><div class="label">Success Rate</div></div>
    <div class="metric"><div class="value">{{EPISODES}}</div><div class="label">Episodes</div></div>
    <div class="metric"><div class="value">{{TRAIN_TIME}}</div><div class="label">Train Time</div></div>
  </div>
  <div class="footer">
    <span class="logo">kualia.ai</span>
    <span class="generated">Generated & trained on kualia.ai</span>
  </div>
</div>
</body></html>"""

CODE_SNIPPET_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1200px; height: 675px; display: flex; align-items: center; justify-content: center;
       background: #ffffff; font-family: 'Fira Code', 'Courier New', monospace; }
.card { width: 1100px; padding: 40px; }
.title-bar { display: flex; align-items: center; gap: 8px; margin-bottom: 20px; }
.dot { width: 12px; height: 12px; border-radius: 50%; }
.dot.r { background: #ff5f57; } .dot.y { background: #febc2e; } .dot.g { background: #28c840; }
.filename { margin-left: 12px; color: #6b7280; font-size: 14px; }
.code { background: #f8fafc; border-radius: 12px; padding: 30px; border: 1px solid #e5e7eb; }
pre { color: #1e293b; font-size: 16px; line-height: 1.8; white-space: pre-wrap; }
.keyword { color: #7c3aed; } .string { color: #059669; } .func { color: #2563eb; }
.comment { color: #9ca3af; } .number { color: #d97706; }
.footer { margin-top: 20px; display: flex; justify-content: space-between; }
.logo { font-size: 18px; font-weight: 700; color: #2563eb; font-family: sans-serif; }
.label { font-size: 14px; color: #9ca3af; font-family: sans-serif; }
</style></head><body>
<div class="card">
  <div class="title-bar">
    <div class="dot r"></div><div class="dot y"></div><div class="dot g"></div>
    <span class="filename">{{FILENAME}}</span>
  </div>
  <div class="code"><pre>{{CODE}}</pre></div>
  <div class="footer">
    <span class="logo">kualia.ai</span>
    <span class="label">AI-generated RL environment</span>
  </div>
</div>
</body></html>"""

STATS_CARD_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1200px; height: 675px; display: flex; align-items: center; justify-content: center;
       background: #ffffff;
       font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
.card { width: 1080px; padding: 50px; text-align: center; }
h2 { font-size: 40px; color: #111827; font-weight: 800; margin-bottom: 40px; }
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.stat { background: #f9fafb; border: 1px solid #e5e7eb;
        border-radius: 20px; padding: 30px; }
.stat .num { font-size: 48px; font-weight: 800; }
.stat .num.blue { color: #2563eb; } .stat .num.green { color: #059669; }
.stat .num.purple { color: #7c3aed; }
.stat .lbl { font-size: 16px; color: #6b7280; margin-top: 8px; }
.footer { margin-top: 40px; }
.logo { font-size: 24px; font-weight: 700; color: #2563eb; }
</style></head><body>
<div class="card">
  <h2>kualia.ai by the numbers</h2>
  <div class="stats">
    <div class="stat"><div class="num blue">{{ENVS}}</div><div class="lbl">Environments Generated</div></div>
    <div class="stat"><div class="num green">{{AGENTS}}</div><div class="lbl">Agents Trained</div></div>
    <div class="stat"><div class="num purple">{{PAPERS}}</div><div class="lbl">Papers Produced</div></div>
  </div>
  <div class="footer"><span class="logo">kualia.ai</span></div>
</div>
</body></html>"""

TEMPLATE_MAP = {
    "feature_card": FEATURE_CARD_HTML,
    "training_result": TRAINING_RESULT_HTML,
    "code_snippet": CODE_SNIPPET_HTML,
    "stats_card": STATS_CARD_HTML,
}

VISUAL_TYPES = [
    "flow_diagram", "comparison", "training_curve", "architecture",
    "step_guide", "infographic", "tip_card",
]


class VisualEngine:
    """Renders HTML templates and AI-designed visuals to PNG using Playwright."""

    # ─────────────────────────────────────────────────
    # STATIC TEMPLATE RENDERING (existing)
    # ─────────────────────────────────────────────────

    async def render_template(self, template_name: str, data: Dict) -> Optional[bytes]:
        html = TEMPLATE_MAP.get(template_name)
        if not html:
            logger.error("Unknown template: %s", template_name)
            return None
        for key, value in data.items():
            html = html.replace("{{" + key.upper() + "}}", str(value))
        return await self._html_to_png(html)

    async def render_raw_html(self, html: str) -> Optional[bytes]:
        return await self._html_to_png(html)

    # ─────────────────────────────────────────────────
    # AI-DESIGNED VISUAL GENERATION (new)
    # ─────────────────────────────────────────────────

    async def design_and_render(
        self, concept: str, visual_type: str = "infographic"
    ) -> Optional[bytes]:
        """Have AI design a custom HTML visual, then render it to PNG."""
        from app.services.ai_service import ai_service

        if visual_type not in VISUAL_TYPES:
            visual_type = "infographic"

        user_prompt = (
            f"Create a {visual_type} visual for this concept:\n\n"
            f"{concept}\n\n"
            f"Visual type: {visual_type}\n"
            f"Brand: kualia.ai — AI-powered RL environment generation, agent training, and research platform.\n"
            f"Output a single complete HTML document. Start with <!DOCTYPE html>."
        )

        try:
            raw_html = await ai_service._call_ai(
                VISUAL_DESIGNER_PROMPT, user_prompt, max_tokens=4000
            )
        except Exception as e:
            logger.error("AI visual design failed: %s", e)
            return await self._fallback_visual(concept)

        html = self._extract_html(raw_html)
        if not html:
            logger.warning("AI returned non-HTML response, using fallback")
            return await self._fallback_visual(concept)

        png = await self._html_to_png(html)
        if not png:
            logger.warning("AI-designed HTML failed to render, using fallback")
            return await self._fallback_visual(concept)

        logger.info("AI visual rendered: %s / %d bytes", visual_type, len(png))
        return png

    async def _fallback_visual(self, concept: str) -> Optional[bytes]:
        """Generate a simple feature card as fallback when AI design fails."""
        words = concept.split()
        title = " ".join(words[:8]) if len(words) > 8 else concept
        desc = concept if len(words) > 8 else ""
        return await self.render_template("feature_card", {
            "badge": "kualia.ai",
            "title": title,
            "description": desc,
        })

    def _extract_html(self, raw: str) -> Optional[str]:
        """Extract HTML from LLM response, stripping markdown fences if present."""
        if not raw:
            return None
        text = raw.strip()
        fence_match = re.search(r"```(?:html)?\s*\n(.*?)```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()
        if text.startswith("<!DOCTYPE") or text.startswith("<html"):
            return text
        doc_match = re.search(r"(<!DOCTYPE html.*)", text, re.DOTALL | re.IGNORECASE)
        if doc_match:
            return doc_match.group(1)
        return None

    # ─────────────────────────────────────────────────
    # SITE SCREENSHOTS (new)
    # ─────────────────────────────────────────────────

    async def screenshot_page(
        self, path: str = "/", selector: Optional[str] = None, width: int = 1200, height: int = 675
    ) -> Optional[bytes]:
        """Navigate to a kualia.ai page and capture a screenshot."""
        url = f"{SCREENSHOT_BASE_URL}{path}"
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright not installed")
            return None

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
                page = await browser.new_page(viewport={"width": width, "height": height})
                await page.goto(url, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(1000)

                if selector:
                    element = await page.query_selector(selector)
                    if element:
                        png_bytes = await element.screenshot(type="png")
                    else:
                        png_bytes = await page.screenshot(type="png")
                else:
                    png_bytes = await page.screenshot(type="png")

                await browser.close()
                logger.info("Screenshot captured: %s (%d bytes)", url, len(png_bytes))
                return png_bytes
        except Exception as e:
            logger.error("Screenshot failed for %s: %s", url, e)
            return None

    # ─────────────────────────────────────────────────
    # COMBINED: auto-generate visual for a tweet
    # ─────────────────────────────────────────────────

    async def generate_tweet_visual(
        self, visual_type: str, visual_concept: str
    ) -> Optional[bytes]:
        """High-level method used by the scheduler to produce a visual for a tweet.
        Routes to AI designer or screenshot depending on visual_type."""
        if visual_type == "screenshot":
            path = visual_concept if visual_concept.startswith("/") else "/"
            return await self.screenshot_page(path)

        return await self.design_and_render(visual_concept, visual_type)

    async def save_visual(self, png_bytes: bytes, prefix: str = "ai_visual") -> str:
        """Save PNG bytes to the marketing_visuals directory. Returns file path."""
        output_dir = os.path.join(os.getenv("DATA_DIR", "./data"), "marketing_visuals")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "wb") as f:
            f.write(png_bytes)
        return filepath

    # ─────────────────────────────────────────────────
    # PLAYWRIGHT CORE
    # ─────────────────────────────────────────────────

    async def _html_to_png(self, html: str) -> Optional[bytes]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright not installed")
            return None

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
                page = await browser.new_page(viewport={"width": 1200, "height": 675})
                await page.set_content(html, wait_until="networkidle")
                png_bytes = await page.screenshot(type="png")
                await browser.close()
                return png_bytes
        except Exception as e:
            logger.error("Playwright render failed: %s", e)
            return None

    # ─────────────────────────────────────────────────
    # CONVENIENCE METHODS (existing, kept)
    # ─────────────────────────────────────────────────

    async def generate_feature_card(self, badge: str, title: str, description: str) -> Optional[bytes]:
        return await self.render_template("feature_card", {
            "badge": badge, "title": title, "description": description,
        })

    async def generate_training_result_card(
        self, env_name: str, domain: str, algorithm: str, steps: str,
        mean_reward: str, success_rate: str, episodes: str, train_time: str,
    ) -> Optional[bytes]:
        return await self.render_template("training_result", {
            "env_name": env_name, "domain": domain, "algorithm": algorithm,
            "steps": steps, "mean_reward": mean_reward, "success_rate": success_rate,
            "episodes": episodes, "train_time": train_time,
        })

    async def generate_stats_card(self, envs: int, agents: int, papers: int) -> Optional[bytes]:
        return await self.render_template("stats_card", {
            "envs": str(envs), "agents": str(agents), "papers": str(papers),
        })

    async def generate_code_card(self, filename: str, code: str) -> Optional[bytes]:
        code_escaped = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return await self.render_template("code_snippet", {
            "filename": filename, "code": code_escaped,
        })


visual_engine = VisualEngine()
