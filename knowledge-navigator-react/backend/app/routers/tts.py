"""TTS 文字转语音（/api/tts）：基于 Microsoft Edge TTS。"""

from __future__ import annotations

import time
from io import BytesIO
from typing import Any

import edge_tts
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/tts", tags=["tts"])

# 音色列表缓存（首次请求后有效期 1 小时）
_voices_cache: list[dict[str, Any]] | None = None
_voices_cache_time: float = 0


async def _get_voices() -> list[dict[str, Any]]:
    global _voices_cache, _voices_cache_time
    now = time.time()
    if _voices_cache and now - _voices_cache_time < 3600:
        return _voices_cache
    voices = await edge_tts.list_voices()
    result = [
        {
            "name": v["ShortName"],
            "friendly_name": v.get("FriendlyName", v["ShortName"]),
            "locale": v["Locale"],
            "gender": v.get("Gender", "Unknown"),
        }
        for v in voices
        if v["Locale"].startswith("zh")
    ]
    _voices_cache = result
    _voices_cache_time = now
    return result


@router.get("/voices")
async def list_voices() -> dict[str, Any]:
    """返回所有中文音色列表。"""
    return {"voices": await _get_voices()}


class SpeakBody(BaseModel):
    text: str
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"


@router.post("/speak")
async def speak(body: SpeakBody) -> StreamingResponse:
    """将文本转为语音，返回 MP3 音频流。"""
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="文本不能为空")
    if len(text) > 5000:
        raise HTTPException(status_code=400, detail="文本过长（最多 5000 字）")

    try:
        communicate = edge_tts.Communicate(
            text, body.voice, rate=body.rate, pitch=body.pitch
        )
        buf = BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 合成失败: {e}")
