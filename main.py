import os
import json
import time
import uuid
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
import httpx
from fastapi import FastAPI, Request, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from profile_data import REGINA_CV_PROFILE
from cv_knowledge import get_deterministic_cv_response, GUARDRAIL_DEFLECTION

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
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
FALLBACK_MODEL = "gemini-3.5-flash"


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


def extract_messages_and_text(input_data: Any) -> tuple[List[Dict[str, Any]], str]:
    """Convierte el input recibido de Open Responses al formato de contenidos de Gemini y extrae la consulta."""
    gemini_contents = []
    last_user_query = ""

    if isinstance(input_data, str):
        last_user_query = input_data
        gemini_contents.append({
            "role": "user",
            "parts": [{"text": input_data}]
        })
        return gemini_contents, last_user_query

    if isinstance(input_data, list):
        for item in input_data:
            if not isinstance(item, dict):
                continue
            role = item.get("role", "user")
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
                    elif isinstance(part, dict) and "text" in part:
                        parts.append(part["text"])
                text_extracted = " ".join(parts)

            if text_extracted:
                if gemini_role == "user":
                    last_user_query = text_extracted
                gemini_contents.append({
                    "role": gemini_role,
                    "parts": [{"text": text_extracted}]
                })

    if not gemini_contents:
        last_user_query = "Hola, háblame de tu perfil profesional."
        gemini_contents.append({
            "role": "user",
            "parts": [{"text": last_user_query}]
        })

    return gemini_contents, last_user_query


async def query_gemini_stream(contents: List[Dict[str, Any]], system_instruction: str, api_key: str, model_name: str = DEFAULT_MODEL, user_query: str = ""):
    """Consulta streaming a Google Gemini API con reintentos y fallback determinista."""
    # 1. Guardrail instantáneo para temas fuera de dominio (ej. recetas, pay de limón)
    q_lower = user_query.lower()
    if any(w in q_lower for w in ["receta", "pay", "limon", "limón", "cocina", "comida", "pastel", "chiste", "poema", "horoscopo"]):
        words = GUARDRAIL_DEFLECTION.split(" ")
        for i in range(0, len(words), 3):
            yield " ".join(words[i:i+3]) + " "
            await asyncio.sleep(0.04)
        return

    candidate_models = [model_name, "gemini-3.1-flash-lite", "gemini-3.5-flash"]
    models_to_try = list(dict.fromkeys(candidate_models))

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024
        }
    }

    success = False
    async with httpx.AsyncClient(timeout=20.0) as client:
        for current_model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:streamGenerateContent?alt=sse&key={api_key}"
            for attempt in range(2):
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
                        elif response.status_code in [503, 429] and attempt == 0:
                            logger.warning(f"Retrying {current_model} after status {response.status_code}...")
                            await asyncio.sleep(1.0)
                            continue
                        else:
                            break
                except Exception:
                    if attempt == 0:
                        await asyncio.sleep(0.5)
                        continue
                    break
            if success:
                break
        
    # Fallback determinista seguro ante saturación del proveedor
    if not success:
        logger.info(f"Activating deterministic fallback for query: '{user_query[:50]}'")
        fallback_text = get_deterministic_cv_response(user_query)
        words = fallback_text.split(" ")
        for i in range(0, len(words), 3):
            yield " ".join(words[i:i+3]) + " "
            await asyncio.sleep(0.03)


async def query_gemini_sync(contents: List[Dict[str, Any]], system_instruction: str, api_key: str, model_name: str = DEFAULT_MODEL, user_query: str = "") -> str:
    """Consulta síncrona a Google Gemini API con reintentos y fallback determinista."""
    q_lower = user_query.lower()
    if any(w in q_lower for w in ["receta", "pay", "limon", "limón", "cocina", "comida", "pastel", "chiste", "poema", "horoscopo"]):
        return GUARDRAIL_DEFLECTION

    candidate_models = [model_name, "gemini-3.1-flash-lite", "gemini-3.5-flash"]
    models_to_try = list(dict.fromkeys(candidate_models))

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024
        }
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        for current_model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={api_key}"
            for attempt in range(2):
                try:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        try:
                            return data["candidates"][0]["content"]["parts"][0]["text"]
                        except Exception:
                            pass
                    elif res.status_code in [503, 429] and attempt == 0:
                        await asyncio.sleep(1.0)
                        continue
                except Exception:
                    if attempt == 0:
                        await asyncio.sleep(0.5)
                        continue
        
        # Fallback determinista seguro
        return get_deterministic_cv_response(user_query)


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

    contents, user_query = extract_messages_and_text(input_data)
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

            async for delta in query_gemini_stream(contents, system_instruction, api_key, model_to_use, user_query):
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
    full_text = await query_gemini_sync(contents, system_instruction, api_key, model_to_use, user_query)
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
