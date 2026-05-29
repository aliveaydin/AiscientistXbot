"""
Email Service — sends transactional and marketing emails via Resend.
"""
import logging
import resend
from typing import Optional, Dict, Any
from datetime import datetime

from app.config import settings

logger = logging.getLogger("email_service")

APP_URL = settings.app_url.rstrip("/")

# kualia.ai logo as inline SVG (works in most email clients)
LOGO_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="810 440 780 780" style="vertical-align:middle;">
<g transform="translate(0,1617) scale(0.1,-0.1)" fill="#111827" stroke="none">
<path d="M12947 10725 c91 -48 143 -130 143 -224 0 -121 -55 -205 -167 -255 -35 -15 -55 -18 -110 -12 -38 4 -69 11 -71 16 -2 6 -11 10 -21 10 -9 0 -22 5 -28 11 -12 12 -106 -81 -805 -794 -234 -238 -284 -294 -273 -303 8 -6 15 -25 15 -42 0 -17 5 -34 10 -37 6 -3 10 -19 10 -36 0 -16 -4 -29 -10 -29 -5 0 -10 -11 -10 -24 0 -35 -66 -116 -101 -123 -16 -3 -32 -10 -35 -14 -7 -12 -101 -11 -109 1 -17 28 -54 7 -128 -72 -41 -46 -119 -128 -171 -182 -53 -55 -96 -105 -96 -111 0 -7 19 -30 43 -52 57 -54 501 -512 524 -541 15 -19 24 -22 46 -17 15 4 27 11 27 16 0 12 117 11 125 -1 3 -5 14 -10 24 -10 23 0 101 -86 101 -110 0 -11 5 -22 10 -25 15 -9 12 -101 -5 -142 l-15 -35 153 -155 c83 -85 206 -209 271 -276 66 -67 220 -224 343 -348 l223 -226 52 18 c29 10 74 18 100 19 94 0 216 -79 233 -152 4 -15 11 -30 16 -33 5 -4 9 -33 9 -65 0 -161 -109 -270 -269 -270 -39 0 -73 5 -76 10 -3 6 -15 10 -26 10 -38 0 -117 95 -143 173 -5 16 -37 17 -476 17 l-471 0 -16 -37 c-8 -21 -18 -40 -22 -43 -3 -3 -12 -17 -20 -33 -8 -15 -37 -42 -65 -59 -45 -29 -59 -32 -126 -33 -84 0 -144 22 -193 71 -40 40 -77 127 -77 181 0 37 30 136 43 141 20 9 -7 43 -175 214 -101 102 -318 324 -483 493 l-301 306 -29 -15 c-48 -25 -154 -21 -209 8 -75 40 -136 115 -136 168 0 17 -11 18 -170 18 l-170 0 -6 -40 c-4 -21 -15 -47 -25 -56 -11 -9 -19 -22 -19 -27 0 -23 -87 -81 -135 -89 -19 -3 -20 -12 -20 -427 l-1 -423 26 -9 c114 -41 180 -134 180 -253 0 -103 -39 -174 -126 -229 -72 -45 -188 -45 -264 2 -75 45 -129 139 -130 226 0 104 81 218 174 246 l46 13 -2 425 -3 425 -35 11 c-60 18 -120 58 -120 82 0 6 -6 16 -14 20 -15 9 -31 57 -41 120 -17 107 77 240 188 267 l27 6 -2 448 -3 447 -25 4 c-14 1 -27 6 -30 10 -3 3 -21 15 -40 25 -65 33 -110 123 -110 217 0 124 64 215 178 254 20 7 37 18 36 24 -1 6 -2 189 -2 406 -2 355 -4 395 -18 395 -20 0 -84 30 -102 47 -7 7 -21 18 -30 25 -21 16 -42 52 -42 72 0 8 -5 16 -11 18 -7 2 -12 34 -13 83 -1 95 22 153 84 209 53 47 70 55 139 62 84 9 152 -15 210 -72 96 -96 107 -199 36 -334 -17 -33 -101 -97 -136 -104 l-29 -5 0 -408 0 -408 40 -13 c48 -14 113 -59 128 -87 42 -78 52 -111 52 -169 0 -112 -71 -210 -179 -246 l-41 -13 0 -442 0 -443 28 -5 c20 -5 31 -1 42 14 16 21 134 170 166 208 10 13 73 87 140 165 66 77 128 150 137 161 89 110 238 287 264 315 31 34 32 34 15 65 -9 16 -21 33 -26 36 -15 12 -12 153 4 185 22 45 98 114 125 114 13 0 27 5 30 10 9 15 56 12 105 -5 52 -18 65 -19 82 -1 7 7 240 244 518 526 278 282 511 520 519 528 12 11 12 18 3 33 -7 10 -12 30 -12 43 0 14 -4 28 -10 31 -19 12 -11 122 12 173 24 52 88 122 112 122 9 0 16 5 16 10 0 6 13 10 29 10 17 0 33 5 36 10 3 6 19 10 34 10 35 0 151 -39 151 -51 0 -5 5 -9 10 -9 24 0 80 -78 90 -125 l6 -30 248 0 247 0 18 51 c23 69 56 107 121 143 75 40 167 43 237 6z"/>
</g></svg>'''

# ─── Base template wrapper ───

def _wrap_html(body_html: str, unsubscribe_url: str = "") -> str:
    unsub = ""
    if unsubscribe_url:
        unsub = f'''
        <tr><td style="padding:24px 40px 20px;text-align:center;border-top:1px solid #e5e7eb;">
          <a href="{unsubscribe_url}" style="color:#9ca3af;font-size:11px;text-decoration:underline;">Unsubscribe from marketing emails</a>
        </td></tr>'''

    return f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f5;padding:40px 20px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
  <!-- Header with logo -->
  <tr><td style="padding:32px 40px 24px;background:linear-gradient(135deg,#111827 0%,#1f2937 100%);">
    <table cellpadding="0" cellspacing="0"><tr>
      <td style="padding-right:12px;">{LOGO_SVG.replace('fill="#111827"', 'fill="#ffffff"')}</td>
      <td><span style="font-size:22px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;">kualia</span><span style="font-size:13px;color:rgba(255,255,255,0.5);">.ai</span></td>
    </tr></table>
  </td></tr>
  <!-- Body -->
  <tr><td style="padding:32px 40px 24px;">
    {body_html}
  </td></tr>
  <!-- Footer -->
  <tr><td style="padding:20px 40px 28px;border-top:1px solid #f3f4f6;text-align:center;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td style="text-align:center;">
        <p style="margin:0 0 6px;font-size:11px;color:#9ca3af;">kualia.ai — Generate RL Environments. Train Agents. Create Papers.</p>
        <p style="margin:0;font-size:11px;color:#d1d5db;">
          <a href="{APP_URL}" style="color:#6b7280;text-decoration:none;">Website</a>
          &nbsp;·&nbsp;
          <a href="{APP_URL}/dashboard" style="color:#6b7280;text-decoration:none;">Dashboard</a>
          &nbsp;·&nbsp;
          <a href="{APP_URL}/docs" style="color:#6b7280;text-decoration:none;">Docs</a>
        </p>
      </td>
    </tr></table>
  </td></tr>
  {unsub}
</table>
</td></tr></table>
</body></html>'''


def _btn(text: str, url: str, color: str = "#111827") -> str:
    return f'<a href="{url}" style="display:inline-block;padding:13px 30px;background-color:{color};color:#ffffff;text-decoration:none;border-radius:8px;font-size:14px;font-weight:600;letter-spacing:-0.2px;">{text}</a>'


def _badge(text: str, bg: str = "#f3f4f6", color: str = "#374151") -> str:
    return f'<span style="display:inline-block;padding:4px 10px;background:{bg};color:{color};border-radius:6px;font-size:12px;font-weight:600;">{text}</span>'


def _stat_row(label: str, value: str, accent: str = "#059669") -> str:
    return f'<tr><td style="padding:6px 0;font-size:13px;color:#6b7280;">{label}</td><td style="text-align:right;font-weight:700;font-size:13px;color:{accent};">{value}</td></tr>'


# ─── Templates ───

TEMPLATES: Dict[str, Any] = {}


def _register_templates():
    # ── Transactional Templates ──

    TEMPLATES["welcome"] = lambda d: (
        "Welcome to kualia.ai — your $5 credit is ready",
        _wrap_html(f'''
        <h1 style="margin:0 0 8px;font-size:26px;font-weight:800;color:#111827;letter-spacing:-0.5px;">Welcome to kualia.ai</h1>
        <p style="margin:0 0 20px;font-size:14px;color:#6b7280;">Your AI-powered reinforcement learning platform is ready.</p>
        <div style="background:linear-gradient(135deg,#f0fdf4 0%,#ecfdf5 100%);border:1px solid #bbf7d0;border-radius:10px;padding:20px;margin:0 0 24px;">
            <p style="margin:0 0 4px;font-size:13px;color:#059669;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Your Welcome Credit</p>
            <p style="margin:0;font-size:32px;font-weight:800;color:#047857;">$5.00</p>
            <p style="margin:4px 0 0;font-size:13px;color:#6b7280;">Enough to generate environments, train agents, and start a research paper.</p>
        </div>
        <p style="margin:0 0 6px;font-size:14px;color:#374151;line-height:1.7;font-weight:600;">Here's what you can do:</p>
        <table style="margin:0 0 24px;font-size:13px;color:#4b5563;line-height:1.6;">
            <tr><td style="padding:4px 10px 4px 0;vertical-align:top;">→</td><td>Describe an environment in plain English and get validated Gymnasium code</td></tr>
            <tr><td style="padding:4px 10px 4px 0;vertical-align:top;">→</td><td>Train agents with PPO, SAC, A2C and get performance reports</td></tr>
            <tr><td style="padding:4px 10px 4px 0;vertical-align:top;">→</td><td>Run full research pipelines and generate academic papers</td></tr>
        </table>
        <p style="margin:0 0 8px;">{_btn("Create Your First Environment", APP_URL + "/dashboard")}</p>
        ''')
    )

    TEMPLATES["env_ready"] = lambda d: (
        f"Environment ready: {d.get('env_name', 'New Environment')}",
        _wrap_html(f'''
        <p style="margin:0 0 4px;font-size:12px;color:#059669;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Environment Generated</p>
        <h1 style="margin:0 0 16px;font-size:24px;font-weight:800;color:#111827;letter-spacing:-0.3px;">{d.get('env_name', 'Your Environment')}</h1>
        <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;padding:18px;margin:0 0 20px;">
            <table width="100%" cellpadding="0" cellspacing="0">
                {_stat_row("Tests", f"{d.get('tests_passed', '?')}/{d.get('tests_total', '8')} passed")}
                {_stat_row("Domain", d.get('domain', 'general'), "#374151")}
                {_stat_row("Difficulty", d.get('difficulty', 'medium'), "#374151")}
            </table>
        </div>
        <p style="margin:0 0 12px;font-size:14px;color:#6b7280;line-height:1.6;">
            Your environment is ready. You can review the code, iterate with the AI assistant, or start training an agent right away.
        </p>
        <p style="margin:0 0 8px;">{_btn("Open in Builder", APP_URL + "/builder/" + str(d.get('env_id', '')))}</p>
        ''')
    )

    TEMPLATES["training_complete"] = lambda d: (
        f"Training complete: {d.get('env_name', 'Environment')}",
        _wrap_html(f'''
        <p style="margin:0 0 4px;font-size:12px;color:#2563eb;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Training Finished</p>
        <h1 style="margin:0 0 16px;font-size:24px;font-weight:800;color:#111827;letter-spacing:-0.3px;">{d.get('env_name', 'Your Environment')}</h1>
        <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;padding:18px;margin:0 0 20px;">
            <table width="100%" cellpadding="0" cellspacing="0">
                {_stat_row("Algorithm", d.get('algorithm', 'PPO'), "#374151")}
                {_stat_row("Total Timesteps", str(d.get('timesteps', '?')), "#374151")}
                {_stat_row("Mean Reward", str(d.get('mean_reward', 'N/A')))}
            </table>
        </div>
        <p style="margin:0 0 12px;font-size:14px;color:#6b7280;line-height:1.6;">
            View the training curves, evaluation episodes, and detailed performance report in the builder.
        </p>
        <p style="margin:0;">{_btn("View Results", APP_URL + "/builder/" + str(d.get('env_id', '')))}</p>
        ''')
    )

    TEMPLATES["paper_ready"] = lambda d: (
        f"Paper ready: {d.get('title', 'Research Paper')}",
        _wrap_html(f'''
        <p style="margin:0 0 4px;font-size:12px;color:#7c3aed;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Paper Generated</p>
        <h1 style="margin:0 0 16px;font-size:22px;font-weight:800;color:#111827;letter-spacing:-0.3px;">"{d.get('title', 'Untitled')}"</h1>
        <p style="margin:0 0 20px;font-size:14px;color:#6b7280;line-height:1.6;">
            Your research paper has been generated with inline training figures, methodology, and analysis sections. It's ready to download as PDF.
        </p>
        <p style="margin:0;">{_btn("View Paper", APP_URL + "/research/" + str(d.get('project_id', '')), "#7c3aed")}</p>
        ''')
    )

    TEMPLATES["research_complete"] = lambda d: (
        f"Research complete: {d.get('title', 'Project')}",
        _wrap_html(f'''
        <p style="margin:0 0 4px;font-size:12px;color:#7c3aed;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Research Pipeline Complete</p>
        <h1 style="margin:0 0 16px;font-size:24px;font-weight:800;color:#111827;letter-spacing:-0.3px;">{d.get('title', 'Untitled')}</h1>
        <div style="margin:0 0 20px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="font-size:13px;">
                <tr>
                    <td style="padding:8px 0;color:#059669;">✓ Hypothesis</td>
                    <td style="padding:8px 0;color:#059669;">✓ Environment</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;color:#059669;">✓ Training</td>
                    <td style="padding:8px 0;color:#059669;">✓ Paper</td>
                </tr>
            </table>
        </div>
        <p style="margin:0 0 12px;font-size:14px;color:#6b7280;line-height:1.6;">
            All phases completed. Your paper with real training results is ready to review and download.
        </p>
        <p style="margin:0;">{_btn("View Results", APP_URL + "/research/" + str(d.get('project_id', '')), "#7c3aed")}</p>
        ''')
    )

    TEMPLATES["credits_low"] = lambda d: (
        "Your kualia.ai credits are running low",
        _wrap_html(f'''
        <h1 style="margin:0 0 16px;font-size:24px;font-weight:800;color:#111827;">Credits Running Low</h1>
        <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:20px;margin:0 0 20px;text-align:center;">
            <p style="margin:0 0 4px;font-size:13px;color:#dc2626;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">Current Balance</p>
            <p style="margin:0;font-size:32px;font-weight:800;color:#b91c1c;">${d.get('balance', '0.00')}</p>
        </div>
        <p style="margin:0 0 20px;font-size:14px;color:#6b7280;line-height:1.6;">
            You may not have enough credits for your next environment generation or training run. Upgrade your plan or add credits to keep building.
        </p>
        <p style="margin:0;">{_btn("Upgrade Plan", APP_URL + "/pricing")}</p>
        ''')
    )

    # ── Marketing Templates ──

    TEMPLATES["new_feature"] = lambda d: (
        d.get("subject", "New on kualia.ai"),
        _wrap_html(f'''
        {_badge("NEW", "#dbeafe", "#1d4ed8")}
        <h1 style="margin:12px 0 8px;font-size:24px;font-weight:800;color:#111827;letter-spacing:-0.3px;">{d.get('headline', 'New Feature')}</h1>
        <div style="margin:0 0 4px;border-top:3px solid #3b82f6;padding-top:20px;"></div>
        <div style="font-size:14px;color:#4b5563;line-height:1.7;">
            {d.get('body', '')}
        </div>
        <div style="margin:28px 0 0;text-align:center;">{_btn(d.get('cta_text', 'Try It Now'), d.get('cta_url', APP_URL + '/dashboard'), '#2563eb')}</div>
        ''', d.get('unsubscribe_url', APP_URL + '/dashboard/settings'))
    )

    TEMPLATES["tips_tricks"] = lambda d: (
        d.get("subject", "RL Tip of the Week"),
        _wrap_html(f'''
        {_badge("WEEKLY RL TIP", "#fef3c7", "#92400e")}
        <h1 style="margin:12px 0 8px;font-size:22px;font-weight:800;color:#111827;letter-spacing:-0.3px;">{d.get('headline', 'RL Tip of the Week')}</h1>
        <div style="margin:0 0 4px;border-top:3px solid #f59e0b;padding-top:20px;"></div>
        <div style="font-size:14px;color:#4b5563;line-height:1.7;">
            {d.get('body', '')}
        </div>
        {"<div style='margin:28px 0 0;text-align:center;'>" + _btn(d.get('cta_text', 'Open kualia.ai'), d.get('cta_url', APP_URL + '/dashboard')) + "</div>" if d.get('cta_text') else ""}
        ''', d.get('unsubscribe_url', APP_URL + '/dashboard/settings'))
    )

    TEMPLATES["reengagement"] = lambda d: (
        d.get("subject", "We miss you at kualia.ai"),
        _wrap_html(f'''
        <h1 style="margin:0 0 8px;font-size:26px;font-weight:800;color:#111827;letter-spacing:-0.5px;">{d.get('headline', "It's been a while!")}</h1>
        <div style="margin:0 0 4px;border-top:3px solid #8b5cf6;padding-top:20px;"></div>
        <div style="font-size:14px;color:#4b5563;line-height:1.7;">
            {d.get('body', '<p style="margin:0 0 16px;">Your environments and experiments are waiting for you. Jump back in and continue where you left off.</p>')}
        </div>
        {('<div style="margin:20px 0 0;">' + d.get('extra', '') + '</div>') if d.get('extra') else ''}
        <div style="margin:28px 0 0;text-align:center;">{_btn("Back to Dashboard", APP_URL + "/dashboard", "#7c3aed")}</div>
        ''', d.get('unsubscribe_url', APP_URL + '/dashboard/settings'))
    )


_register_templates()


# ─── Service ───

class EmailService:
    def __init__(self):
        if settings.resend_api_key:
            resend.api_key = settings.resend_api_key
            logger.info("Resend API key configured")
        else:
            logger.warning("RESEND_API_KEY not set — emails will be logged but not sent")

    async def send_transactional(
        self,
        to: str,
        template: str,
        data: Dict[str, Any] = None,
        subject_override: Optional[str] = None,
        user_id: int = None,
    ) -> dict:
        data = data or {}
        tpl = TEMPLATES.get(template)
        if not tpl:
            logger.error("Unknown template: %s", template)
            return {"success": False, "error": "unknown_template"}

        subject, html = tpl(data)
        if subject_override:
            subject = subject_override

        return await self._send(
            from_addr=settings.email_from_transactional,
            to=to, subject=subject, html=html,
            channel="transactional", template=template, user_id=user_id,
        )

    async def send_marketing(
        self,
        to: str,
        template: str,
        data: Dict[str, Any] = None,
        subject_override: Optional[str] = None,
        user_id: int = None,
    ) -> dict:
        data = data or {}
        data.setdefault("unsubscribe_url", f"{APP_URL}/dashboard/settings")

        tpl = TEMPLATES.get(template)
        if not tpl:
            logger.error("Unknown marketing template: %s", template)
            return {"success": False, "error": "unknown_template"}

        subject, html = tpl(data)
        if subject_override:
            subject = subject_override

        return await self._send(
            from_addr=settings.email_from_marketing,
            to=to, subject=subject, html=html,
            channel="marketing", template=template, user_id=user_id,
        )

    async def send_raw(
        self,
        to: str,
        subject: str,
        html: str,
        channel: str = "marketing",
        user_id: int = None,
    ) -> dict:
        from_addr = settings.email_from_marketing if channel == "marketing" else settings.email_from_transactional
        return await self._send(from_addr=from_addr, to=to, subject=subject, html=_wrap_html(html), channel=channel, template="raw", user_id=user_id)

    async def _send(self, from_addr: str, to: str, subject: str, html: str, channel: str, template: str, user_id: int = None) -> dict:
        result = {"to": to, "subject": subject, "channel": channel, "template": template}

        if not settings.resend_api_key:
            logger.info("[DRY RUN] Would send '%s' to %s (template=%s)", subject, to, template)
            result["success"] = True
            result["dry_run"] = True
            await self._log(user_id=user_id, to=to, subject=subject, template=template, channel=channel, status="sent", resend_id="dry_run")
            return result

        try:
            resp = resend.Emails.send({
                "from": from_addr,
                "to": [to],
                "subject": subject,
                "html": html,
            })
            result["success"] = True
            result["resend_id"] = resp.get("id") if isinstance(resp, dict) else getattr(resp, "id", None)
            logger.info("Email sent: '%s' to %s (id=%s)", subject, to, result.get("resend_id"))
            await self._log(user_id=user_id, to=to, subject=subject, template=template, channel=channel, status="sent", resend_id=result.get("resend_id"))
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            logger.error("Email send failed: %s — %s", to, e)
            await self._log(user_id=user_id, to=to, subject=subject, template=template, channel=channel, status="failed", error=str(e))

        return result

    async def _log(self, **kwargs):
        try:
            from app.database import async_session
            from app.models import EmailLog
            if "to" in kwargs:
                kwargs["to_email"] = kwargs.pop("to")
            async with async_session() as db:
                db.add(EmailLog(**kwargs))
                await db.commit()
        except Exception as e:
            logger.warning("Failed to log email: %s", e)


email_service = EmailService()
