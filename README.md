# 🏛️ Agente de CV Profesional — Reto IA Banorte
### Candidata: Aurea Regina Guzmán Montero
**Posición:** Especialista Sr. en Inteligencia Artificial e Innovación  
**Estándar de Interoperabilidad:** Open Responses v1 + Protocolo A2A (Agent Card)  
**Modelo Fundacional:** Google Gemini 1.5 Flash (Google Cloud Generative AI)

---

## 🎯 1. Visión General del Proyecto

Este repositorio contiene la implementación y arquitectura de despliegue del **Agente Conversacional de Trayectoria Profesional** de **Aurea Regina Guzmán Montero**, diseñado específicamente para el **Reto IA Banorte**.

El agente expone una interfaz estandarizada bajo la especificación abierta **Open Responses** y el protocolo de descubrimiento **A2A (Agent-to-Agent)** mediante `/.well-known/agent-card.json`. Permite a reclutadores, líderes técnicos y evaluadores de Banorte interactuar de manera fluida, natural e inteligente con el perfil profesional, proyectos de impacto, experiencia en sistemas multi-agente, arquitecturas financieras y trayectoria en innovación de Regina.

---

## 🏗️ 2. Decisiones Técnicas y Arquitectura

```
┌────────────────────────────────────────────────────────┐
│               Plataforma Reto IA Banorte               │
│          (Cliente web compatible con A2A)             │
└───────────────┬────────────────────────▲───────────────┘
                │                        │
       1. Descubrimiento A2A             │ 2. POST /v1/responses
 (GET /.well-known/agent-card.json)      │    (Streaming SSE / JSON)
                │                        │
┌───────────────▼────────────────────────┴───────────────┐
│              Agente de CV (FastAPI Backend)            │
│  - Parser de mensajes Open Responses                   │
│  - Inyección de Contexto & System Prompts (RAG ligero) │
│  - Orquestador de Eventos SSE (response.output_text)   │
└───────────────┬────────────────────────▲───────────────┘
                │                        │
       3. Request REST                   │ 4. Tokens SSE
   (generateContent / Stream)            │    (Latencia < 400ms)
┌───────────────▼────────────────────────┴───────────────┐
│               Google Gemini Foundation Model           │
│                    (gemini-1.5-flash)                  │
└────────────────────────────────────────────────────────┘
```

### Justificación de Decisiones Técnicas:

1. **Framework Backend (FastAPI + Async I/O):**
   - Se seleccionó **Python + FastAPI** por su alto desempeño asíncrono (`async`/`await`), su tipado estricto con Pydantic y su facilidad para orquestar flujos de streaming (`Server-Sent Events - SSE`) sin bloquear el bucle de eventos.
   
2. **Modelo Fundacional (Google Gemini 1.5 Flash):**
   - Ofrece una ventana de contexto masiva (1M tokens), baja latencia de primer token (TTFT < 400ms) y gran capacidad de razonamiento con costos de inferencia optimizados.
   - Alineado a la certificación oficial de Regina como **Google Cloud Generative AI Leader**.

3. **Protocolo Open Responses & A2A:**
   - En lugar de implementar un chat propietario cerrado, se adoptó el estándar **Open Responses**, garantizando total interoperabilidad con plataformas como Parley, LibreChat, Open WebUI y la plataforma del Reto IA Banorte.
   - La inclusión de `/.well-known/agent-card.json` permite la autodescripción del agente, sus capacidades de streaming y sugerencias dinámicas de preguntas (`promptSuggestions`).

4. **Seguridad y Criterio Financiero (Banking Compliance):**
   - **Gestión Segura de Secretos:** La API key no se expone en el cliente; reside en variables de entorno seguras (`GEMINI_API_KEY`) y admite tokens Bearer dinámicos enviados por el cliente.
   - **Enfoque de Guardrails y PII:** El agente está instruido para proteger información personal sensible y apegarse estrictamente al perfil profesional verificado, mitigando alucinaciones.

---

## 📂 3. Estructura del Repositorio

```
banorte-cv-agent/
├── main.py                 # Servidor FastAPI y endpoints de Open Responses
├── profile_data.py         # Contexto profesional exhaustivo de Regina Guzmán
├── requirements.txt       # Dependencias de Python mínimas y optimizadas
├── Dockerfile             # Contenedor listo para despliegue en cualquier nube
├── .env.example           # Plantilla de variables de entorno
└── README.md              # Documentación técnica y guía de despliegue
```

---

## 🚀 4. Guía de Ejecución y Despliegue

### Opción A: Despliegue Gratuito en Render.com (Recomendado para Producción)

1. Sube esta carpeta a un nuevo repositorio público en tu GitHub (ej. `banorte-cv-agent`).
2. Entra a [render.com](https://render.com) e inicia sesión con tu cuenta de GitHub.
3. Haz clic en **New +** y selecciona **Web Service**.
4. Conecta el repositorio de GitHub recién creado.
5. Configura los siguientes campos:
   - **Name:** `banorte-cv-agent`
   - **Language:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free`
6. En la sección **Environment Variables**, añade:
   - `GEMINI_API_KEY`: *(Pega tu clave de API de Google Gemini)*
   - `GEMINI_MODEL`: `gemini-1.5-flash`
7. Haz clic en **Create Web Service**.
8. En 2 minutos tendrás tu URL pública HTTPS, por ejemplo:
   `https://banorte-cv-agent.onrender.com`

---

### Opción B: Prueba Rápida Local con Túnel HTTPS (ngrok o localtunnel)

Si deseas probar el agente de inmediato en la plataforma de Banorte antes de desplegar en Render:

1. **Crear entorno virtual e instalar dependencias:**
   ```bash
   cd banorte-cv-agent
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configurar tu API Key de Gemini:**
   ```bash
   export GEMINI_API_KEY="tu_google_api_key"
   ```

3. **Ejecutar el servidor localmente:**
   ```bash
   python3 main.py
   # O con uvicorn:
   uvicorn main:app --port 8000
   ```

4. **Exponer el puerto 8000 a internet con HTTPS:**
   En otra terminal:
   ```bash
   npx localtunnel --port 8000
   # O con ngrok:
   # ngrok http 8000
   ```
   Te dará una URL HTTPS pública (ej. `https://hungry-foxes-sing.loca.lt`).

---

## 📋 5. Cómo Registrar el Agente en la Plataforma de Banorte

1. Ve a la plataforma del Reto IA Banorte: [https://bit.ly/4bAuyDh](https://bit.ly/4bAuyDh)
2. En el menú lateral izquierdo, haz clic en **Agentes**.
3. Haz clic en el botón superior derecho **+ Añadir un agente**.
4. En el primer campo **Importar desde tarjeta de agente**:
   - Pega tu URL pública:  
     `https://tu-servicio-render.onrender.com` (o la URL de tu túnel HTTPS)
   - Haz clic en **Importar**.  
     *(La plataforma consultará automáticamente `/.well-known/agent-card.json` y completará el nombre, descripción, sugerencias y la URL base `https://.../v1`).*
5. Si no pusiste la variable de entorno en el servidor, puedes ingresar tu API Key en el campo **Clave de API**.
6. En **Entrega de archivos**, déjalo en el valor por defecto.
7. Haz clic en **Añadir un agente**.
8. Dirígete a **Nuevo chat**, selecciona tu agente y ¡comienza a conversar con él!

---

## 🧪 6. Preguntas Sugeridas para la Demostración

- *"¿Cuál es tu trayectoria profesional y qué experiencia tienes en el sector financiero?"*
- *"¿Cómo construiste el ecosistema multi-agente con LangGraph y MCP en Gentera?"*
- *"¿Qué medidas de seguridad bancaria y enmascaramiento de PII implementaste bajo la regulación de la CNBV?"*
- *"Cuéntame sobre tu proyecto premiado por la NASA que se probó en la Estación Espacial Internacional."*
- *"¿Por qué consideras que tu perfil agrega valor inmediato como Especialista Sr. en IA e Innovación en Banorte?"*

---

## 👩‍💻 Autora
**Aurea Regina Guzmán Montero**  
*Especialista Sr. en Inteligencia Artificial e Innovación | Full Stack GenAI Engineer*  
- Correo: aurguzmanm@gmail.com  
- LinkedIn: [linkedin.com/in/aurguzmanm](https://linkedin.com/in/aurguzmanm)  
- GitHub: [github.com/aurguzman](https://github.com/aurguzman)
