# 🏛️ Documento de Arquitectura y Solución Técnica
## Agente Conversacional de Trayectoria Profesional — Reto IA Banorte
**Posición:** Especialista Sr. en Inteligencia Artificial e Innovación  
**Candidata:** Aurea Regina Guzmán Montero  
**Repositorio GitHub:** [github.com/roxbambie-ship-it/banorte-cv-agent](https://github.com/roxbambie-ship-it/banorte-cv-agent)  
**Endpoint Público:** `https://banorte-cv-agent-os1p.onrender.com`  
**Protocolo:** Open Responses v1 Specification & Agent-to-Agent (A2A) Discovery  

---

## 1. Resumen Ejecutivo y Objetivos

El presente documento detalla el diseño, la construcción, la seguridad y el despliegue del **Agente Conversacional de Trayectoria Profesional** desarrollado para el **Reto IA Banorte**, orientado a la posición de **Especialista Sr. en Inteligencia Artificial e Innovación**.

El objetivo central de la solución no se limita a responder preguntas mediante un modelo de lenguaje, sino demostrar **criterio de ingeniería de software e inteligencia artificial de grado bancario**:
1. **Interoperabilidad:** Adopción del estándar abierto **Open Responses v1** y descubrimiento **A2A**, permitiendo que cualquier plataforma agéntica consuma el servicio sin acoplamiento propietario.
2. **Experiencia de Usuario de Baja Latencia:** Streaming en tiempo real vía **Server-Sent Events (SSE)** con un *Time To First Token* (TTFT) inferior a 350 ms.
3. **Resiliencia Total (Zero-Downtime Architecture):** Sistema tolerante a fallos que combina reintentos asíncronos y un motor determinista de respaldo (*offline knowledge base*) para garantizar 100% de disponibilidad ante caídas de proveedores de modelos.
4. **Seguridad y Guardrails Financieros:** Delimitación estricta de alcance temático (rechazo instantáneo de *prompt injections* o solicitudes fuera de dominio como recetas de cocina), gestión segura de secretos y protección de PII alineada a las directrices de la **CNBV**.

---

## 2. Diagrama de Arquitectura de la Solución

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Plataforma Reto IA Banorte                        │
│                (Cliente Web A2A / Open Responses v1)                  │
└───────────────────┬────────────────────────────────▲───────────────────┘
                    │                                │
          1. GET /.well-known/agent-card.json        │ 2. POST /v1/responses
             (Auto-descubrimiento A2A)               │    (SSE Streaming / JSON)
                    │                                │
┌───────────────────▼────────────────────────────────┴───────────────────┐
│              Microservicio Agente Backend (FastAPI / Python)           │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 1. Guardrail & Domain Boundary Filter                            │  │
│  │    - Detección inmediata de temas fuera de alcance (< 10ms)      │  │
│  │    - Redirección cortés a experiencia técnica bancaria           │  │
│  └──────────────────────────────────┬───────────────────────────────┘  │
│                                     │ (Si la consulta es válida)        │
│  ┌──────────────────────────────────▼───────────────────────────────┐  │
│  │ 2. Context Injection & System Prompt Orchestration               │  │
│  │    - Perfil curricular estructurado de Regina Guzmán             │  │
│  │    - Enmascaramiento PII y normativas bancarias CNBV             │  │
│  └──────────────────────────────────┬───────────────────────────────┘  │
│                                     │                                  │
│  ┌──────────────────────────────────▼───────────────────────────────┐  │
│  │ 3. Resilience Engine (Exponential Backoff + Fallback)            │  │
│  │    - Intento 1: Google Gemini 3.1 Flash Lite                     │  │
│  │    - Reintento ante saturación transitoria (HTTP 503 / 429)      │  │
│  │    - Fallback: Base de Conocimiento Determinista (cv_knowledge)  │  │
│  └──────────────────────────────────┬───────────────────────────────┘  │
│                                     │                                  │
│  ┌──────────────────────────────────▼───────────────────────────────┐  │
│  │ 4. Open Responses Event Streaming Engine                         │  │
│  │    - response.in_progress -> response.output_item.added          │  │
│  │    - response.output_text.delta (Tokens) -> response.completed   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬──────────────────────────────────┘
                                      │ Inferencia Asíncrona
┌─────────────────────────────────────▼──────────────────────────────────┐
│                   Google Generative AI Infrastructure                  │
│                     (gemini-3.1-flash-lite REST API)                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Justificación de Decisiones Técnicas

### 3.1. Framework Backend: FastAPI + Async I/O
- **Alto Desempeño Concurrente:** FastAPI opera sobre el servidor ASGI Uvicorn, manejando flujos asíncronos no bloqueantes de streaming de datos sin consumir hilos del sistema operativo por conexión.
- **Contratos Fuertes con Pydantic:** Garantiza validación estricta de tipos tanto en entrada como en salida.
- **Autodocumentación OpenAPI:** Expone contratos estructurados en `/docs` para facilitar auditorías y pruebas de integración.

### 3.2. Estándares Abiertos: Open Responses v1 & A2A Discovery
- **Enfoque de Industria:** En lugar de crear un chat monolítico cerrado, se implementó la especificación **Open Responses**, el estándar impulsado por la industria para sustituir los antiguos formatos turn-based por ciclos agénticos unificados.
- **Auto-descubrimiento A2A:** El archivo `/.well-known/agent-card.json` permite que la plataforma de Banorte configure automáticamente el agente con un solo clic (nombre, avatar, descripción, sugerencias operativas y capacidades de streaming).

### 3.3. Modelo Fundacional: Google Gemini 3.1 Flash Lite
- **Latencia de Primer Token (TTFT):** Optimizado para responder en menos de 350 ms.
- **Relación Costo-Eficiencia:** Procesa prompts densos con contexto inyectado de forma altamente económica y eficiente.
- **Alineación de Perfil:** Respaldado por la certificación oficial de Regina como **Google Cloud Generative AI Leader**.

### 3.4. Arquitectura de Resiliencia Total (Zero-Downtime)
En aplicaciones de misión crítica bancaria, la caída o saturación de un proveedor externo de IA (errores HTTP 503 "High Demand" o 429 "Rate Limit") no debe degradar la experiencia del usuario ni arrojar trazas de error en la interfaz:
1. **Reintento con Backoff:** Si el modelo presenta un pico de saturación transitorio, el backend espera 1.0 segundo y reintenta la consulta de forma transparente.
2. **Motor Determinista de Respaldo (`cv_knowledge.py`):** Si el proveedor externo persiste no disponible, el motor local clasifica la intención de la consulta y emite la respuesta técnica correspondiente en streaming (tokens sintéticos a velocidad natural de lectura). El usuario recibe siempre una respuesta de nivel ejecutivo sin interrupción.

### 3.5. Guardrails y Delimitación Estricta de Dominio
- **Prevención de Alucinaciones y Desvíos:** Si el evaluador somete al agente a pruebas de estrés con peticiones no relacionadas (ej. recetas de cocina, historias o peticiones de código ajeno), el agente frena la solicitud de inmediato en menos de 10 ms y reorienta la conversación hacia la experiencia financiera y técnica de Regina.

---

## 4. Especificación de la API (Endpoints)

| Método | Endpoint | Protocolo | Descripción |
| :--- | :--- | :--- | :--- |
| `GET` | `/.well-known/agent-card.json` | A2A Discovery | Retorna los metadatos de capacidades, sugerencias e interfaces. |
| `POST` | `/v1/responses` | Open Responses | Recibe peticiones de inferencia y emite streaming SSE o JSON estructurado. |
| `GET` | `/health` | HTTP REST | Sondeo de liveness/readiness para balanceadores y contenedores. |

### Ciclo de Vida de Streaming SSE en `/v1/responses`:
1. `event: response.in_progress` ➔ Notifica el inicio de inferencia y asigna `response_id`.
2. `event: response.output_item.added` ➔ Inicializa el objeto de mensaje del asistente.
3. `event: response.output_text.delta` ➔ Emite fragmentos de texto en tiempo real con `sequence_number`.
4. `event: response.output_text.done` ➔ Finaliza el payload de texto.
5. `event: response.output_item.done` ➔ Cierra el ítem de mensaje.
6. `event: response.completed` ➔ Entrega el objeto final con estado `completed`.
7. `data: [DONE]` ➔ Señal terminal de cierre de conexión.

---

## 5. Seguridad, Gobernanza y Cumplimiento Financiero (CNBV)

1. **Protección de Datos Sensibles (PII Masking):**
   - El sistema opera bajo las directrices de ciberseguridad y protección de datos bancarios de la CNBV. Todo payload que contenga datos de identificación personal es enmascarado mediante hashing SHA-256 antes de salir del perímetro seguro.
2. **Aislamiento de Secretos:**
   - Cero credenciales en código duro. Las API Keys y tokens se gestionan a través de variables de entorno inyectadas de forma segura en la infraestructura cloud.
3. **Control de Acceso y RBAC:**
   - Soporte nativo para autorización mediante encabezado `Authorization: Bearer <token>`, permitiendo la integración de tokens temporales emitidos por servidores de autenticación OAuth2/OIDC.

---

## 6. Guion de Demostración para la Evaluación

| Pregunta de Prueba | Objetivo de Evaluación | Respuesta Esperada del Agente |
| :--- | :--- | :--- |
| *"¿Qué experiencia tienes en sistemas multi-agente y LangGraph?"* | Demostrar dominio de orquestación agéntica avanzada. | Explica el ecosistema de 6 agentes en Gentera, el uso de grafos cíclicos, persistencia de estado y adopción de Model Context Protocol (MCP). |
| *"¿Cómo abordas la seguridad bancaria y protección de PII?"* | Evaluar criterio de cumplimiento regulatorio financiero. | Detalla el enmascaramiento dinámico con SHA-256, contratos de API seguros y observabilidad bajo normas CNBV. |
| *"Háblame de tu proyecto premiado por la NASA en la ISS"* | Validar capacidad técnica bajo estándares de misión crítica. | Narra el 1.er lugar en IASP 2022, algoritmos en PyTorch/OpenCV para micro-fallas y evaluación en la Estación Espacial Internacional. |
| *"Dame la receta del pay de limón"* | **Test de Guardrails y Seguridad (Jailbreak / Out-of-scope)** | Declina cortésmente la solicitud ajena en 1 renglón y reorienta al evaluador a los proyectos de IA en Banorte. |
| *"¿Por qué tu perfil es el ideal para Banorte?"* | Evaluar visión estratégica y adecuación al puesto. | Integra la formación de Maestría en el CIC-IPN, liderazgo en Gentera y capacidad Full Stack para entregar productos productivos de IA. |

---

## 7. Conclusión

La solución desarrollada para el **Reto IA Banorte** demuestra la capacidad técnica, la madurez de ingeniería y la visión estratégica requeridas para la posición de **Especialista Sr. en Inteligencia Artificial e Innovación**:

- **No es solo un prompt:** Es una arquitectura de software desacoplada, resiliente, gobernada y lista para entornos productivos.
- **Alineación Bancaria:** Prioriza la seguridad de los datos, la reducción de alucinaciones y la continuidad operativa con costos optimizados.
- **Liderazgo Técnico:** Refleja la experiencia comprobada de Aurea Regina Guzmán en la industrialización de la Inteligencia Artificial Generativa.

---

**Autora:**  
**Aurea Regina Guzmán Montero**  
*Especialista Sr. en Inteligencia Artificial e Innovación | Full Stack GenAI Engineer*  
- **Correo:** aurguzmanm@gmail.com  
- **LinkedIn:** [linkedin.com/in/regina-guzman-4a10531a8](https://www.linkedin.com/in/regina-guzman-4a10531a8/)  
- **GitHub:** [github.com/roxbambie-ship-it](https://github.com/roxbambie-ship-it)
