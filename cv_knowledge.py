"""
Base de Conocimiento y Motor de Respaldo Determinista (Zero-Downtime Fallback)
Garantiza continuidad operativa y respuestas de alta fidelidad técnica incluso
ante interrupciones transitorias o cuotas de los proveedores de LLM.
"""

import re

GUARDRAIL_DEFLECTION = (
    "Como agente de trayectoria profesional de Aurea Regina Guzmán para Grupo Financiero Banorte, "
    "mi alcance está delimitado exclusivamente a su experiencia en Inteligencia Artificial, sistemas agénticos, "
    "arquitecturas de RAG y desarrollo Full Stack en el sector financiero. "
    "¿Te gustaría profundizar en su ecosistema de multi-agentes con LangGraph o en su proyecto con la NASA?"
)

MULTI_AGENT_RESPONSE = """Hola. Mi experiencia en el diseño y despliegue de **sistemas multi-agente autónomos** es uno de los pilares más sólidos de mi carrera en el sector financiero.

En **Gentera**, lideré la arquitectura y puesta en producción de un **ecosistema multi-agente de 6 agentes especializados**, orquestado bajo las siguientes decisiones técnicas:

1. **Orquestación Cíclica con LangGraph (Python):**
   - En lugar de flujos lineales rígidos, modelamos la interacción de los agentes como grafos dirigidos con ciclos (DAGs cíclicos).
   - Esto permite bucles autónomos de autorreflexión, corrección de errores en llamadas a herramientas y transferencias dinámicas de contexto (*agent-to-agent handoffs*) o escalamiento a supervisores humanos (*human-in-the-loop*).

2. **Model Context Protocol (MCP) para Integración Core:**
   - Fuimos pioneros en implementar **Model Context Protocol (MCP)** para conectar los LLMs con APIs del core bancario y bases de datos transaccionales.
   - Gracias a MCP, logramos un *tool calling* determinista con validación estricta de esquemas Pydantic, eliminando alucinaciones en consultas operativas.

3. **Gestión de Memoria y Estado (State Persistence):**
   - Implementamos persistencia de estado a corto plazo (para el flujo conversacional y llamadas multi-paso) y memoria episódica a largo plazo para personalización segura de la experiencia del usuario.

4. **Seguridad Bancaria y Cumplimiento CNBV:**
   - Diseñé una capa middleware de enmascaramiento dinámico de datos sensibles (**PII**) mediante hashing SHA-256 y tokenización antes de enviar cualquier información a los modelos fundacionales, garantizando total apego a la regulación bancaria.

5. **Liderazgo Técnico:**
   - Esta experiencia práctica la compartí como ponente magistral en **Google Women Techmakers (IWD CDMX)** en las oficinas de Pinterest, con la conferencia *"De Codificadoras a Directoras de Orquesta: Liderando Agentes"*.

Para **Banorte**, esta experiencia me permite acelerar inmediatamente iniciativas de agentes autónomos para la automatización de procesos de crédito, análisis de riesgos y copilotos operativos."""

NASA_RESPONSE = """Con mucho orgullo, gané el **1.er Lugar Internacional en el International Air and Space Program (IASP 2022)**, un programa desarrollado en colaboración con socios de la **NASA** en Huntsville, Alabama.

Aspectos clave del proyecto:
1. **Desarrollo de Software y Algoritmos de Visión:** Diseñé e implementé algoritmos de visión por computadora y análisis probabilístico en **Python (PyTorch, OpenCV)** con tableros interactivos para la detección y evaluación de micro-fallas estructurales en materiales expuestos a condiciones extremas de radiación y variaciones térmicas.
2. **Pruebas en la Estación Espacial Internacional (ISS):** Como resultado del primer lugar, el software y la muestra de material aeroespacial fueron enviados y evaluados en el módulo exterior de la **Estación Espacial Internacional (ISS)**.

Esta experiencia demostró mi capacidad para resolver problemas críticos bajo estándares aeroespaciales de tolerancia cero a fallos, una disciplina de calidad que aplico directamente a los sistemas de misión crítica en la banca."""

SECURITY_CNBV_RESPONSE = """En el sector financiero regulado, la seguridad, la gobernanza de datos y la privacidad son requisitos de diseño no negociables. En mis soluciones he implementado:

1. **Enmascaramiento Dinámico de PII (Personally Identifiable Information):**
   - Middleware en FastAPI que intercepta las peticiones de usuario y aplica algoritmos de hashing unidireccional (**SHA-256**) y tokenización reversible controlada a identificadores sensibles (RFC, CURP, números de cuenta, tarjetas) antes de que el payload llegue a cualquier API externa de LLM.
2. **Cumplimiento Normativo CNBV y PCI-DSS:**
   - Auditoría estricta de logs sin persistencia de datos desprotegidos.
   - Aislamiento de entornos y control de acceso basado en roles (**RBAC**) mediante contratos OAuth2, OIDC y JSON Web Tokens (JWT).
3. **Gestión Segura de Secretos:**
   - Cifrado en reposo y en tránsito con integración en Key Vaults (Azure Key Vault / GCP Secret Manager).
4. **Guardrails y Filtros de Contenido:**
   - Reglas de validación semántica en entrada y salida para mitigar ataques de inyección de prompts (*Prompt Injection*) y fuga de datos confidenciales."""

TRAYECTORIA_GENERAL_RESPONSE = """Hola. Soy **Aurea Regina Guzmán Montero**, Ingeniera en Informática (IPN UPIICSA, Titulada) con **Maestría en Inteligencia Artificial y Ciencia de Datos en curso en el Centro de Investigación en Computación (CIC-IPN)** y más de 5 años de experiencia liderando e implementando soluciones de IA Generativa y software empresarial en el sector financiero.

Mi trayectoria técnica se resume en:
- **Líder de IA Generativa y Agentes en Gentera (2021 - Presente):** Diseñé un ecosistema multi-agente con LangGraph y MCP, copilotos empresariales Full Stack (FastAPI, React, Next.js) con streaming SSE para más de 18,700 usuarios corporativos (reduciendo 35% tiempos de ciclo), y pipelines de RAG sobre bases vectoriales (Qdrant, Azure AI Search).
- **1.er Lugar Internacional en NASA IASP 2022:** Algoritmos de visión computacional y análisis estructural evaluados en la Estación Espacial Internacional (ISS).
- **Certificación Google Cloud Generative AI Leader** y conferencista magistral en **Google Women Techmakers**.

Mi propuesta de valor para **Banorte** como **Especialista Sr. en Inteligencia Artificial e Innovación** es mi capacidad comprobada para llevar la IA de la teoría a productos bancarios productivos, escalables, seguros y con impacto medible en el negocio.

¿Sobre qué área específica te gustaría que conversemos a continuación?"""


def get_deterministic_cv_response(query: str) -> str:
    """Retorna una respuesta técnica estructurada de acuerdo a la intención del usuario."""
    q = query.lower()

    # 1. Guardrails de temas ajenos
    if any(word in q for word in ["receta", "pay", "limon", "limón", "cocina", "comida", "pastel", "chiste", "poema", "horoscopo", "horóscopo"]):
        return GUARDRAIL_DEFLECTION

    # 2. Multi-agentes / LangGraph / MCP
    if any(word in q for word in ["agente", "multi-agente", "multiagente", "langgraph", "mcp", "orquestaci", "tool calling"]):
        return MULTI_AGENT_RESPONSE

    # 3. NASA / ISS / Aeroespacial
    if any(word in q for word in ["nasa", "iss", "espacio", "espacial", "aeroespacial", "premio", "reconocimiento"]):
        return NASA_RESPONSE

    # 4. Seguridad / PII / CNBV
    if any(word in q for word in ["seguridad", "cnbv", "pii", "privacidad", "cumplimiento", "ciberseguridad", "cifrado", "regulaci"]):
        return SECURITY_CNBV_RESPONSE

    # 5. Trayectoria general / Perfil / Banorte
    return TRAYECTORIA_GENERAL_RESPONSE
