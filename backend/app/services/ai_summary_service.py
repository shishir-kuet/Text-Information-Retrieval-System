import json
import os
import re
import urllib.request
import urllib.error
import logging
from typing import Optional


class AiSummaryService:
    """AI summarization.

    Configuration:
    - SUMMARY_PROVIDER: auto | gemini | huggingface
    - GEMINI_API_KEY
    - GEMINI_API_BASE (default: https://generativelanguage.googleapis.com/v1beta)
    - GEMINI_MODEL
    - GEMINI_SUMMARY_PROMPT_TEMPLATE (required for Gemini)
    - HF_API_KEY
    - HF_API_BASE (default: https://router.huggingface.co/hf-inference/models)
    - HF_MODEL
    """

    DEFAULT_MAX_CHARS = 12000

    def __init__(self):
        self.summary_provider = (os.getenv("SUMMARY_PROVIDER") or "auto").strip().lower()

        self.gemini_api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        self.gemini_model = (os.getenv("GEMINI_MODEL") or "gemini-2.5-flash").strip()
        self.gemini_api_base = (
            os.getenv("GEMINI_API_BASE") or "https://generativelanguage.googleapis.com/v1beta"
        ).strip().rstrip("/")

        self.gemini_prompt_template = self._read_prompt_template(os.getenv("GEMINI_SUMMARY_PROMPT_TEMPLATE"))

        self.hf_api_key = (os.getenv("HF_API_KEY") or "").strip()
        self.hf_model = (os.getenv("HF_MODEL") or "facebook/bart-large-cnn").strip()
        self.hf_api_base = (
            os.getenv("HF_API_BASE") or "https://router.huggingface.co/hf-inference/models"
        ).strip().rstrip("/")

    def _read_prompt_template(self, raw: Optional[str]):
        template = (raw or "").strip()
        if not template:
            return None
        # Allow writing multi-line prompts in .env using \n
        return template.replace("\\n", "\n")

    def _build_prompt(self, template: Optional[str], *, provider: str, max_sentences: int, content: str):
        if not template:
            raise RuntimeError(f"{provider}_SUMMARY_PROMPT_TEMPLATE is required")

        # Avoid str.format() to prevent accidental formatting errors.
        prompt = template
        prompt = prompt.replace("{max_sentences}", str(max_sentences))
        prompt = prompt.replace("{content}", content)
        prompt = prompt.replace("{text}", content)
        return prompt

    def _gemini_configured(self):
        return bool(self.gemini_api_key and self.gemini_prompt_template)

    def _hf_configured(self):
        return bool(self.hf_api_key and self.hf_model)

    def is_configured(self):
        provider = self.summary_provider
        if provider == "gemini":
            return self._gemini_configured()
        if provider in {"huggingface", "hf"}:
            return self._hf_configured()
        return self._gemini_configured() or self._hf_configured()

    def split_sentences(self, text: str):
        cleaned = re.sub(r"\s+", " ", (text or "").strip())
        if not cleaned:
            return []
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]

    def _truncate(self, text: str, max_chars: int):
        text = (text or "").strip()
        if not text:
            return ""
        if max_chars <= 0:
            max_chars = self.DEFAULT_MAX_CHARS
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rstrip() + "\n\n[...truncated...]"

    def _postprocess(self, text: str, max_sentences: int):
        cleaned = re.sub(r"\s+", " ", (text or "").strip())
        if not cleaned:
            return ""
        if max_sentences < 1:
            max_sentences = 1
        if max_sentences > 8:
            max_sentences = 8

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
        if len(sentences) <= max_sentences:
            return cleaned
        return " ".join(sentences[:max_sentences]).strip()

    def _extractive_fallback_summary(self, text: str, max_sentences: int):
        # Deterministic local fallback so summary endpoint still works when external APIs fail.
        cleaned = re.sub(r"\s+", " ", (text or "").strip())
        if not cleaned:
            return ""
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
        if not sentences:
            return cleaned[:500].strip()
        max_sentences = max(1, min(max_sentences, 8))
        return " ".join(sentences[:max_sentences]).strip()

    def summarize(self, text: str, max_sentences: int = 3, max_chars: Optional[int] = None):
        if max_chars is None:
            max_chars = self.DEFAULT_MAX_CHARS

        source = self._truncate(text, max_chars)
        if not source:
            return {"summary": "", "provider": None}

        provider = self.summary_provider
        if provider == "gemini":
            if not self._gemini_configured():
                return {"summary": "", "provider": None}
            try:
                summary = self._summarize_gemini(source, max_sentences=max_sentences)
                return {"summary": self._postprocess(summary, max_sentences), "provider": "gemini"}
            except Exception as exc:
                logging.error("Gemini failed, using extractive fallback: %s", exc)
                summary = self._extractive_fallback_summary(source, max_sentences)
                return {"summary": summary, "provider": "extractive"}

        if provider in {"huggingface", "hf"}:
            if not self._hf_configured():
                return {"summary": "", "provider": None}
            try:
                summary = self._summarize_hf(source)
                return {"summary": self._postprocess(summary, max_sentences), "provider": "huggingface"}
            except Exception as exc:
                logging.error("Hugging Face failed, using extractive fallback: %s", exc)
                summary = self._extractive_fallback_summary(source, max_sentences)
                return {"summary": summary, "provider": "extractive"}

        if self._gemini_configured():
            try:
                summary = self._summarize_gemini(source, max_sentences=max_sentences)
                return {"summary": self._postprocess(summary, max_sentences), "provider": "gemini"}
            except Exception:
                pass

        if self._hf_configured():
            try:
                summary = self._summarize_hf(source)
                return {"summary": self._postprocess(summary, max_sentences), "provider": "huggingface"}
            except Exception:
                pass

        summary = self._extractive_fallback_summary(source, max_sentences)
        return {"summary": summary, "provider": "extractive"}

        return {"summary": "", "provider": None}

    def _summarize_gemini(self, text: str, max_sentences: int):
        url = (
            f"{self.gemini_api_base}/models/"
            f"{self.gemini_model}:generateContent?key={self.gemini_api_key}"
        )
        prompt = self._build_prompt(
            self.gemini_prompt_template,
            provider="GEMINI",
            max_sentences=max_sentences,
            content=text,
        )

        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            logging.error("Gemini summary failed: %s %s", exc.code, detail)
            detail = detail.strip()
            detail_snippet = detail[:400] + ("..." if len(detail) > 400 else "")
            if detail_snippet:
                raise RuntimeError(f"Gemini summary failed: {exc.code} {detail_snippet}") from exc
            raise RuntimeError(f"Gemini summary failed: {exc.code}") from exc
        except urllib.error.URLError as exc:
            logging.error("Gemini summary failed: %s", exc.reason)
            raise RuntimeError("Gemini summary failed: network error") from exc
        except Exception as exc:
            logging.error("Gemini summary failed: %s", exc)
            raise RuntimeError("Gemini summary failed") from exc

        candidates = payload.get("candidates")
        if isinstance(candidates, list) and candidates:
            content = (candidates[0] or {}).get("content") or {}
            parts = content.get("parts")
            if isinstance(parts, list) and parts:
                text_out = (parts[0] or {}).get("text")
                if isinstance(text_out, str) and text_out.strip():
                    return text_out.strip()

        raise RuntimeError("AI summary returned empty output")

    def _summarize_hf(self, text: str):
        candidate_urls = [
            f"{self.hf_api_base}/{self.hf_model}",
            f"https://router.huggingface.co/hf-inference/models/{self.hf_model}",
            f"https://api-inference.huggingface.co/models/{self.hf_model}",
            f"https://api-inference.huggingface.co/pipeline/summarization/{self.hf_model}",
        ]
        # Preserve order while removing duplicates.
        urls = list(dict.fromkeys(candidate_urls))

        body = {
            "inputs": text,
            "parameters": {
                "do_sample": False,
            },
        }
        last_error = None
        for url in urls:
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.hf_api_key}",
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="ignore")
                logging.error("Hugging Face summary failed on %s: %s %s", url, exc.code, detail)
                # Route-not-found style errors often happen with older/base URL formats.
                # Try the next endpoint candidate before failing.
                if exc.code == 404:
                    last_error = RuntimeError(f"Hugging Face summary failed: {exc.code} {detail[:200]}")
                    continue
                detail = detail.strip()
                detail_snippet = detail[:400] + ("..." if len(detail) > 400 else "")
                if detail_snippet:
                    raise RuntimeError(f"Hugging Face summary failed: {exc.code} {detail_snippet}") from exc
                raise RuntimeError(f"Hugging Face summary failed: {exc.code}") from exc
            except urllib.error.URLError as exc:
                logging.error("Hugging Face summary failed on %s: %s", url, exc.reason)
                last_error = RuntimeError("Hugging Face summary failed: network error")
                continue
            except Exception as exc:
                logging.error("Hugging Face summary failed on %s: %s", url, exc)
                last_error = RuntimeError("Hugging Face summary failed")
                continue

            if isinstance(payload, dict):
                if payload.get("error"):
                    last_error = RuntimeError(f"Hugging Face summary failed: {payload.get('error')}")
                    continue
                summary_text = payload.get("summary_text") or payload.get("generated_text")
                if isinstance(summary_text, str) and summary_text.strip():
                    return summary_text.strip()

            if isinstance(payload, list) and payload:
                item = payload[0] or {}
                summary_text = item.get("summary_text") or item.get("generated_text")
                if isinstance(summary_text, str) and summary_text.strip():
                    return summary_text.strip()

            last_error = RuntimeError("AI summary returned empty output")

        if last_error:
            raise last_error
        raise RuntimeError("AI summary returned empty output")
