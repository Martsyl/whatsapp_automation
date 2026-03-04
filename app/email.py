import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────────
# SHARED HELPERS
# ─────────────────────────────────────────────

def _smtp_send(to_email, subject, body_html):
    """Core send function shared by all email helpers."""
    if not os.getenv("MAIL_USERNAME") or not os.getenv("MAIL_PASSWORD"):
        print("Email skipped — credentials not configured")
        return False

    try:
        msg            = MIMEMultipart('alternative')
        msg['From']    = f"{os.getenv('MAIL_FROM_NAME', 'BotMart')} <{os.getenv('MAIL_FROM')}>"
        msg['To']      = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body_html, 'html'))

        server = smtplib.SMTP(os.getenv("MAIL_SERVER"), int(os.getenv("MAIL_PORT", 587)))
        server.starttls()
        server.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
        server.sendmail(os.getenv("MAIL_FROM"), to_email, msg.as_string())
        server.quit()
        return True

    except Exception as e:
        print(f"Email send failed: {e}")
        return False


def _header(title, subtitle):
    """Green gradient header banner — same across all emails."""
    return """
    <tr>
      <td style="background:linear-gradient(135deg,#064e3b 0%,#065f46 40%,#047857 70%,#059669 100%);
        padding:0;height:110px;overflow:hidden;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
          style="height:110px;">
          <tr>
            <td style="padding:0 32px;vertical-align:middle;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="vertical-align:middle;">
                    <table cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="background:rgba(255,255,255,0.18);border-radius:10px;
                          padding:7px 14px;vertical-align:middle;">
                          <span style="font-size:20px;vertical-align:middle;">&#x1F4AC;</span>
                          <span style="color:#ffffff;font-size:20px;font-weight:800;
                            vertical-align:middle;margin-left:8px;
                            font-family:Arial,sans-serif;">BotMart</span>
                        </td>
                      </tr>
                    </table>
                    <p style="color:#ffffff;font-size:18px;font-weight:700;
                      margin:12px 0 4px;font-family:Arial,sans-serif;">
                      __TITLE__
                    </p>
                    <p style="color:rgba(255,255,255,0.75);font-size:13px;
                      margin:0;font-family:Arial,sans-serif;">
                      __SUBTITLE__
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>""".replace('__TITLE__', title).replace('__SUBTITLE__', subtitle)


def _subject_bar(text):
    """Centered subject title bar with green underline."""
    return """
    <tr>
      <td style="background:#f9fafb;border-bottom:2px solid #059669;
        padding:16px 32px;text-align:center;">
        <p style="margin:0;font-size:14px;font-weight:700;color:#111827;
          letter-spacing:0.5px;text-transform:uppercase;
          font-family:Arial,sans-serif;">__TEXT__</p>
      </td>
    </tr>""".replace('__TEXT__', text)


def _security_notice():
    """Yellow security notice box — same across all emails."""
    return """
    <tr>
      <td style="background:#fefce8;border-top:1px solid #fde68a;
        border-bottom:1px solid #fde68a;padding:14px 32px;">
        <p style="margin:0 0 4px;font-size:11px;font-weight:700;
          color:#92400e;font-family:Arial,sans-serif;letter-spacing:0.5px;">
          SECURITY NOTICE
        </p>
        <p style="margin:0;font-size:12px;color:#78350f;
          font-family:Arial,sans-serif;line-height:1.6;">
          BotMart will <strong>NEVER</strong> ask for your password or payment
          details via email. If you did not request this email, please ignore it
          or contact us immediately.
        </p>
      </td>
    </tr>"""


def _footer():
    """Standard footer with links."""
    base_url = os.getenv('BASE_URL', 'http://localhost:8001')
    whatsapp = os.getenv('SUPPORT_WHATSAPP', '2348000000000')

    return """
    <tr>
      <td style="background:#ffffff;padding:20px 32px;border-top:1px solid #e5e7eb;">
        <p style="margin:0 0 8px;font-size:11px;font-weight:700;
          color:#111827;font-family:Arial,sans-serif;letter-spacing:0.5px;">
          WAYS TO REACH US
        </p>
        <p style="margin:0 0 12px;font-size:12px;color:#6b7280;
          font-family:Arial,sans-serif;line-height:1.6;">
          For support, visit your dashboard or chat with us on WhatsApp.
          We respond within minutes during business hours (Mon&ndash;Fri, 9am&ndash;6pm WAT).
        </p>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="vertical-align:middle;">
              <a href="__WA_LINK__"
                style="display:inline-block;background:#25d366;border-radius:4px;
                padding:8px 16px;color:#ffffff;font-family:Arial,sans-serif;
                font-size:12px;font-weight:700;text-decoration:none;">
                &#x1F4AC; WhatsApp Us
              </a>
            </td>
            <td style="text-align:right;vertical-align:middle;">
              <table cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="padding:0 3px;">
                    <a href="https://facebook.com/botmart"
                      style="display:inline-block;background:#1877f2;border-radius:50%;
                      width:28px;height:28px;text-align:center;line-height:28px;
                      text-decoration:none;color:#fff;font-size:12px;font-weight:700;
                      font-family:Arial,sans-serif;">f</a>
                  </td>
                  <td style="padding:0 3px;">
                    <a href="__WA_LINK__"
                      style="display:inline-block;background:#25d366;border-radius:50%;
                      width:28px;height:28px;text-align:center;line-height:28px;
                      text-decoration:none;color:#fff;font-size:12px;
                      font-family:Arial,sans-serif;">&#x1F4AC;</a>
                  </td>
                  <td style="padding:0 3px;">
                    <a href="https://twitter.com/botmart"
                      style="display:inline-block;background:#000;border-radius:50%;
                      width:28px;height:28px;text-align:center;line-height:28px;
                      text-decoration:none;color:#fff;font-size:11px;font-weight:700;
                      font-family:Arial,sans-serif;">X</a>
                  </td>
                  <td style="padding:0 3px;">
                    <a href="https://instagram.com/botmart"
                      style="display:inline-block;background:#e1306c;border-radius:50%;
                      width:28px;height:28px;text-align:center;line-height:28px;
                      text-decoration:none;color:#fff;font-size:10px;font-weight:700;
                      font-family:Arial,sans-serif;">IG</a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    <tr>
      <td style="background:#f3f4f6;border-top:1px solid #e5e7eb;
        padding:18px 32px;text-align:center;">
        <p style="margin:0 0 6px;font-size:11px;color:#6b7280;
          font-family:Arial,sans-serif;">
          &copy; 2026 BotMart &mdash; WhatsApp Automation for Every Business.
          Lagos, Nigeria.
        </p>
        <p style="margin:0;">
          <a href="__BASE_URL__/unsubscribe/"
            style="color:#6b7280;font-size:11px;font-family:Arial,sans-serif;
            text-decoration:underline;">Unsubscribe</a>
          <span style="color:#d1d5db;padding:0 6px;">|</span>
          <a href="__BASE_URL__/privacy/"
            style="color:#6b7280;font-size:11px;font-family:Arial,sans-serif;
            text-decoration:underline;">Privacy Policy</a>
          <span style="color:#d1d5db;padding:0 6px;">|</span>
          <a href="__BASE_URL__"
            style="color:#6b7280;font-size:11px;font-family:Arial,sans-serif;
            text-decoration:underline;">botmart.app</a>
        </p>
      </td>
    </tr>""".replace('__WA_LINK__', f'https://wa.me/{whatsapp}').replace('__BASE_URL__', base_url)


def _wrap(inner_rows):
    """Wraps header/body/footer rows in the outer card shell."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
</head>
<body style="margin:0;padding:0;background:#e8e8e8;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
    style="background:#e8e8e8;padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
          style="max-width:580px;background:#ffffff;border-radius:4px;
          overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.12);">
          {inner_rows}
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _data_table(rows):
    """
    Renders a striped data table.
    rows = list of (label, value) tuples
    """
    header = """
    <tr>
      <td colspan="2" style="background:#f3f4f6;padding:10px 16px;
        border-bottom:1px solid #d1d5db;">
        <strong style="font-size:12px;color:#111827;font-family:Arial,sans-serif;
          letter-spacing:0.3px;">DETAILS</strong>
      </td>
    </tr>"""

    cells = ""
    for i, (label, value) in enumerate(rows):
        border = "border-bottom:1px solid #e5e7eb;" if i < len(rows) - 1 else ""
        cells += f"""
        <tr>
          <td style="padding:11px 16px;font-size:13px;font-weight:600;
            color:#374151;font-family:Arial,sans-serif;width:45%;
            background:#fafafa;{border}">{label}</td>
          <td style="padding:11px 16px;font-size:13px;color:#111827;
            font-family:Arial,sans-serif;{border}">{value}</td>
        </tr>"""

    return f"""
    <tr>
      <td style="padding:0 32px 28px;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
          style="border:1px solid #d1d5db;border-radius:6px;overflow:hidden;
          margin-top:24px;">
          {header}
          {cells}
        </table>
      </td>
    </tr>"""


# ─────────────────────────────────────────────
# 1. HUMAN HANDOFF NOTIFICATION
# ─────────────────────────────────────────────

def send_email_notification(to_email, business_name, sender_number, message_text):
    """Alert business owner that a customer requested a human agent."""
    subject = f"Customer Needs Attention — {business_name}"

    body = _wrap(
        _header("&#x1F514; Customer Needs Attention",
                "A customer has requested to speak with a human agent") +
        _subject_bar("Human Handoff Request") +
        f"""
        <tr>
          <td style="padding:28px 32px 8px;">
            <p style="margin:0 0 6px;font-size:15px;color:#111827;
              font-family:Arial,sans-serif;">
              Dear <strong>{business_name}</strong>,
            </p>
            <p style="margin:0;font-size:14px;color:#4b5563;
              font-family:Arial,sans-serif;line-height:1.7;">
              One of your customers has requested to speak with a human agent.
              Please follow up as soon as possible.
            </p>
          </td>
        </tr>""" +
        _data_table([
            ("Business",         business_name),
            ("Customer Number",  sender_number),
            ("Last Message",     message_text),
            ("Action Required",  "<strong style='color:#b45309;'>Follow up immediately</strong>"),
        ]) +
        _security_notice() +
        _footer()
    )

    result = _smtp_send(to_email, subject, body)
    if result:
        print(f"✅ Handoff notification sent to {to_email}")
    return result


# ─────────────────────────────────────────────
# 2. PASSWORD RESET
# ─────────────────────────────────────────────

def send_password_reset_email(to_email, business_name, reset_link):
    """Send password reset link email."""
    subject = "Password Reset Request — BotMart"

    body = _wrap(
        _header("&#x1F510; Password Reset",
                "You requested a password reset for your BotMart account") +
        _subject_bar("Password Reset Request") +
        f"""
        <tr>
          <td style="padding:28px 32px 8px;">
            <p style="margin:0 0 16px;font-size:15px;color:#111827;
              font-family:Arial,sans-serif;">
              Dear <strong>{business_name}</strong>,
            </p>
            <p style="margin:0 0 24px;font-size:14px;color:#4b5563;
              font-family:Arial,sans-serif;line-height:1.7;">
              We received a request to reset the password for your BotMart account.
              Click the button below to set a new password. This link expires in
              <strong>1 hour</strong>.
            </p>
            <table cellpadding="0" cellspacing="0" border="0" style="margin-bottom:24px;">
              <tr>
                <td style="background:#065f46;border-radius:4px;">
                  <a href="{reset_link}"
                    style="display:inline-block;padding:13px 32px;color:#ffffff;
                    font-family:Arial,sans-serif;font-size:14px;font-weight:700;
                    text-decoration:none;letter-spacing:0.5px;">
                    RESET MY PASSWORD &rarr;
                  </a>
                </td>
              </tr>
            </table>
            <p style="margin:0 0 6px;font-size:12px;color:#9ca3af;
              font-family:Arial,sans-serif;line-height:1.6;">
              Or copy and paste this link into your browser:
            </p>
            <p style="margin:0 0 24px;font-size:12px;font-family:Arial,sans-serif;">
              <a href="{reset_link}" style="color:#065f46;word-break:break-all;">
                {reset_link}
              </a>
            </p>
            <p style="margin:0;font-size:13px;color:#9ca3af;
              font-family:Arial,sans-serif;line-height:1.6;">
              If you did not request a password reset, please ignore this email —
              your password will not change.
            </p>
          </td>
        </tr>
        <tr><td style="padding:0 32px 28px;"></td></tr>""" +
        _security_notice() +
        _footer()
    )

    result = _smtp_send(to_email, subject, body)
    if result:
        print(f"✅ Password reset email sent to {to_email}")
    return result


# ─────────────────────────────────────────────
# 3. REGISTRATION CONFIRMATION
# ─────────────────────────────────────────────

def send_registration_email(to_email, business_name):
    """Send confirmation email immediately after registration."""
    subject = "Registration Received — BotMart"

    body = _wrap(
        _header("&#x1F44B; Welcome to BotMart!",
                "We have received your registration") +
        _subject_bar("Registration Confirmation") +
        f"""
        <tr>
          <td style="padding:28px 32px 8px;">
            <p style="margin:0 0 16px;font-size:15px;color:#111827;
              font-family:Arial,sans-serif;">
              Dear <strong>{business_name}</strong>,
            </p>
            <p style="margin:0 0 20px;font-size:14px;color:#4b5563;
              font-family:Arial,sans-serif;line-height:1.7;">
              Thank you for registering on BotMart. We have received your details
              and payment. Our team is currently reviewing your Meta credentials
              and will activate your account within <strong>2&ndash;4 hours</strong>.
            </p>
          </td>
        </tr>""" +
        _data_table([
            ("Business Name", business_name),
            ("Email",         to_email),
            ("Status",        "<span style='background:#fef9c3;color:#854d0e;font-size:12px;"
                              "font-weight:700;padding:3px 10px;border-radius:100px;'>"
                              "PENDING ACTIVATION</span>"),
            ("Est. Time",     "2 &ndash; 4 hours"),
        ]) +
        f"""
        <tr>
          <td style="padding:0 32px 28px;">
            <p style="margin:0 0 10px;font-size:13px;font-weight:700;color:#111827;
              font-family:Arial,sans-serif;letter-spacing:0.3px;">
              WHAT HAPPENS NEXT
            </p>
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
              style="background:#f0fdf4;border-radius:6px;border:1px solid #bbf7d0;">
              <tr>
                <td style="padding:16px 20px;">
                  <p style="margin:0;font-size:13px;color:#166534;
                    font-family:Arial,sans-serif;line-height:2;">
                    &#x2713;&nbsp; We verify your Meta credentials<br/>
                    &#x2713;&nbsp; We activate your WhatsApp bot<br/>
                    &#x2713;&nbsp; You receive an activation email<br/>
                    &#x2713;&nbsp; You log in and set up your bot
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>""" +
        _security_notice() +
        _footer()
    )

    result = _smtp_send(to_email, subject, body)
    if result:
        print(f"✅ Registration email sent to {to_email}")
    return result


# ─────────────────────────────────────────────
# 4. ACCOUNT ACTIVATION
# ─────────────────────────────────────────────

def send_activation_email(to_email, business_name):
    """Send email when admin activates a client account."""
    subject = "Your BotMart Account is Now Live!"
    base_url = os.getenv('BASE_URL', 'http://localhost:8001')

    body = _wrap(
        _header("&#x1F680; You're Live on BotMart!",
                "Your WhatsApp bot is now active and ready") +
        _subject_bar("Account Activation Confirmation") +
        f"""
        <tr>
          <td style="padding:28px 32px 8px;">
            <p style="margin:0 0 16px;font-size:15px;color:#111827;
              font-family:Arial,sans-serif;">
              Dear <strong>{business_name}</strong>,
            </p>
            <p style="margin:0 0 24px;font-size:14px;color:#4b5563;
              font-family:Arial,sans-serif;line-height:1.7;">
              Your WhatsApp bot is now active and ready to serve your customers.
              Log in to your dashboard to set up auto-replies, add products
              and customise your bot.
            </p>
            <table cellpadding="0" cellspacing="0" border="0" style="margin-bottom:24px;">
              <tr>
                <td style="background:#065f46;border-radius:4px;">
                  <a href="{base_url}/login/"
                    style="display:inline-block;padding:13px 32px;color:#ffffff;
                    font-family:Arial,sans-serif;font-size:14px;font-weight:700;
                    text-decoration:none;letter-spacing:0.5px;">
                    LOG IN TO DASHBOARD &rarr;
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>""" +
        _data_table([
            ("Business Name", business_name),
            ("Status",        "<span style='background:#dcfce7;color:#166534;font-size:12px;"
                              "font-weight:700;padding:3px 10px;border-radius:100px;'>"
                              "ACTIVE</span>"),
            ("Platform",      "BotMart WhatsApp Automation"),
            ("Dashboard",     f"<a href='{base_url}/login/' style='color:#065f46;'>"
                              f"{base_url}/login/</a>"),
        ]) +
        _security_notice() +
        _footer()
    )

    result = _smtp_send(to_email, subject, body)
    if result:
        print(f"✅ Activation email sent to {to_email}")
    return result