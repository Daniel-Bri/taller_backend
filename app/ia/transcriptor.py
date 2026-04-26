"""
Transcriptor de audio para mensajes de voz en incidentes viales (§4.5 – Módulo IA)
Usa SpeechRecognition con Google Web Speech API (sin clave para uso básico).
"""
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

try:
    import speech_recognition as sr
    _SR_OK = True
except ImportError:
    _SR_OK = False
    logger.warning("SpeechRecognition no instalado. CU08 operará sin transcripción.")


def transcribir(audio_bytes: bytes, formato: str = "wav") -> dict:
    """Transcribe bytes de audio a texto en español.

    Returns:
        {transcripcion, idioma, exito, mensaje}
    """
    if not _SR_OK:
        return {
            "transcripcion": "",
            "idioma": "es-ES",
            "exito": False,
            "mensaje": "Módulo SpeechRecognition no disponible. Ejecutar: pip install SpeechRecognition",
        }

    fmt = formato.lower().strip(".")
    # SpeechRecognition soporta nativamente: wav, aiff, flac
    if fmt not in ("wav", "aiff", "aif", "flac"):
        fmt = "wav"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        with sr.AudioFile(tmp_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio_data = recognizer.record(source)

        texto = recognizer.recognize_google(audio_data, language="es-ES")
        return {
            "transcripcion": texto,
            "idioma": "es-ES",
            "exito": True,
            "mensaje": "Transcripción exitosa",
        }

    except sr.UnknownValueError:
        return {
            "transcripcion": "",
            "idioma": "es-ES",
            "exito": False,
            "mensaje": "No se pudo entender el audio. Intenta hablar más claro o en un lugar silencioso.",
        }
    except sr.RequestError as exc:
        return {
            "transcripcion": "",
            "idioma": "es-ES",
            "exito": False,
            "mensaje": f"Error al conectar con el servicio de transcripción: {exc}",
        }
    except Exception as exc:
        logger.error("Error transcribiendo audio: %s", exc)
        return {
            "transcripcion": "",
            "idioma": "es-ES",
            "exito": False,
            "mensaje": f"Error procesando el audio: {exc}",
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
