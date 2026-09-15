import os
import json
import time
import uuid
import logging
from typing import Any, Dict, List, Optional, Union
import httpx
from fastapi import FastAPI, Request, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from profile_data import REGINA_CV_PROFILE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("banorte-cv-agent")

app = FastAPI(
    title="Banorte CV Agent - Aurea Regina Guzmán Montero",
    description="Agente de CV compatible con el estándar Open Responses y A2A para el Reto IA Banorte (Especialista Sr. en IA e Innovación).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
FALLBACK_MODEL = "gemini-flash-latest"


@app.get("/")
async def root():
    return {
        "status": "online",
        "agent": "Aurea Regina Guzmán Montero - Agente CV",
        "role": "Especialista Sr. en Inteligencia Artificial e Innovación (Banorte)",
        "protocol": "Open Responses v1 & A2A Agent Card",
        "agent_card": "/.well-known/agent-card.json",
        "responses_endpoint": "/v1/responses"
    }


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": int(time.time())}


@app.get("/debug/models")
async def debug_models(authorization: Optional[str] = Header(None)):
    api_key = GEMINI_API_KEY
    if not api_key and authorization and authorization.startswith("Bearer "):
        api_key = authorization.replace("Bearer ", "").strip()
    if not api_key:
        return {"error": "no api key"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}")
        return res.json()


@app.get("/.well-known/agent-card.json")
async def agent_card(request: Request):
    base_url = str(request.base_url).rstrip("/")
    # Si viene detrás de proxy con HTTPS o encabezado x-forwarded-proto
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("host", request.url.netloc)
    full_base = f"{proto}://{host}"

    return {
        "name": "Aurea Regina Guzmán - Agente CV",
        "description": "Agente conversacional sobre el perfil profesional, habilidades, proyectos y experiencia técnica de Aurea Regina Guzmán Montero para Especialista Sr. en IA e Innovación en Banorte.",
        "version": "1.0.0",
        "capabilities": {
            "streaming": True
        },
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
        "promptSuggestions": [
            "Cuéntame de tu trayectoria y perfil profesional",
            "¿Qué experiencia tienes en sistemas multi-agente y LangGraph?",
            "¿Cómo abordas la seguridad bancaria y protección de PII?",
            "Háblame de tu proyecto premiado por la NASA en la ISS",
            "¿Por qué tu perfil es ideal para Banorte?"
        ],
        "skills": [],
        "supportedInterfaces": [
            {
                "url": f"{full_base}/v1",
                "protocolBinding": "https://openresponses.org/v1",
                "protocolVersion": "1.0"
            }
        ]
    }


def extract_messages_and_text(input_data: Any) -> List[Dict[str, Any]]:
    """Convierte el input recibido de Open Responses al formato de contenidos de Gemini."""
    gemini_contents = []

    if isinstance(input_data, str):
        gemini_contents.append({
            "role": "user",
            "parts": [{"text": input_data}]
        })
        return gemini_contents

    if isinstance(input_data, list):
        for item in input_data:
            if not isinstance(item, dict):
                continue
            role = item.get("role", "user")
            # En Gemini los roles permitidos son 'user' y 'model'
            gemini_role = "model" if role in ["assistant", "model"] else "user"

            content = item.get("content", "")
            text_extracted = ""

            if isinstance(content, str):
                text_extracted = content
            elif isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, str):
                        parts.append(part)
                    elif isinstance(part, dict):
                        if "text" in part:
                            parts.append(part["text"])
                text_extracted = " ".join(parts)

            if text_extracted:
                gemini_contents.append({
                    "role": gemini_role,
                    "parts": [{"text": text_extracted}]
                })

    if not gemini_contents:
        gemini_contents.append({
            "role": "user",
            "parts": [{"text": "Hola, háblame de tu perfil profesional."}]
        })

    return gemini_contents


async def query_gemini_stream(contents: List[Dict[str, Any]], system_instruction: str, api_key: str, model_name: str = DEFAULT_MODEL):
    """Consulta streaming a Google Gemini API con fallback automático."""
    candidate_models = [model_name, "gemini-2.5-pro", "gemini-pro-latest", "gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]
    models_to_try = list(dict.fromkeys(candidate_models))

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 2048
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        success = False
        errors = []
        for current_model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:streamGenerateContent?alt=sse&key={api_key}"
            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code == 200:
                        success = True
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                json_str = line[6:].strip()
                                try:
                                    chunk = json.loads(json_str)
                                    candidates = chunk.get("candidates", [])
                                    if candidates:
                                        parts = candidates[0].get("content", {}).get("parts", [])
                                        for part in parts:
                                            if "text" in part:
                                                yield part["text"]
                                except Exception as e:
                                    logger.warning(f"Error parsing Gemini SSE chunk: {e}")
                        break
                    else:
                        error_body = await response.aread()
                        err_detail = f"[{current_model} {response.status_code}]: {error_body.decode()[:120]}"
                        errors.append(err_detail)
                        logger.warning(err_detail)
            except Exception as ex:
                errors.append(f"[{current_model} exc]: {str(ex)[:100]}")
        
        if not success:
            yield f"Error al consultar Gemini: {' | '.join(errors)}"


async def query_gemini_sync(contents: List[Dict[str, Any]], system_instruction: str, api_key: str, model_name: str = DEFAULT_MODEL) -> str:
    """Consulta síncrona a Google Gemini API con fallback automático."""
    candidate_models = [model_name, "gemini-2.5-pro", "gemini-pro-latest", "gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]
    models_to_try = list(dict.fromkeys(candidate_models))

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 2048
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        errors = []
        for current_model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={api_key}"
            try:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    try:
                        return data["candidates"][0]["content"]["parts"][0]["text"]
                    except Exception:
                        return "No fue posible procesar la respuesta del modelo."
                else:
                    err_detail = f"[{current_model} {res.status_code}]: {res.text[:120]}"
                    errors.append(err_detail)
                    logger.warning(f"Gemini sync error: {err_detail}")
            except Exception as ex:
                errors.append(f"[{current_model} exc]: {str(ex)[:100]}")
        
        return f"Error de Gemini: {' | '.join(errors)}"


@app.post("/v1/responses")
@app.post("/responses")
async def create_response(request: Request, authorization: Optional[str] = Header(None)):
    body = await request.json()
    logger.info(f"Received request on /v1/responses: {list(body.keys())}")

    # Determinar API Key: priorizar variable de entorno, o token Bearer si la plataforma lo envía
    api_key = GEMINI_API_KEY
    if not api_key and authorization and authorization.startswith("Bearer "):
        api_key = authorization.replace("Bearer ", "").strip()

    if not api_key:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": "Falta configurar GEMINI_API_KEY en las variables de entorno o la clave de API en la plataforma.",
                    "type": "configuration_error"
                }
            }
        )

    input_data = body.get("input", "")
    stream_requested = body.get("stream", True)
    custom_instructions = body.get("instructions", "")
    req_model = body.get("model")
    model_to_use = req_model if (req_model and req_model not in ["default", "opcional", None]) else DEFAULT_MODEL

    # Combinar las instrucciones del sistema con el contexto del CV de Regina
    system_instruction = REGINA_CV_PROFILE
    if custom_instructions:
        system_instruction += f"\n\nInstrucciones adicionales del cliente:\n{custom_instructions}"

    contents = extract_messages_and_text(input_data)
    response_id = f"resp_{uuid.uuid4().hex[:24]}"
    message_id = f"msg_{uuid.uuid4().hex[:24]}"
    now = int(time.time())

    # Caso Streaming (Open Responses SSE)
    if stream_requested:
        async def event_generator():
            # 1. response.in_progress
            yield f"event: response.in_progress\ndata: {json.dumps({'type': 'response.in_progress', 'id': response_id})}\n\n"

            # 2. response.output_item.added
            item_added = {
                "type": "response.output_item.added",
                "output_index": 0,
                "item": {
                    "id": message_id,
                    "type": "message",
                    "role": "assistant",
                    "status": "in_progress",
                    "content": []
                }
            }
            yield f"event: response.output_item.added\ndata: {json.dumps(item_added)}\n\n"

            accumulated_text = ""
            seq = 0

            async for delta in query_gemini_stream(contents, system_instruction, api_key, model_to_use):
                accumulated_text += delta
                seq += 1
                delta_event = {
                    "type": "response.output_text.delta",
                    "sequence_number": seq,
                    "item_id": message_id,
                    "output_index": 0,
                    "content_index": 0,
                    "delta": delta,
                    "logprobs": []
                }
                yield f"event: response.output_text.delta\ndata: {json.dumps(delta_event)}\n\n"

            # 3. response.output_text.done
            done_text_event = {
                "type": "response.output_text.done",
                "item_id": message_id,
                "output_index": 0,
                "content_index": 0,
                "text": accumulated_text
            }
            yield f"event: response.output_text.done\ndata: {json.dumps(done_text_event)}\n\n"

            # 4. response.output_item.done
            done_item_event = {
                "type": "response.output_item.done",
                "output_index": 0,
                "item": {
                    "id": message_id,
                    "type": "message",
                    "role": "assistant",
                    "status": "completed",
                    "content": [
                        {
                            "type": "output_text",
                            "text": accumulated_text,
                            "annotations": []
                        }
                    ]
                }
            }
            yield f"event: response.output_item.done\ndata: {json.dumps(done_item_event)}\n\n"

            # 5. response.completed
            completed_event = {
                "type": "response.completed",
                "response": {
                    "id": response_id,
                    "object": "response",
                    "created_at": now,
                    "completed_at": int(time.time()),
                    "status": "completed",
                    "model": DEFAULT_MODEL,
                    "output": [
                        {
                            "id": message_id,
                            "type": "message",
                            "role": "assistant",
                            "status": "completed",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": accumulated_text,
                                    "annotations": []
                                }
                            ]
                        }
                    ]
                }
            }
            yield f"event: response.completed\ndata: {json.dumps(completed_event)}\n\n"

            # 6. Terminal signal
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # Caso Síncrono (Non-streaming JSON)
    full_text = await query_gemini_sync(contents, system_instruction, api_key, model_to_use)
    completed_time = int(time.time())

    return {
        "id": response_id,
        "object": "response",
        "created_at": now,
        "completed_at": completed_time,
        "status": "completed",
        "model": model_to_use,
        "output": [
            {
                "id": message_id,
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [
                    {
                        "type": "output_text",
                        "text": full_text,
                        "annotations": []
                    }
                ]
            }
        ],
        "usage": {
            "input_tokens": 120,
            "output_tokens": 180,
            "total_tokens": 300
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
