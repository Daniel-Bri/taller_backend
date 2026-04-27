"""
Push notification service usando Firebase Admin SDK.
Si FIREBASE_CREDENTIALS_JSON o FIREBASE_CREDENTIALS_PATH no están configurados,
las notificaciones se omiten silenciosamente — el resto de la app sigue funcionando.
"""
import json
import logging
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_firebase_app = None
_firebase_initialized = False


def _init_firebase():
    global _firebase_app, _firebase_initialized
    if _firebase_initialized:
        return _firebase_app
    _firebase_initialized = True
    try:
        import firebase_admin
        from firebase_admin import credentials

        creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

        if creds_json:
            cred = credentials.Certificate(json.loads(creds_json))
        elif creds_path and os.path.exists(creds_path):
            cred = credentials.Certificate(creds_path)
        else:
            logger.info(
                "Firebase no configurado: define FIREBASE_CREDENTIALS_JSON "
                "o FIREBASE_CREDENTIALS_PATH para activar push notifications."
            )
            return None

        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK inicializado.")
        return _firebase_app
    except Exception as exc:
        logger.error(f"Error al inicializar Firebase Admin SDK: {exc}")
        return None


def _enviar_push(token: str, titulo: str, cuerpo: str, data: dict | None = None) -> bool:
    try:
        from firebase_admin import messaging
        if _init_firebase() is None:
            return False

        msg = messaging.Message(
            notification=messaging.Notification(title=titulo, body=cuerpo),
            data={k: str(v) for k, v in (data or {}).items()},
            token=token,
            android=messaging.AndroidConfig(priority="high"),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(aps=messaging.Aps(sound="default"))
            ),
        )
        messaging.send(msg)
        return True
    except Exception as exc:
        logger.warning(f"Push no enviada (token …{token[-10:]}): {exc}")
        return False


async def notificar_usuario(
    user_id: int,
    titulo: str,
    cuerpo: str,
    db: AsyncSession,
    data: dict | None = None,
) -> None:
    """Envía push a todos los dispositivos registrados de un usuario.
    Nunca lanza excepción — los errores se loguean y se ignoran."""
    try:
        from app.notificaciones.models import DispositivoToken
        result = await db.execute(
            select(DispositivoToken.token).where(DispositivoToken.user_id == user_id)
        )
        for (token,) in result.all():
            _enviar_push(token, titulo, cuerpo, data)
    except Exception as exc:
        logger.warning(f"notificar_usuario({user_id}): {exc}")
