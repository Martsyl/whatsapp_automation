from datetime import date
from app.database import SessionLocal
from app.models import Client

# ── Import Django's email helper via direct SMTP call ──
# FastAPI doesn't use Django, so we send emails directly with smtplib
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_reminder_email(to_email: str, business_name: str, days_left: int, plan: str):
    """Send a subscription expiry reminder email."""
    smtp_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("EMAIL_PORT", 587))
    smtp_user = os.getenv("EMAIL_HOST_USER", "")
    smtp_pass = os.getenv("EMAIL_HOST_PASSWORD", "")
    from_email = os.getenv("DEFAULT_FROM_EMAIL", smtp_user)
    app_name   = os.getenv("APP_NAME", "BotMart")
    app_url    = os.getenv("BASE_URL", "http://localhost:8001")

    if days_left > 0:
        subject = f"⚠️ Your {app_name} subscription expires in {days_left} day{'s' if days_left != 1 else ''}"
        urgency_color = "#f59e0b" if days_left > 3 else "#dc3545"
        urgency_msg   = f"Your subscription expires in <strong>{days_left} day{'s' if days_left != 1 else ''}</strong>."
        cta_text      = "Renew Now"
    else:
        subject = f"❌ Your {app_name} subscription has expired"
        urgency_color = "#dc3545"
        urgency_msg   = "Your subscription has <strong>expired</strong>. Your bot is now paused."
        cta_text      = "Reactivate Now"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta name="color-scheme" content="light"/></head>
    <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" bgcolor="#f4f4f4">
        <tr><td align="center" style="padding:32px 16px;">
          <table width="600" cellpadding="0" cellspacing="0"
                 style="max-width:600px;width:100%;background:#ffffff;
                        border-radius:12px;overflow:hidden;
                        border:1px solid #e5e7eb;">

            <!-- Header -->
            <tr>
              <td bgcolor="#065f46" style="padding:28px 32px;">
                <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;">
                  {app_name}
                </h1>
                <p style="margin:4px 0 0;color:#a7f3d0;font-size:13px;">
                  WhatsApp Automation Platform
                </p>
              </td>
            </tr>

            <!-- Alert banner -->
            <tr>
              <td bgcolor="{urgency_color}" style="padding:12px 32px;">
                <p style="margin:0;color:#ffffff;font-size:14px;font-weight:600;">
                  {'⚠️ Subscription Expiring Soon' if days_left > 0 else '❌ Subscription Expired'}
                </p>
              </td>
            </tr>

            <!-- Body -->
            <tr>
              <td style="padding:32px;">
                <p style="margin:0 0 16px;font-size:16px;color:#111827;">
                  Hi <strong>{business_name}</strong>,
                </p>
                <p style="margin:0 0 24px;font-size:15px;color:#374151;line-height:1.6;">
                  {urgency_msg} Renew your <strong>{plan.title()} Plan</strong>
                  to keep your WhatsApp bot running without interruption.
                </p>

                <!-- CTA -->
                <table cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                  <tr>
                    <td bgcolor="#065f46"
                        style="border-radius:8px;padding:14px 28px;">
                      <a href="{app_url}/renew/"
                         style="color:#ffffff;font-size:15px;
                                font-weight:600;text-decoration:none;">
                        {cta_text} →
                      </a>
                    </td>
                  </tr>
                </table>

                <p style="margin:0;font-size:13px;color:#9ca3af;">
                  If you have any questions, reply to this email or contact our support team.
                </p>
              </td>
            </tr>

            <!-- Footer -->
            <tr>
              <td bgcolor="#f9fafb"
                  style="padding:20px 32px;border-top:1px solid #e5e7eb;">
                <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
                  © {app_name} · You're receiving this because your account is registered with us.
                </p>
              </td>
            </tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{app_name} <{from_email}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to_email, msg.as_string())

        print(f"[subscription_checker] Reminder sent to {to_email} ({days_left}d left)")
    except Exception as e:
        print(f"[subscription_checker] Failed to send email to {to_email}: {e}")


def send_expired_bot_paused_email(to_email: str, business_name: str, plan: str):
    """Notify client their bot has been paused due to expiry."""
    smtp_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("EMAIL_PORT", 587))
    smtp_user = os.getenv("EMAIL_HOST_USER", "")
    smtp_pass = os.getenv("EMAIL_HOST_PASSWORD", "")
    from_email = os.getenv("DEFAULT_FROM_EMAIL", smtp_user)
    app_name   = os.getenv("APP_NAME", "BotMart")
    app_url    = os.getenv("BASE_URL", "http://localhost:8001")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta name="color-scheme" content="light"/></head>
    <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" bgcolor="#f4f4f4">
        <tr><td align="center" style="padding:32px 16px;">
          <table width="600" cellpadding="0" cellspacing="0"
                 style="max-width:600px;width:100%;background:#ffffff;
                        border-radius:12px;overflow:hidden;
                        border:1px solid #e5e7eb;">
            <tr>
              <td bgcolor="#065f46" style="padding:28px 32px;">
                <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;">
                  {app_name}
                </h1>
              </td>
            </tr>
            <tr>
              <td bgcolor="#dc3545" style="padding:12px 32px;">
                <p style="margin:0;color:#ffffff;font-size:14px;font-weight:600;">
                  🤖 Your bot has been paused
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:32px;">
                <p style="margin:0 0 16px;font-size:16px;color:#111827;">
                  Hi <strong>{business_name}</strong>,
                </p>
                <p style="margin:0 0 24px;font-size:15px;color:#374151;line-height:1.6;">
                  Your <strong>{plan.title()} Plan</strong> has expired and your
                  WhatsApp bot has been <strong>paused</strong>.
                  Your contacts will no longer receive automated replies until you renew.
                </p>
                <table cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                  <tr>
                    <td bgcolor="#065f46" style="border-radius:8px;padding:14px 28px;">
                      <a href="{app_url}/renew/"
                         style="color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;">
                        Reactivate My Bot →
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td bgcolor="#f9fafb" style="padding:20px 32px;border-top:1px solid #e5e7eb;">
                <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
                  © {app_name}
                </p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🤖 Your {app_name} bot has been paused"
        msg["From"]    = f"{app_name} <{from_email}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to_email, msg.as_string())

        print(f"[subscription_checker] Bot-paused email sent to {to_email}")
    except Exception as e:
        print(f"[subscription_checker] Failed to send paused email to {to_email}: {e}")


def run_subscription_checks():
    """
    Runs daily at 8am via APScheduler.

    Actions:
    - 7 days before expiry  → send reminder (once)
    - 3 days before expiry  → send urgent reminder (once)
    - On expiry day         → pause bot (set payment_status = 'expired')
    - After grace period    → deactivate client
    """
    db    = SessionLocal()
    today = date.today()

    try:
        clients = db.query(Client).filter(
            Client.payment_status == "paid",
            Client.subscription_end != None
        ).all()

        for client in clients:
            days_left = (client.subscription_end - today).days

            # ── 7-day reminder ──
            if days_left == 7 and not client.reminder_7_sent:
                send_reminder_email(
                    client.email, client.business_name,
                    days_left=7, plan=client.plan
                )
                client.reminder_7_sent = True
                db.commit()
                print(f"[checker] 7-day reminder → {client.business_name}")

            # ── 3-day reminder ──
            elif days_left == 3 and not client.reminder_3_sent:
                send_reminder_email(
                    client.email, client.business_name,
                    days_left=3, plan=client.plan
                )
                client.reminder_3_sent = True
                db.commit()
                print(f"[checker] 3-day reminder → {client.business_name}")

            # ── Expired today — pause bot ──
            elif days_left <= 0 and client.payment_status == "paid":
                client.payment_status = "expired"
                db.commit()
                send_expired_bot_paused_email(
                    client.email, client.business_name, client.plan
                )
                print(f"[checker] Bot paused → {client.business_name}")

        # ── Grace period over — deactivate ──
        expired_clients = db.query(Client).filter(
            Client.payment_status == "expired",
            Client.grace_period_end != None,
            Client.grace_period_end < today,
            Client.is_active == True
        ).all()

        for client in expired_clients:
            client.is_active = False
            db.commit()
            print(f"[checker] Deactivated (grace over) → {client.business_name}")

    except Exception as e:
        print(f"[subscription_checker] Error: {e}")
    finally:
        db.close()