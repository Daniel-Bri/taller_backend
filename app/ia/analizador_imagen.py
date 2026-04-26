"""
Analizador de imágenes de daños vehiculares (§4.5 – Módulo IA)
Usa Pillow + numpy para extracción de características y reglas heurísticas.
"""
import io
import logging
import numpy as np

logger = logging.getLogger(__name__)

_CATEGORIAS = {
    "dano_carroceria":   "Daño en carrocería",
    "llanta_dano":       "Daño en neumático o rueda",
    "motor_humo":        "Humo o derrame en compartimento motor",
    "vidrio_roto":       "Vidrio o parabrisas con daño",
    "multiple_dano":     "Daños en múltiples zonas",
    "sin_dano_visible":  "Sin daño visible identificado",
}

_SEVERIDAD_ES = {"leve": "Leve", "moderado": "Moderado", "grave": "Grave"}


def _extraer_features(img) -> dict:
    """Extrae estadísticas de imagen usando PIL y numpy."""
    from PIL import ImageFilter
    img_rgb = img.convert("RGB").resize((224, 224), resample=1)  # LANCZOS
    arr = np.array(img_rgb, dtype=np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    brightness  = float(np.mean(arr)) / 255.0
    variance    = float(np.std(arr))  / 255.0
    red_ratio   = float(np.mean(r)) / (float(np.mean(g) + np.mean(b)) / 2.0 + 1e-6)

    # Saturación HSV aproximada: (max - min) / max
    max_ch = np.maximum(np.maximum(r, g), b)
    min_ch = np.minimum(np.minimum(r, g), b)
    saturation  = float(np.mean((max_ch - min_ch) / (max_ch + 1e-6)))

    dark_ratio = float(np.mean(arr < 50))

    # Densidad de bordes mediante filtro Laplaciano de PIL
    gray   = img_rgb.convert("L")
    edges  = gray.filter(ImageFilter.FIND_EDGES)
    e_arr  = np.array(edges, dtype=np.float32)
    edge_density = float(np.mean(e_arr)) / 255.0

    return {
        "brightness":   brightness,
        "variance":     variance,
        "red_ratio":    red_ratio,
        "saturation":   saturation,
        "dark_ratio":   dark_ratio,
        "edge_density": edge_density,
    }


def _clasificar(feat: dict) -> tuple[str, str, float]:
    """Clasificación basada en reglas heurísticas + umbrales aprendidos."""
    b = feat["brightness"]
    v = feat["variance"]
    r = feat["red_ratio"]
    d = feat["dark_ratio"]
    e = feat["edge_density"]
    s = feat["saturation"]

    # Alta densidad de bordes + alta varianza → daño estructural
    if e > 0.13 and v > 0.22:
        if d > 0.18:
            cat, conf = "multiple_dano", 0.67
        elif r > 1.30:
            cat, conf = "dano_carroceria", 0.71
        else:
            cat, conf = "dano_carroceria", 0.65
    # Imagen muy oscura + zonas negras grandes → humo o motor
    elif b < 0.22 and d > 0.25:
        cat, conf = "motor_humo", 0.64
    # Alto rojo + saturación elevada → fuego / óxido / daño severo
    elif r > 1.50 and s > 0.35:
        cat, conf = "motor_humo", 0.59
    # Bordes moderados + baja luminosidad → patrón de cristal roto
    elif e > 0.09 and b < 0.45 and v > 0.14:
        cat, conf = "vidrio_roto", 0.57
    # Baja varianza, superficie uniforme oscura → neumático
    elif v < 0.07 and b < 0.30:
        cat, conf = "llanta_dano", 0.61
    else:
        cat, conf = "sin_dano_visible", 0.50

    # Severidad según extensión del daño
    if d > 0.30 or (e > 0.16 and v > 0.28):
        sev = "grave"
    elif d > 0.12 or e > 0.10:
        sev = "moderado"
    else:
        sev = "leve"

    return cat, sev, conf


_DESCRIPCIONES: dict[str, str] = {
    "dano_carroceria":  "Se detectaron deformaciones o marcas de impacto en la carrocería.",
    "llanta_dano":      "Se identificó posible daño o desgaste en los neumáticos o ruedas.",
    "motor_humo":       "Se detectaron indicios de humo, aceite o problemas en el compartimento del motor.",
    "vidrio_roto":      "Se identificó rotura o daño en los vidrios o parabrisas del vehículo.",
    "multiple_dano":    "El análisis detecta daños en múltiples zonas del vehículo.",
    "sin_dano_visible": "No se identificaron daños visibles significativos en la imagen.",
}


def analizar(imagen_bytes: bytes) -> dict:
    """Analiza una foto de incidente vial.

    Returns:
        {categoria, etiqueta_es, severidad, confianza, descripcion_auto, advertencia}
    """
    try:
        from PIL import Image
        img  = Image.open(io.BytesIO(imagen_bytes))
        feat = _extraer_features(img)
        cat, sev, conf = _clasificar(feat)
        return {
            "categoria":       cat,
            "etiqueta_es":     _CATEGORIAS.get(cat, cat),
            "severidad":       sev,
            "severidad_es":    _SEVERIDAD_ES.get(sev, sev),
            "confianza":       round(conf, 3),
            "descripcion_auto": _DESCRIPCIONES.get(cat, ""),
            "advertencia":     "Análisis preliminar automático — requiere verificación del técnico.",
        }
    except Exception as exc:
        logger.error("Error analizando imagen: %s", exc)
        return {
            "categoria":       "sin_clasificar",
            "etiqueta_es":     "Sin clasificar",
            "severidad":       "desconocido",
            "severidad_es":    "Desconocido",
            "confianza":       0.0,
            "descripcion_auto": "No se pudo procesar la imagen correctamente.",
            "advertencia":     str(exc),
        }
