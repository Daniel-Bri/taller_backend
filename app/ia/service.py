from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings

_OPENAI_TRANSCRIBE_URL = "https://api.openai.com/v1/audio/transcriptions"
_OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
_VISION_URL = "https://vision.googleapis.com/v1/images:annotate"


def map_labels_to_categoria(labels: list[str]) -> str:
    pool = {x.lower() for x in labels}
    if {"tire", "wheel", "flat tire", "rim"} & pool:
        return "llanta"
    if {"car battery", "battery", "jumper cable"} & pool:
        return "bateria"
    if {"crash", "collision", "damaged", "wreck"} & pool:
        return "choque"
    if {"engine", "hood", "motor vehicle"} & pool:
        return "motor"
    return "otros"


async def transcribir_audio(file_path: Path) -> dict[str, Any]:
    if not settings.IA_ENABLED or not settings.OPENAI_API_KEY:
        return {"ok": False, "text": None, "reason": "IA deshabilitada o sin API key"}

    try:
        async with httpx.AsyncClient(timeout=40) as client:
            with file_path.open("rb") as f:
                files = {"file": (file_path.name, f, "audio/mpeg")}
                data = {"model": "gpt-4o-mini-transcribe", "language": "es"}
                res = await client.post(
                    _OPENAI_TRANSCRIBE_URL,
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    files=files,
                    data=data,
                )
        if res.status_code >= 400:
            return {"ok": False, "text": None, "reason": f"Whisper HTTP {res.status_code}"}
        body = res.json()
        return {"ok": True, "text": (body.get("text") or "").strip() or None}
    except Exception as e:
        return {"ok": False, "text": None, "reason": str(e)}


async def resumir_incidente(texto_usuario: str | None, transcripcion: str | None, categoria: str | None) -> dict[str, Any]:
    if not settings.IA_ENABLED or not settings.OPENAI_API_KEY:
        # Fallback simple y defendible para demo
        base = (texto_usuario or "").strip() or (transcripcion or "").strip() or "Sin descripción"
        return {
            "ok": True,
            "resumen": f"Categoria sugerida: {categoria or 'otros'}. Resumen: {base[:220]}",
            "confianza": 0.55,
        }

    prompt = (
        "Eres un asistente de emergencias vehiculares. "
        "Devuelve JSON con campos: resumen, confianza (0-1), categoria_sugerida.\n"
        f"texto_usuario={texto_usuario!r}\n"
        f"transcripcion_audio={transcripcion!r}\n"
        f"categoria_actual={categoria!r}\n"
    )
    try:
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Responde solo JSON válido."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                _OPENAI_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if res.status_code >= 400:
            return {"ok": False, "resumen": None, "confianza": None}
        raw = res.json()["choices"][0]["message"]["content"]
        data = json.loads(raw)
        return {
            "ok": True,
            "resumen": data.get("resumen"),
            "confianza": data.get("confianza"),
            "categoria": data.get("categoria_sugerida"),
        }
    except Exception:
        return {"ok": False, "resumen": None, "confianza": None}


async def clasificar_imagen(file_path: Path) -> dict[str, Any]:
    if not settings.IA_ENABLED or not settings.GOOGLE_VISION_API_KEY:
        return {"ok": False, "labels": [], "categoria": None}
    try:
        b64 = base64.b64encode(file_path.read_bytes()).decode("utf-8")
        req = {
            "requests": [
                {
                    "image": {"content": b64},
                    "features": [{"type": "LABEL_DETECTION", "maxResults": 8}],
                }
            ]
        }
        url = f"{_VISION_URL}?key={settings.GOOGLE_VISION_API_KEY}"
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(url, json=req)
        if res.status_code >= 400:
            return {"ok": False, "labels": [], "categoria": None}
        labels = [
            x.get("description", "")
            for x in (((res.json().get("responses") or [{}])[0].get("labelAnnotations") or []))
            if x.get("description")
        ]
        categoria = map_labels_to_categoria(labels)
        return {"ok": True, "labels": labels, "categoria": categoria}
    except Exception:
        return {"ok": False, "labels": [], "categoria": None}
