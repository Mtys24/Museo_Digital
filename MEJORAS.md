# Mejoras para el Museo Digital

## Alta prioridad (mucho impacto, poco esfuerzo)

### 🎤 Dictar preguntas con voz
Botón para hablar en vez de escribir usando reconocimiento de voz.
- **API:** Groq Whisper (gratis, ~200 req/día) o Google Speech-to-Text (60 min/mes gratis)
- **Qué se necesita:** Cuenta gratuita en Groq o Google Cloud, API key

### 📚 Conocimiento real vía Wikipedia ✅
El personaje consulta Wikipedia en tiempo real para dar datos precisos y verificables.
- **API:** Wikipedia API — sin key, ilimitada
- **Cómo funciona:** Antes de responder, busca en Wikipedia (español) y agrega el contexto al mensaje del LLM
- **Ejemplo:** Si preguntan "¿Cuándo inventaste la bobina Tesla?", busca en Wikipedia y da la fecha exacta
- **Archivos:** `wiki.py` — caché local para no repetir búsquedas

### 🗓️ Línea de tiempo interactiva
Al seleccionar un personaje, mostrar una línea visual con sus hitos clave (nacimiento, inventos, obras, muerte).
- **API:** Ninguna — se hace con HTML + CSS en Gradio
- **Datos:** Se definen en `figures.py` como un array de eventos con año y descripción

---

## Prioridad media

### 🖼️ Generar imágenes de época
Cuando el personaje habla de un lugar, invento u obra, mostrar una imagen generada automáticamente.
- **API:** Gemini API (imágenes + texto) o Stability AI (25 créditos/mes gratis)
- **Alternativa gratuita:** Unsplash API o Wikipedia Image API (fotos reales, no generadas)

### 🎮 Modo quiz
El personaje te toma un examen sobre su vida y obra, y te da una puntuación al final.
- **API:** Usa el mismo LLM que ya está implementado
- **Cómo funciona:** El system prompt del personaje cambia a modo "examinador"

### 🗣️ Charla entre dos personajes
Seleccionás dos figuras históricas y ellas dialogan entre sí automáticamente.
- **API:** Mismo LLM — se alternan los system prompts de cada personaje
- **UX:** Botón "Iniciar diálogo" + selector de segundo personaje

---

## Baja prioridad (pero muy original)

### 🌍 Traducción en vivo
Preguntarle a Da Vinci en italiano y que responda en italiano con su voz italiana.
- **API:** LibreTranslate (open source, sin key) o Google Translate API (gratis hasta 500K chars/mes)
- **Cómo funciona:** Se detecta el idioma del input y el personaje responde en ese idioma

### 📜 Visor de documentos históricos
El personaje te "muestra" una carta, patente o manuscrito original en pantalla.
- **API:** Ninguna — HTML renderizado en Gradio
- **Datos:** Imágenes de documentos históricos (dominio público) linkeadas desde Wikipedia

### 🔊 Música ambiental de época
Música de fondo que suena según la época del personaje (Renacimiento, siglo XIX, etc.).
- **API:** Freesound API (gratis, requiere cuenta)
- **Alternativa:** Archivo de música libre (Creative Commons) incluido en el proyecto

---

## Notas técnicas generales

- **Gradio 6.0** compatible — todas las mejoras se integran dentro del sistema de Blocks existente
- Las APIs gratuitas tienen rate limits; implementar caché local para evitar llamadas repetidas (ej: cachear respuestas de Wikipedia por personaje+pregunta)
- El archivo `figures.py` es el lugar natural para agregar datos nuevos (eventos de timeline, imágenes asociadas, etc.)
