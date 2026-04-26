import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import HTTPException

from app.core.config import settings


async def send_reset_code(to_email: str, code: str, nombre: str) -> None:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail="El servidor no tiene configurado el servicio de correo. "
                   "Agrega SMTP_USER y SMTP_PASSWORD en el archivo .env",
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Código de verificación — RutaSegura"
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to_email

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px">
      <h2 style="color:#2563EB;margin-bottom:8px">RutaSegura</h2>
      <p style="color:#1F2937">Hola <strong>{nombre}</strong>,</p>
      <p style="color:#1F2937">Tu código para restablecer la contraseña es:</p>
      <div style="background:#F3F4F6;border-radius:12px;padding:24px;text-align:center;margin:24px 0">
        <span style="font-size:36px;font-weight:800;letter-spacing:10px;color:#2563EB">{code}</span>
      </div>
      <p style="color:#6B7280;font-size:13px">
        Este código expira en <strong>15 minutos</strong>.<br>
        Si no solicitaste este cambio, ignora este mensaje.
      </p>
    </div>
    """

    msg.attach(MIMEText(html, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo enviar el correo: {exc}",
        )
