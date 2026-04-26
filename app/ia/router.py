"""
Endpoints de Inteligencia Artificial — análisis directo (§4.5)
"""
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from app.ia import clasificador, analizador_imagen, transcriptor

router = APIRouter()


class ClasificarBody(BaseModel):
    texto: str


@router.post("/clasificar-incidente")
async def clasificar_incidente(body: ClasificarBody):
    """CU05/CU09 – Clasifica el tipo de incidente a partir de texto libre en español."""
    return clasificador.clasificar(body.texto)


@router.post("/analizar-foto")
async def analizar_foto(foto: UploadFile = File(...)):
    """CU07 – Analiza una foto de daño vehicular y retorna categoría + severidad."""
    contenido = await foto.read()
    return analizador_imagen.analizar(contenido)


@router.post("/transcribir-audio")
async def transcribir_audio(audio: UploadFile = File(...)):
    """CU08 – Transcribe un audio de voz y clasifica el tipo de incidente."""
    contenido = await audio.read()
    ext = "wav"
    if audio.filename and "." in audio.filename:
        ext = audio.filename.rsplit(".", 1)[-1].lower()

    resultado_transcripcion = transcriptor.transcribir(contenido, ext)
    clasificacion = None
    if resultado_transcripcion.get("exito") and resultado_transcripcion.get("transcripcion"):
        clasificacion = clasificador.clasificar(resultado_transcripcion["transcripcion"])

    return {**resultado_transcripcion, "clasificacion": clasificacion}
