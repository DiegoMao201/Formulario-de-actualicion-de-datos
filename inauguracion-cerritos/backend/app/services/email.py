"""Envío de emails transaccionales con QR embebido (inline CID).

Estrategia: intenta SendGrid primero; si no hay API key o falla, cae a SMTP (Gmail).
Los errores de envío NO deben tumbar el registro del usuario -> se capturan y loguean.
"""
import base64
import logging
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from ..config import settings

logger = logging.getLogger("email")

BRAND_NAVY = "#0A2E57"
BRAND_YELLOW = "#FFD200"
BRAND_RED = "#E63329"


def _wrapper(titulo: str, cuerpo_html: str) -> str:
    return f"""\
<div style="margin:0;padding:0;background:#EEF3F8;font-family:Segoe UI,Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;padding:24px;">
    <div style="background:{BRAND_NAVY};border-radius:16px 16px 0 0;padding:28px 24px;text-align:center;">
      <div style="color:#fff;font-size:13px;letter-spacing:3px;opacity:.85;">TIENDA PINTUCO</div>
      <div style="color:{BRAND_YELLOW};font-size:26px;font-weight:800;margin-top:4px;">CERRITOS</div>
    </div>
    <div style="background:#fff;border-radius:0 0 16px 16px;padding:32px 28px;color:#172B3A;">
      <h1 style="font-size:22px;margin:0 0 12px;color:{BRAND_NAVY};">{titulo}</h1>
      {cuerpo_html}
      <hr style="border:none;border-top:1px solid #E3EAF2;margin:28px 0;">
      <p style="font-size:12px;color:#7A8AA0;margin:0;">
        Ferreinox S.A.S. BIC · {settings.store_address}<br>
        WhatsApp: 310 280 66 05 · www.ferreinox.co
      </p>
    </div>
  </div>
</div>"""


def _html_cupon(nombre: str, code: str) -> str:
    cuerpo = f"""
    <p>¡Hola <strong>{nombre}</strong>! Gracias por registrarte en la inauguración de la
    nueva <strong>Tienda Pintuco Cerritos</strong>. 🎉</p>
    <p>Este es tu cupón de bienvenida:</p>
    <div style="text-align:center;margin:22px 0;">
      <div style="display:inline-block;background:{BRAND_YELLOW};color:{BRAND_NAVY};
        font-size:30px;font-weight:800;padding:14px 28px;border-radius:12px;">10% OFF</div>
      <div style="margin-top:10px;font-size:15px;color:{BRAND_NAVY};font-weight:700;
        letter-spacing:1px;">{code}</div>
    </div>
    <p style="text-align:center;">Muestra este código QR en caja para redimirlo:</p>
    <div style="text-align:center;margin:12px 0 4px;">
      <img src="cid:qrimg" width="180" height="180" alt="QR del cupón"
        style="border:8px solid #fff;border-radius:12px;box-shadow:0 4px 16px rgba(10,46,87,.12);">
    </div>
    <p style="text-align:center;font-size:13px;color:#7A8AA0;">
      Revisa tu WhatsApp: te enviamos el enlace para <strong>girar la ruleta</strong> y ganar premios. 🎡
    </p>"""
    return _wrapper("¡Tu cupón está listo! 🎁", cuerpo)


def _html_premio(nombre: str, premio: str) -> str:
    cuerpo = f"""
    <p>¡Felicitaciones <strong>{nombre}</strong>! 🏆 Giraste la ruleta del equipo ganador
    Pintuco y te ganaste:</p>
    <div style="text-align:center;margin:22px 0;">
      <div style="display:inline-block;background:{BRAND_NAVY};color:{BRAND_YELLOW};
        font-size:24px;font-weight:800;padding:16px 30px;border-radius:12px;">{premio}</div>
    </div>
    <p style="text-align:center;">Presenta este QR en la tienda para reclamar tu premio:</p>
    <div style="text-align:center;margin:12px 0 4px;">
      <img src="cid:qrimg" width="200" height="200" alt="QR del premio"
        style="border:8px solid #fff;border-radius:12px;box-shadow:0 4px 16px rgba(10,46,87,.12);">
    </div>
    <p style="text-align:center;font-size:13px;color:#7A8AA0;">
      Válido en {settings.store_address}. Un solo uso.
    </p>"""
    return _wrapper("¡Ganaste! 🎉🏆", cuerpo)


# ---------------- Transporte ----------------
def _enviar_sendgrid(to: str, asunto: str, html: str, qr_png: Optional[bytes]) -> bool:
    if not settings.sendgrid_api_key:
        return False
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import (
            Attachment,
            Disposition,
            FileContent,
            FileName,
            FileType,
            Mail,
            ContentId,
        )

        message = Mail(
            from_email=(settings.sendgrid_from_email, settings.sendgrid_from_name),
            to_emails=to,
            subject=asunto,
            html_content=html,
        )
        if qr_png:
            att = Attachment(
                FileContent(base64.b64encode(qr_png).decode()),
                FileName("qr.png"),
                FileType("image/png"),
                Disposition("inline"),
            )
            att.content_id = ContentId("qrimg")
            message.attachment = att

        client = SendGridAPIClient(settings.sendgrid_api_key)
        resp = client.send(message)
        return 200 <= resp.status_code < 300
    except Exception as e:  # noqa: BLE001
        logger.warning("SendGrid falló: %s", e)
        return False


def _enviar_smtp(to: str, asunto: str, html: str, qr_png: Optional[bytes]) -> bool:
    if not (settings.smtp_server and settings.smtp_user and settings.smtp_password):
        return False
    try:
        root = MIMEMultipart("related")
        root["Subject"] = asunto
        root["From"] = f"{settings.sendgrid_from_name} <{settings.smtp_user}>"
        root["To"] = to

        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText("Abre este correo en formato HTML.", "plain"))
        alt.attach(MIMEText(html, "html"))
        root.attach(alt)

        if qr_png:
            img = MIMEImage(qr_png, _subtype="png")
            img.add_header("Content-ID", "<qrimg>")
            img.add_header("Content-Disposition", "inline", filename="qr.png")
            root.attach(img)

        with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, [to], root.as_string())
        return True
    except Exception as e:  # noqa: BLE001
        logger.warning("SMTP falló: %s", e)
        return False


def _enviar(to: str, asunto: str, html: str, qr_png: Optional[bytes]) -> bool:
    if _enviar_sendgrid(to, asunto, html, qr_png):
        return True
    return _enviar_smtp(to, asunto, html, qr_png)


# ---------------- API pública del módulo ----------------
def enviar_cupon(to: str, nombre: str, code: str, qr_png: bytes) -> bool:
    return _enviar(to, "🎁 Tu cupón 10% — Tienda Pintuco Cerritos",
                   _html_cupon(nombre, code), qr_png)


def enviar_premio(to: str, nombre: str, premio: str, qr_png: bytes) -> bool:
    return _enviar(to, "🏆 ¡Ganaste! — Tienda Pintuco Cerritos",
                   _html_premio(nombre, premio), qr_png)
