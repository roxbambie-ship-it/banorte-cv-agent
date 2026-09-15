# 🏛️ Conversational CV Agent — Open Responses & A2A Architecture
### Reto Técnico: Especialista Sr. en Inteligencia Artificial e Innovación — Grupo Financiero Banorte
**Candidata:** Aurea Regina Guzmán Montero  
**Protocolo:** Open Responses v1 Specification & Agent-to-Agent (A2A) Discovery  
**Core Engine:** Google Gemini Foundation Models via Async REST API & SSE Streaming  

---

## 📌 1. Arquitectura del Sistema y Decisiones Técnicas

El objetivo de esta solución es implementar y operar un agente conversacional interactivo capaz de representar fielmente una trayectoria profesional en el sector financiero, cumpliendo con estándares modernos de interoperabilidad agéntica, resiliencia y baja latencia.

```
┌────────────────────────────────────────────────────────┐
│               Plataforma Cliente (A2A)                │
│             (Protocolo Open Responses)                 │
└───────────────┬────────────────────────▲───────────────┘
                │                        │
       1. Descubrimiento A2A             │ 2. POST /v1/responses
 (GET /.well-known/agent-card.json)      │    (Streaming SSE / JSON)
                │                        │
┌───────────────▼────────────────────────┴───────────────┐
│              Backend Service (FastAPI)                 │
│  - Parser de esquemas Open Responses                   │
│  - Pipeline de inyección contextual y guardrails       │
│  - Streaming Engine (Server-Sent Events)               │
│  - Orquestador de resiliencia con fallback dinámico    │
└───────────────┬────────────────────────▲───────────────┘
                │                        │
       3. Async Request                  │ 4. SSE Tokens
     (Generative AI REST)                │    (TTFT < 350ms)
┌───────────────▼────────────────────────┴───────────────┐
│            Google Generative AI Infrastructure         │
│     (Gemini 3.1 Flash Lite / 3.5 Flash / Gemma)        │
└────────────────────────────────────────────────────────┘
```

### Principales Criterios de Diseño e Ingeniería:

1. **Adopción de Estándares Abiertos (Open Responses & A2A):**
   - En lugar de construir un endpoint conversacional monolítico o propietario, se implementó la especificación **Open Responses v1** para la inferencia y el protocolo **A2A (Agent-to-Agent)** a través del manifiesto `/.well-known/agent-card.json`. Esto permite que cualquier plataforma o cliente compatible auto-descubra las capacidades del agente, sus interfaces y sugerencias operativas sin acoplamiento.

2. **Baja Latencia Percibida mediante Server-Sent Events (SSE):**
   - Para maximizar la fluidez en la experiencia conversacional, el servicio implementa el ciclo de vida de eventos de streaming de Open Responses (`response.in_progress`, `response.output_item.added`, `response.output_text.delta`, `response.output_text.done`, `response.completed` y `[DONE]`), logrando un *Time To First Token* (TTFT) inferior a 350 ms.

3. **Estrategia de Resiliencia y Alta Disponibilidad (Multi-Model Fallback):**
   - En entornos productivos, los modelos fundacionales pueden experimentar picos de demanda o limitaciones transitorias de cuota (HTTP 503 / 429). El backend implementa un mecanismo de degradación elegante (*graceful fallback*) que enruta automáticamente la consulta a través de un pool de modelos alternativos de alta eficiencia garantizando continuidad operativa.

4. **Seguridad y Criterio de Cumplimiento Bancario (CNBV & PII):**
   - El sistema opera bajo el principio de menor privilegio: las claves de API no se exponen al cliente ni se almacenan en código fuente.
   - El contexto inyectado incorpora directrices de gobernanza de información para evitar la fuga de datos personales sensibles y mitigar alucinaciones fuera del espectro profesional verificado.

---

## 📡 2. Especificación de Endpoints (API Reference)

### `GET /.well-known/agent-card.json`
Manifiesto de auto-descubrimiento conforme a la especificación A2A.
- **Respuesta:** Objeto JSON con metadatos del agente, capacidades declaradas (`streaming: true`), modos de entrada/salida y lista de interfaces soportadas (`protocolBinding: https://openresponses.org/v1`).

### `POST /v1/responses`
Endpoint principal de inferencia compatible con Open Responses.
- **Headers:** `Content-Type: application/json`, `Authorization: Bearer <token>` (opcional).
- **Request Body:**
  ```json
  {
    "model": "optional_model_name",
    "input": "Hola, ¿cuál es tu experiencia en sistemas multi-agente?",
    "stream": true,
    "instructions": "Instrucciones de sistema opcionales"
  }
  ```
- **Responses:**
  - `stream: true` ➔ `Content-Type: text/event-stream` con eventos semánticos de Open Responses.
  - `stream: false` ➔ `Content-Type: application/json` con objeto estándar `response` y métricas de uso de tokens.

### `GET /health`
Sondeo de salud (*liveness & readiness probe*) para orquestadores y balanceadores de carga.
- **Respuesta:** `{"status": "ok", "timestamp": 1789493600}`

---

## 🛠️ 3. Ejecución y Desarrollo Local

### Requisitos Previos
- Python 3.10+
- Docker (opcional para entornos contenerizados)
- API Key de Google Generative AI

### Instalación de Dependencias
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuración de Variables de Entorno
Crear un archivo `.env` basado en `.env.example`:
```bash
GEMINI_API_KEY=tu_api_key_aqui
GEMINI_MODEL=gemini-3.1-flash-lite
PORT=8000
```

### Inicio del Servicio
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Ejecución con Docker
```bash
docker build -t banorte-cv-agent .
docker run -p 8000:8000 -e GEMINI_API_KEY="tu_api_key" banorte-cv-agent
```

---

## 🧪 4. Pruebas de Verificación y Contrato

Prueba de respuesta en modo JSON:
```bash
curl -X POST http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "¿Qué experiencia tienes en sistemas multi-agente con LangGraph?", "stream": false}'
```

Prueba de streaming SSE:
```bash
curl -N -X POST http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "Háblame de tu proyecto premiado por la NASA en la ISS", "stream": true}'
```

---

## 👩‍💻 Perfil Profesional
**Aurea Regina Guzmán Montero**  
*Especialista Sr. en Inteligencia Artificial e Innovación | Full Stack GenAI Engineer*  
- **LinkedIn:** [linkedin.com/in/regina-guzman-4a10531a8](https://www.linkedin.com/in/regina-guzman-4a10531a8/)  
- **GitHub:** [github.com/roxbambie-ship-it](https://github.com/roxbambie-ship-it)
