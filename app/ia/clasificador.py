"""
Clasificador de tipo de incidente vial (§4.5 – Módulo IA)
Modelo: TF-IDF + Logistic Regression entrenado con datos sintéticos en español.
"""
import os
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

TIPOS_INCIDENTE = [
    "llanta_ponchada",
    "falla_motor",
    "sin_gasolina",
    "bateria_muerta",
    "accidente",
    "sobrecalentamiento",
    "frenos",
    "transmision",
    "otros",
]

ETIQUETAS_ES = {
    "llanta_ponchada":  "Llanta ponchada",
    "falla_motor":      "Falla de motor",
    "sin_gasolina":     "Sin combustible",
    "bateria_muerta":   "Batería descargada",
    "accidente":        "Accidente vial",
    "sobrecalentamiento": "Sobrecalentamiento",
    "frenos":           "Falla en frenos",
    "transmision":      "Falla en transmisión",
    "otros":            "Otro tipo de falla",
}

_ENTRENAMIENTO: list[tuple[str, str]] = [
    # llanta_ponchada
    ("se me ponchó la llanta delantera", "llanta_ponchada"),
    ("llanta desinflada necesito ayuda", "llanta_ponchada"),
    ("neumático reventado en la carretera", "llanta_ponchada"),
    ("rueda pinchada tengo el carro en la vía", "llanta_ponchada"),
    ("llanta baja de aire", "llanta_ponchada"),
    ("se pinchó la goma trasera", "llanta_ponchada"),
    ("neumático completamente desinflado", "llanta_ponchada"),
    ("me explotó la llanta a toda velocidad", "llanta_ponchada"),
    ("goma ponchada en la autopista", "llanta_ponchada"),
    ("llanta trasera con clavo metido", "llanta_ponchada"),
    ("se reventó el neumático derecho", "llanta_ponchada"),
    ("tengo la rueda baja sin poder mover el carro", "llanta_ponchada"),
    ("pinchadura en la llanta delantera izquierda", "llanta_ponchada"),
    ("el carro jala hacia un lado llanta baja", "llanta_ponchada"),
    ("la rueda trasera está completamente desinflada", "llanta_ponchada"),
    # falla_motor
    ("el motor no enciende", "falla_motor"),
    ("el carro no arranca de ninguna manera", "falla_motor"),
    ("motor fundido sin respuesta", "falla_motor"),
    ("el vehículo no prende", "falla_motor"),
    ("falla grave en el motor", "falla_motor"),
    ("el coche se apagó y no enciende más", "falla_motor"),
    ("problemas al encender el motor", "falla_motor"),
    ("motor haciendo ruido extraño y se apagó solo", "falla_motor"),
    ("el motor se detuvo de repente en la vía", "falla_motor"),
    ("no puedo arrancar el auto por más que intento", "falla_motor"),
    ("motor averiado varado en la ruta", "falla_motor"),
    ("falla mecánica el motor no responde", "falla_motor"),
    ("el carro se paró y no enciende ni hace nada", "falla_motor"),
    ("motor hace golpes extraños y luego se apaga", "falla_motor"),
    ("el motor vibra mucho y se apagó", "falla_motor"),
    # sin_gasolina
    ("me quedé sin gasolina en la autopista", "sin_gasolina"),
    ("sin combustible varado en carretera", "sin_gasolina"),
    ("el tanque está vacío necesito gasolina", "sin_gasolina"),
    ("me quedé sin gas y no puedo moverme", "sin_gasolina"),
    ("tanque vacío en la vía principal", "sin_gasolina"),
    ("necesito gasolina urgente me quedé tirado", "sin_gasolina"),
    ("se acabó el combustible en la carretera", "sin_gasolina"),
    ("nafta vacía sin poder arrancar", "sin_gasolina"),
    ("el vehículo se apagó por falta de gasolina", "sin_gasolina"),
    ("indicador de gasolina en cero y se apagó", "sin_gasolina"),
    ("depósito vacío no tengo gasolina cerca", "sin_gasolina"),
    ("me quedé sin diesel en la ruta", "sin_gasolina"),
    ("el tanque de combustible está en reserva y vacío", "sin_gasolina"),
    # bateria_muerta
    ("batería descargada no enciende nada", "bateria_muerta"),
    ("se me murió la batería del carro", "bateria_muerta"),
    ("batería agotada totalmente", "bateria_muerta"),
    ("el carro no enciende la batería está muerta", "bateria_muerta"),
    ("necesito un puente para la batería", "bateria_muerta"),
    ("batería sin carga no responde", "bateria_muerta"),
    ("el acumulador está descargado", "bateria_muerta"),
    ("no tiene energía la batería está muerta", "bateria_muerta"),
    ("me dejó tirado la batería del auto", "bateria_muerta"),
    ("el auto no tiene electricidad la batería está vacía", "bateria_muerta"),
    ("necesito cargar la batería del vehículo", "bateria_muerta"),
    ("no encienden las luces la batería está agotada", "bateria_muerta"),
    ("el carro no hace nada al girar la llave batería muerta", "bateria_muerta"),
    # accidente
    ("tuve un accidente de tráfico en la vía principal", "accidente"),
    ("choque en la carretera necesito ayuda", "accidente"),
    ("colisión frontal con otro vehículo", "accidente"),
    ("accidente vehicular necesito asistencia inmediata", "accidente"),
    ("choqué con otro carro en el semáforo", "accidente"),
    ("volcamiento del vehículo en la curva", "accidente"),
    ("me golpearon en la parte trasera del auto", "accidente"),
    ("impacto lateral en el auto", "accidente"),
    ("accidente en la autopista", "accidente"),
    ("colisión necesito asistencia urgente", "accidente"),
    ("choque múltiple en la carretera principal", "accidente"),
    ("volcé el auto en una curva cerrada", "accidente"),
    ("el carro se salió de la vía y chocó", "accidente"),
    ("fui chocado por detrás hay daños serios", "accidente"),
    # sobrecalentamiento
    ("el motor se calentó demasiado", "sobrecalentamiento"),
    ("temperatura del motor muy alta en el marcador", "sobrecalentamiento"),
    ("el radiador está echando vapor", "sobrecalentamiento"),
    ("el coche se sobrecalentó y se apagó", "sobrecalentamiento"),
    ("indicador de temperatura en rojo", "sobrecalentamiento"),
    ("sale humo del motor por calentamiento excesivo", "sobrecalentamiento"),
    ("el radiador se quedó sin agua y está hirviendo", "sobrecalentamiento"),
    ("el motor se prendió temperatura subió al tope", "sobrecalentamiento"),
    ("el termómetro del motor al máximo", "sobrecalentamiento"),
    ("agua hirviendo sale del motor", "sobrecalentamiento"),
    ("overheating el motor está al límite de temperatura", "sobrecalentamiento"),
    ("el indicador de calor está parpadeando rojo", "sobrecalentamiento"),
    ("hay vapor saliendo del cofre del auto", "sobrecalentamiento"),
    # frenos
    ("los frenos no funcionan bien", "frenos"),
    ("frenos sin respuesta al pisar el pedal", "frenos"),
    ("el pedal de freno está al piso y no frena", "frenos"),
    ("frenos fallando en la carretera es peligroso", "frenos"),
    ("se me fueron los frenos del carro", "frenos"),
    ("freno de mano trabado no puedo moverme", "frenos"),
    ("pastillas de freno desgastadas hace ruido al frenar", "frenos"),
    ("el carro no frena correctamente", "frenos"),
    ("pérdida de líquido de frenos en la vía", "frenos"),
    ("los frenos chirrían y no frenan bien", "frenos"),
    ("el carro tarda mucho en detenerse riesgo de accidente", "frenos"),
    ("el pedal de freno se hunde hasta el fondo", "frenos"),
    # transmision
    ("la caja de cambios no funciona", "transmision"),
    ("problemas con la transmisión automática", "transmision"),
    ("no entra ninguna marcha en la caja de velocidades", "transmision"),
    ("la transmisión automática falla al acelerar", "transmision"),
    ("se traba el cambio de velocidades", "transmision"),
    ("la palanca de cambios no responde", "transmision"),
    ("ruido extraño al cambiar de marcha", "transmision"),
    ("transmisión patinando no agarra velocidad", "transmision"),
    ("la caja de velocidades está averiada", "transmision"),
    ("el carro no avanza aunque ponga primera marcha", "transmision"),
    ("la transmisión se traba en neutro", "transmision"),
    ("el carro se queda en un solo cambio", "transmision"),
    # otros
    ("problemas con el vehículo no sé qué es", "otros"),
    ("necesito asistencia en carretera", "otros"),
    ("vehículo varado necesito ayuda urgente", "otros"),
    ("problema eléctrico en el auto", "otros"),
    ("el carro tiene una falla desconocida", "otros"),
    ("no sé qué le pasa al coche", "otros"),
    ("falla general en el vehículo", "otros"),
    ("emergencia en carretera sin saber la causa", "otros"),
    ("el carro hace ruidos raros no sé qué es", "otros"),
    ("luz del tablero encendida sin saber por qué", "otros"),
    ("vehículo inmovilizado causa desconocida", "otros"),
    ("el auto se comporta raro al manejar", "otros"),
    ("no arranca y no sé la causa", "otros"),
]

MODEL_PATH = "app/ia/modelo_clasificador.joblib"
_pipeline: Pipeline | None = None


def _entrenar() -> Pipeline:
    import joblib
    textos  = [t for t, _ in _ENTRENAMIENTO]
    etiquetas = [e for _, e in _ENTRENAMIENTO]
    p = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=5000,
            sublinear_tf=True,
            analyzer="word",
            min_df=1,
        )),
        ("clf", LogisticRegression(
            max_iter=2000,
            C=4.0,
            solver="lbfgs",
        )),
    ])
    p.fit(textos, etiquetas)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(p, MODEL_PATH)
    return p


def inicializar() -> None:
    global _pipeline
    try:
        import joblib
        if os.path.exists(MODEL_PATH):
            _pipeline = joblib.load(MODEL_PATH)
        else:
            _pipeline = _entrenar()
        logger.info("Clasificador de incidentes listo (%d clases)", len(TIPOS_INCIDENTE))
    except Exception as exc:
        logger.error("Error inicializando clasificador: %s", exc)
        _pipeline = None


def clasificar(texto: str) -> dict:
    """Clasifica el tipo de incidente a partir de texto libre en español.

    Returns:
        {tipo, etiqueta_es, confianza, alternativas}
    """
    if not _pipeline or not texto or not texto.strip():
        return {
            "tipo": "otros",
            "etiqueta_es": ETIQUETAS_ES["otros"],
            "confianza": 0.0,
            "alternativas": [],
        }
    try:
        probs  = _pipeline.predict_proba([texto])[0]
        clases = _pipeline.classes_
        idx    = int(np.argmax(probs))
        top3   = sorted(zip(clases, probs), key=lambda x: -x[1])[:3]
        return {
            "tipo":        str(clases[idx]),
            "etiqueta_es": ETIQUETAS_ES.get(str(clases[idx]), str(clases[idx])),
            "confianza":   round(float(probs[idx]), 3),
            "alternativas": [
                {
                    "tipo":        t,
                    "etiqueta_es": ETIQUETAS_ES.get(t, t),
                    "confianza":   round(float(p), 3),
                }
                for t, p in top3[1:]
            ],
        }
    except Exception as exc:
        logger.error("Error en clasificar: %s", exc)
        return {"tipo": "otros", "etiqueta_es": "Otro tipo de falla", "confianza": 0.0, "alternativas": []}
