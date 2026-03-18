from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import requests

from rlforge.remote_env import RemoteEnv


class RLForgeError(Exception):
    """Base exception for RLForge SDK errors."""

    def __init__(self, message: str, status_code: int | None = None, detail: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class RLForgeClient:
    """HTTP client that wraps all RLForge API calls."""

    def __init__(self, api_url: str = "https://rlforge.ai", api_key: str | None = None):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        if self.api_key:
            self._session.headers["X-API-Key"] = self.api_key

    # ── HTTP helpers ──────────────────────────────────────

    def _url(self, path: str) -> str:
        return f"{self.api_url}/api/rlforge{path}"

    def _handle_response(self, resp: requests.Response) -> Any:
        if resp.status_code >= 400:
            try:
                body = resp.json()
                detail = body.get("detail", resp.text)
            except (ValueError, KeyError):
                detail = resp.text
            raise RLForgeError(
                f"API error {resp.status_code}: {detail}",
                status_code=resp.status_code,
                detail=detail,
            )
        return resp.json()

    def _get(self, path: str, params: dict | None = None) -> Any:
        resp = self._session.get(self._url(path), params=params)
        return self._handle_response(resp)

    def _post(self, path: str, data: dict | None = None) -> Any:
        resp = self._session.post(self._url(path), json=data or {})
        return self._handle_response(resp)

    def _delete(self, path: str) -> Any:
        resp = self._session.delete(self._url(path))
        return self._handle_response(resp)

    # ── Catalog ───────────────────────────────────────────

    def list_envs(
        self,
        domain: str | None = None,
        difficulty: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List published environments from the catalog.

        Returns a dict with ``items`` (list of env dicts) and ``total`` count.
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if domain:
            params["domain"] = domain
        if difficulty:
            params["difficulty"] = difficulty
        if search:
            params["search"] = search
        return self._get("/catalog", params=params)

    def get_env(self, slug_or_id: Union[str, int]) -> Dict[str, Any]:
        """Get full environment details by slug or numeric id."""
        if isinstance(slug_or_id, int) or str(slug_or_id).isdigit():
            return self._get(f"/envs/{slug_or_id}")
        return self._get(f"/catalog/{slug_or_id}")

    # ── Generate ──────────────────────────────────────────

    def generate(
        self,
        description: str,
        domain: str | None = None,
        difficulty: str = "medium",
    ) -> Dict[str, Any]:
        """Generate a new environment from a natural language description.

        Returns a dict with ``id``, ``slug``, ``name``, ``test_results``,
        and ``generation_log``.
        """
        payload: Dict[str, Any] = {
            "description": description,
            "difficulty": difficulty,
        }
        if domain:
            payload["domain"] = domain
        return self._post("/generate", data=payload)

    # ── Sessions (remote step) ────────────────────────────

    def make(self, env_slug_or_id: Union[str, int], **kwargs) -> RemoteEnv:
        """Create a remote env session and return a Gymnasium-compatible wrapper.

        Accepts the same ``api_key`` kwarg to override the client-level key for
        this session only.
        """
        if "api_key" in kwargs and kwargs["api_key"]:
            self._session.headers["X-API-Key"] = kwargs.pop("api_key")

        env_info = self.get_env(env_slug_or_id)
        env_id = env_info["id"]

        session_resp = self._post("/sessions", data={"env_id": env_id})
        session_id = session_resp["session_id"]

        return RemoteEnv(client=self, session_id=session_id, env_info=env_info)

    # ── Session primitives (used by RemoteEnv) ────────────

    def session_step(self, session_id: str, action: Any) -> Dict[str, Any]:
        return self._post(f"/sessions/{session_id}/step", data={"action": action})

    def session_reset(self, session_id: str, seed: int | None = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if seed is not None:
            payload["seed"] = seed
        return self._post(f"/sessions/{session_id}/reset", data=payload)

    def session_close(self, session_id: str) -> None:
        self._delete(f"/sessions/{session_id}")

    # ── Utility ───────────────────────────────────────────

    def __repr__(self) -> str:
        masked = f"{self.api_key[:4]}...{self.api_key[-4:]}" if self.api_key and len(self.api_key) > 8 else "***"
        return f"RLForgeClient(api_url={self.api_url!r}, api_key={masked!r})"
