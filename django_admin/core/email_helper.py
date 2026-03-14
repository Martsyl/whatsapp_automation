import os
import requests as http_requests
from dotenv import load_dotenv
from datetime import date
load_dotenv()


# ─────────────────────────────────────────────
# CORE RESEND SENDER
# ─────────────────────────────────────────────

def _smtp_send(to_email, subject, body_html):
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("Email skipped — RESEND_API_KEY not configured")
        return False
    try:
        from_name  = os.getenv("MAIL_FROM_NAME", "BotMart")
        from_email = os.getenv("MAIL_FROM", "noreply@botmart.app")
        response = http_requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": f"{from_name} <{from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": body_html,
            },
            timeout=15
        )
        if response.status_code in (200, 201):
            return True
        else:
            print(f"Resend error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Email send failed: {e}")
        return False


# ─────────────────────────────────────────────
# SHARED TEMPLATE BUILDER
# ─────────────────────────────────────────────

def _build_email(header_icon, header_title, header_subtitle, subject_bar, body_content):
    """
    Builds a professional, dark-mode-safe HTML email.
    Uses data-ogsc / !important overrides to force light mode in Gmail dark mode.
    """
    base_url = os.getenv('BASE_URL', 'http://localhost:8001')
    whatsapp = os.getenv('SUPPORT_WHATSAPP', '2348000000000')

    # Use __PLACEHOLDER__ to avoid f-string CSS brace issues
    html = """<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <meta name="color-scheme" content="light"/>
  <meta name="supported-color-schemes" content="light"/>
  <title>__SUBJECT_BAR__</title>
  <style>
    /* Force light mode in ALL email clients */
    :root { color-scheme: light only; }

    body {
      margin: 0 !important;
      padding: 0 !important;
      background-color: #f4f4f4 !important;
      -webkit-text-size-adjust: 100%;
    }

    /* Gmail dark mode overrides */
    [data-ogsc] body,
    [data-ogsb] body,
    u + .body,
    .gmail-dark-mode body {
      background-color: #f4f4f4 !important;
    }

    [data-ogsc] .email-card,
    u + .body .email-card {
      background-color: #ffffff !important;
    }

    [data-ogsc] .email-body-cell,
    u + .body .email-body-cell {
      background-color: #ffffff !important;
      color: #333333 !important;
    }

    [data-ogsc] .email-footer-cell,
    u + .body .email-footer-cell {
      background-color: #f8f8f8 !important;
    }

    [data-ogsc] p,
    [data-ogsc] td,
    [data-ogsc] span,
    u + .body p,
    u + .body td,
    u + .body span {
      color: inherit !important;
    }

    @media only screen and (max-width: 600px) {
      .email-card { width: 100% !important; }
      .email-header { padding: 28px 20px !important; }
      .email-body-cell { padding: 24px 20px !important; }
      .email-footer-cell { padding: 16px 20px !important; }
    }
  </style>
</head>

<!--[if mso]>
<body class="body" style="background-color:#f4f4f4;">
<![endif]-->
<body class="body" style="margin:0;padding:0;background-color:#f4f4f4;
  font-family:Arial,Helvetica,sans-serif;-webkit-text-size-adjust:100%;">

  <table width="100%" cellpadding="0" cellspacing="0" border="0" role="presentation"
    style="background-color:#f4f4f4;padding:32px 16px;">
    <tr>
      <td align="center">

        <!-- Wrapper card -->
        <table class="email-card" width="580" cellpadding="0" cellspacing="0"
          border="0" role="presentation"
          style="max-width:580px;width:100%;background-color:#ffffff;
          border-radius:6px;overflow:hidden;
          box-shadow:0 1px 8px rgba(0,0,0,0.10);">

          <!-- ══════════════ HEADER ══════════════ -->
          <tr>
            <td class="email-header" bgcolor="#065f46"
              style="background-color:#065f46 !important;padding:32px 40px;">

              <!-- Logo row -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="vertical-align:middle;">
                    <table cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td bgcolor="#ffffff" style="background-color:#ffffff;
                          border-radius:8px;padding:6px 12px;vertical-align:middle;">
                          <span style="font-size:16px;vertical-align:middle;">&#x1F4AC;</span>
                          <span style="color:#065f46;font-size:15px;font-weight:700;
                            vertical-align:middle;margin-left:6px;
                            font-family:Arial,sans-serif;">BotMart</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td style="text-align:right;vertical-align:middle;">
                    <span style="color:rgba(255,255,255,0.65);font-size:11px;
                      font-family:Arial,sans-serif;font-style:italic;">
                      WhatsApp Automation
                    </span>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <div style="border-top:1px solid rgba(255,255,255,0.2);margin:20px 0 16px;"></div>

              <!-- Title -->
              <p style="margin:0 0 4px;font-size:22px;font-weight:700;
                color:#ffffff !important;font-family:Arial,sans-serif;line-height:1.3;">
                __ICON__ __TITLE__
              </p>
              <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.75) !important;
                font-family:Arial,sans-serif;">
                __SUBTITLE__
              </p>
            </td>
          </tr>

          <!-- Subject bar -->
          <tr>
            <td bgcolor="#f0fdf4" style="background-color:#f0fdf4 !important;
              padding:12px 40px;border-bottom:2px solid #065f46;
              border-top:1px solid #d1fae5;text-align:center;">
              <p style="margin:0;font-size:13px;font-weight:700;
                color:#064e3b !important;letter-spacing:0.8px;
                text-transform:uppercase;font-family:Arial,sans-serif;">
                __SUBJECT_BAR__
              </p>
            </td>
          </tr>

          <!-- ══════════════ BODY ══════════════ -->
          <tr>
            <td class="email-body-cell" bgcolor="#ffffff"
              style="background-color:#ffffff !important;
              padding:32px 40px;color:#333333 !important;">
              __BODY_CONTENT__
            </td>
          </tr>

          <!-- ══════════════ SECURITY NOTICE ══════════════ -->
          <tr>
            <td bgcolor="#fffbeb" style="background-color:#fffbeb !important;
              padding:14px 40px;border-top:1px solid #fde68a;
              border-bottom:1px solid #fde68a;">
              <p style="margin:0 0 4px;font-size:11px;font-weight:700;
                color:#92400e !important;letter-spacing:0.5px;
                font-family:Arial,sans-serif;text-transform:uppercase;">
                Security Notice
              </p>
              <p style="margin:0;font-size:12px;color:#78350f !important;
                font-family:Arial,sans-serif;line-height:1.6;">
                BotMart will <strong>NEVER</strong> ask for your password or
                payment details via email or WhatsApp. If you did not request
                this email, please ignore it or contact us immediately.
              </p>
            </td>
          </tr>

          <!-- ══════════════ FOOTER ══════════════ -->
          <tr>
            <td class="email-footer-cell" bgcolor="#f8f8f8"
              style="background-color:#f8f8f8 !important;padding:24px 40px;">

              <!-- Ways to reach us -->
              <p style="margin:0 0 6px;font-size:11px;font-weight:700;
                color:#333333 !important;letter-spacing:0.5px;
                font-family:Arial,sans-serif;text-transform:uppercase;">
                Ways to Reach Us
              </p>
              <p style="margin:0 0 14px;font-size:12px;color:#666666 !important;
                font-family:Arial,sans-serif;line-height:1.6;">
                For support, visit your dashboard or chat with us on WhatsApp.
                We respond within minutes during business hours (Mon&ndash;Fri, 9am&ndash;6pm WAT).
              </p>

              <!-- WhatsApp + Social -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="vertical-align:middle;">
                    <a href="__WA_LINK__"
                      style="display:inline-block;background-color:#25d366;
                      border-radius:4px;padding:8px 16px;color:#ffffff !important;
                      font-family:Arial,sans-serif;font-size:12px;font-weight:700;
                      text-decoration:none;">
                      &#x1F4AC; WhatsApp Us
                    </a>
                  </td>
                  <td style="text-align:right;vertical-align:middle;">
                    <table cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="padding:0 3px;">
                          <a href="https://facebook.com/botmart"
                            style="display:inline-block;background-color:#1877f2;
                            border-radius:50%;width:28px;height:28px;
                            text-align:center;line-height:28px;text-decoration:none;
                            color:#ffffff !important;font-size:12px;font-weight:700;
                            font-family:Arial,sans-serif;">f</a>
                        </td>
                        <td style="padding:0 3px;">
                          <a href="https://twitter.com/botmart"
                            style="display:inline-block;background-color:#000000;
                            border-radius:50%;width:28px;height:28px;
                            text-align:center;line-height:28px;text-decoration:none;
                            color:#ffffff !important;font-size:11px;font-weight:700;
                            font-family:Arial,sans-serif;">X</a>
                        </td>
                        <td style="padding:0 3px;">
                          <a href="https://instagram.com/botmart"
                            style="display:inline-block;background-color:#e1306c;
                            border-radius:50%;width:28px;height:28px;
                            text-align:center;line-height:28px;text-decoration:none;
                            color:#ffffff !important;font-size:10px;font-weight:700;
                            font-family:Arial,sans-serif;">IG</a>
                        </td>
                        <td style="padding:0 3px;">
                          <a href="https://linkedin.com/company/botmart"
                            style="display:inline-block;background-color:#0077b5;
                            border-radius:50%;width:28px;height:28px;
                            text-align:center;line-height:28px;text-decoration:none;
                            color:#ffffff !important;font-size:10px;font-weight:700;
                            font-family:Arial,sans-serif;">in</a>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <div style="border-top:1px solid #e0e0e0;margin:18px 0;"></div>

              <!-- Copyright -->
              <p style="margin:0 0 6px;font-size:11px;color:#999999 !important;
                text-align:center;font-family:Arial,sans-serif;line-height:1.6;">
                &copy; 2026 BotMart &mdash; WhatsApp Automation for Every Business.
                Lagos, Nigeria.
              </p>
              <p style="margin:0;text-align:center;">
                <a href="__BASE_URL__/unsubscribe/"
                  style="color:#999999 !important;font-size:11px;
                  font-family:Arial,sans-serif;text-decoration:underline;">
                  Unsubscribe</a>
                <span style="color:#cccccc;padding:0 6px;">|</span>
                <a href="__BASE_URL__/privacy/"
                  style="color:#999999 !important;font-size:11px;
                  font-family:Arial,sans-serif;text-decoration:underline;">
                  Privacy Policy</a>
                <span style="color:#cccccc;padding:0 6px;">|</span>
                <a href="__BASE_URL__"
                  style="color:#999999 !important;font-size:11px;
                  font-family:Arial,sans-serif;text-decoration:underline;">
                  botmart.app</a>
              </p>
            </td>
          </tr>

        </table>

      </td>
    </tr>
  </table>

</body>
</html>"""

    html = html.replace('__WA_LINK__',  f'https://wa.me/{whatsapp}')
    html = html.replace('__BASE_URL__', base_url)
    html = html.replace('__ICON__',     header_icon)
    html = html.replace('__TITLE__',    header_title)
    html = html.replace('__SUBTITLE__', header_subtitle)
    html = html.replace('__SUBJECT_BAR__', subject_bar)
    html = html.replace('__BODY_CONTENT__', body_content)

    return html


def _details_table(rows):
    """Renders a clean striped details table. rows = list of (label, value)."""
    cells = ""
    for i, (label, value) in enumerate(rows):
        bg     = "#f9f9f9" if i % 2 == 0 else "#ffffff"
        border = "border-bottom:1px solid #eeeeee;" if i < len(rows) - 1 else ""
        cells += f"""
        <tr>
          <td bgcolor="{bg}" style="background-color:{bg} !important;
            padding:10px 14px;font-size:13px;font-weight:600;
            color:#444444 !important;font-family:Arial,sans-serif;
            width:42%;{border}">{label}</td>
          <td bgcolor="{bg}" style="background-color:{bg} !important;
            padding:10px 14px;font-size:13px;color:#222222 !important;
            font-family:Arial,sans-serif;{border}">{value}</td>
        </tr>"""

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0"
      style="border:1px solid #e0e0e0;border-radius:6px;
      overflow:hidden;margin:20px 0;">
      <tr>
        <td colspan="2" bgcolor="#f0f0f0"
          style="background-color:#f0f0f0 !important;
          padding:9px 14px;border-bottom:2px solid #065f46;">
          <strong style="font-size:11px;color:#333333 !important;
            font-family:Arial,sans-serif;letter-spacing:0.5px;
            text-transform:uppercase;">Details</strong>
        </td>
      </tr>
      {cells}
    </table>"""


def _cta_button(text, url):
    return f"""
    <table cellpadding="0" cellspacing="0" border="0" style="margin:24px 0 8px;">
      <tr>
        <td bgcolor="#065f46" style="background-color:#065f46;border-radius:4px;">
          <a href="{url}"
            style="display:inline-block;padding:12px 28px;color:#ffffff !important;
            font-family:Arial,sans-serif;font-size:14px;font-weight:700;
            text-decoration:none;letter-spacing:0.3px;">
            {text} &rarr;
          </a>
        </td>
      </tr>
    </table>"""


# ─────────────────────────────────────────────
# 1. HUMAN HANDOFF NOTIFICATION
# ─────────────────────────────────────────────

def send_email_notification(to_email, business_name, sender_number, message_text):
    subject = f"Customer Needs Attention — {business_name}"

    body = f"""
    <p style="margin:0 0 4px;font-size:15px;font-family:Arial,sans-serif;
      color:#222222 !important;">
      Dear <strong>{business_name}</strong>,
    </p>
    <p style="margin:0 0 16px;font-size:14px;color:#555555 !important;
      font-family:Arial,sans-serif;line-height:1.7;">
      One of your customers has requested to speak with a human agent.
      Please follow up as soon as possible.
    </p>
    """ + _details_table([
        ("Business",        business_name),
        ("Customer Number", sender_number),
        ("Last Message",    message_text),
        ("Action",          "<span style='color:#b45309;font-weight:700;'>"
                            "Follow up immediately</span>"),
    ]) + """
    <p style="margin:8px 0 0;font-size:13px;color:#888888 !important;
      font-family:Arial,sans-serif;line-height:1.6;">
      Log in to your dashboard to view the full conversation history.
    </p>"""

    html = _build_email(
        header_icon     = "&#x1F514;",
        header_title    = "Customer Needs Attention",
        header_subtitle = "A customer has requested to speak with a human agent",
        subject_bar     = "Human Handoff Request",
        body_content    = body
    )

    result = _smtp_send(to_email, subject, html)
    if result:
        print(f"✅ Handoff notification sent to {to_email}")
    return result


# ─────────────────────────────────────────────
# 2. PASSWORD RESET
# ─────────────────────────────────────────────

def send_password_reset_email(to_email, business_name, reset_link):
    subject = "Password Reset Request — BotMart"

    body = f"""
    <p style="margin:0 0 4px;font-size:15px;font-family:Arial,sans-serif;
      color:#222222 !important;">
      Dear <strong>{business_name}</strong>,
    </p>
    <p style="margin:0 0 20px;font-size:14px;color:#555555 !important;
      font-family:Arial,sans-serif;line-height:1.7;">
      We received a request to reset the password for your BotMart account.
      Click the button below to set a new password.
      This link expires in <strong>1 hour</strong>.
    </p>
    {_cta_button("Reset My Password", reset_link)}
    <p style="margin:20px 0 6px;font-size:12px;color:#999999 !important;
      font-family:Arial,sans-serif;">
      Or copy and paste this link into your browser:
    </p>
    <p style="margin:0 0 20px;font-size:12px;font-family:Arial,sans-serif;
      word-break:break-all;">
      <a href="{reset_link}" style="color:#065f46 !important;">{reset_link}</a>
    </p>
    <p style="margin:0;font-size:13px;color:#999999 !important;
      font-family:Arial,sans-serif;line-height:1.6;">
      If you did not request a password reset, please ignore this email —
      your password will not change.
    </p>"""

    html = _build_email(
        header_icon     = "&#x1F510;",
        header_title    = "Password Reset",
        header_subtitle = "You requested a password reset for your BotMart account",
        subject_bar     = "Password Reset Request",
        body_content    = body
    )

    result = _smtp_send(to_email, subject, html)
    if result:
        print(f"✅ Password reset email sent to {to_email}")
    return result


# ─────────────────────────────────────────────
# 3. REGISTRATION CONFIRMATION
# ─────────────────────────────────────────────

def send_registration_email(to_email, business_name):
    subject = "Registration Received — BotMart"

    body = f"""
    <p style="margin:0 0 4px;font-size:15px;font-family:Arial,sans-serif;
      color:#222222 !important;">
      Dear <strong>{business_name}</strong>,
    </p>
    <p style="margin:0 0 16px;font-size:14px;color:#555555 !important;
      font-family:Arial,sans-serif;line-height:1.7;">
      Thank you for registering on BotMart. We have received your details
      and payment. Our team is currently reviewing your Meta credentials
      and will activate your account within <strong>2&ndash;4 hours</strong>.
    </p>
    """ + _details_table([
        ("Business Name", business_name),
        ("Email",         to_email),
        ("Status",        "<span style='background-color:#fef9c3;color:#854d0e;"
                          "font-size:11px;font-weight:700;padding:3px 10px;"
                          "border-radius:100px;'>PENDING ACTIVATION</span>"),
        ("Est. Time",     "2 &ndash; 4 hours"),
    ]) + """
    <table width="100%" cellpadding="0" cellspacing="0" border="0"
      style="background-color:#f0fdf4;border-radius:6px;
      border:1px solid #bbf7d0;margin-top:4px;">
      <tr>
        <td style="padding:14px 18px;">
          <p style="margin:0 0 6px;font-size:11px;font-weight:700;
            color:#166534 !important;font-family:Arial,sans-serif;
            letter-spacing:0.5px;text-transform:uppercase;">
            What Happens Next
          </p>
          <p style="margin:0;font-size:13px;color:#166534 !important;
            font-family:Arial,sans-serif;line-height:2.1;">
            &#x2713;&nbsp; We verify your Meta credentials<br/>
            &#x2713;&nbsp; We activate your WhatsApp bot<br/>
            &#x2713;&nbsp; You receive an activation email<br/>
            &#x2713;&nbsp; You log in and set up your bot
          </p>
        </td>
      </tr>
    </table>"""

    html = _build_email(
        header_icon     = "&#x1F44B;",
        header_title    = "Welcome to BotMart!",
        header_subtitle = "We have received your registration",
        subject_bar     = "Registration Confirmation",
        body_content    = body
    )

    result = _smtp_send(to_email, subject, html)
    if result:
        print(f"✅ Registration email sent to {to_email}")
    return result


# ─────────────────────────────────────────────
# 4. ACCOUNT ACTIVATION
# ─────────────────────────────────────────────

def send_activation_email(to_email, business_name):
    subject  = "Your BotMart Account is Now Live!"
    base_url = os.getenv('BASE_URL', 'http://localhost:8001')

    body = f"""
    <p style="margin:0 0 4px;font-size:15px;font-family:Arial,sans-serif;
      color:#222222 !important;">
      Dear <strong>{business_name}</strong>,
    </p>
    <p style="margin:0 0 16px;font-size:14px;color:#555555 !important;
      font-family:Arial,sans-serif;line-height:1.7;">
      Your WhatsApp bot is now active and ready to serve your customers.
      Log in to your dashboard to set up auto-replies, add products
      and customise your bot.
    </p>
    """ + _details_table([
        ("Business Name", business_name),
        ("Status",        "<span style='background-color:#dcfce7;color:#166534;"
                          "font-size:11px;font-weight:700;padding:3px 10px;"
                          "border-radius:100px;'>ACTIVE</span>"),
        ("Platform",      "BotMart WhatsApp Automation"),
        ("Dashboard",     f"<a href='{base_url}/login/' style='color:#065f46 !important;'>"
                          f"{base_url}/login/</a>"),
    ]) + _cta_button("Log In to Dashboard", f"{base_url}/login/")

    html = _build_email(
        header_icon     = "&#x1F680;",
        header_title    = "You're Live on BotMart!",
        header_subtitle = "Your WhatsApp bot is now active and ready",
        subject_bar     = "Account Activation Confirmation",
        body_content    = body
    )

    result = _smtp_send(to_email, subject, html)
    if result:
        print(f"✅ Activation email sent to {to_email}")
    return result




# ─────────────────────────────────────────────
# Add these two functions to your email_helper.py
# ─────────────────────────────────────────────

def send_new_client_notification(client_email, business_name, plan, months, amount_naira, admin_url):
    """
    Notifies the BotMart owner when a new client registers and pays.
    Triggered from paystack_webhook after first payment.
    """
    admin_email = os.getenv('ADMIN_NOTIFY_EMAIL')
    if not admin_email:
        print("[email] ADMIN_NOTIFY_EMAIL not set — skipping admin notification")
        return

    today       = date.today().strftime("%d %b %Y")
    plan_colors = {'starter': '#6b7280', 'growth': '#2563eb', 'pro': '#7c3aed'}
    plan_color  = plan_colors.get(plan, '#6b7280')
    duration    = {1: '1 Month', 3: '3 Months', 6: '6 Months', 12: '12 Months'}.get(months, f'{months} Months')

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:0;background:#0d1117;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0d1117;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="580" cellpadding="0" cellspacing="0" style="max-width:580px;width:100%;">

          <!-- Header -->
          <tr>
            <td style="padding:0 0 28px 0;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <span style="font-size:22px;font-weight:800;color:white;letter-spacing:-0.03em;">
                      🤖 Bot<span style="color:#25D366;">Mart</span>
                    </span>
                  </td>
                  <td align="right">
                    <span style="background:rgba(37,211,102,0.1);border:1px solid rgba(37,211,102,0.25);
                      color:#25D366;padding:4px 12px;border-radius:100px;font-size:11px;
                      font-family:monospace;letter-spacing:0.1em;">NEW CLIENT</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main card -->
          <tr>
            <td style="background:#161b22;border:1px solid rgba(255,255,255,0.07);
              border-radius:16px;overflow:hidden;">

              <!-- Green top bar -->
              <tr>
                <td style="background:linear-gradient(90deg,#075e54,#25D366);height:4px;display:block;line-height:4px;font-size:4px;">&nbsp;</td>
              </tr>

              <!-- Content -->
              <tr>
                <td style="padding:32px;">

                  <!-- Icon + title -->
                  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                    <tr>
                      <td style="width:56px;vertical-align:middle;">
                        <div style="width:52px;height:52px;background:rgba(37,211,102,0.1);
                          border:1px solid rgba(37,211,102,0.2);border-radius:14px;
                          text-align:center;line-height:52px;font-size:24px;">🎉</div>
                      </td>
                      <td style="padding-left:16px;vertical-align:middle;">
                        <div style="font-size:11px;font-family:monospace;letter-spacing:0.12em;
                          text-transform:uppercase;color:rgba(255,255,255,0.35);margin-bottom:4px;">
                          New Registration — {today}
                        </div>
                        <div style="font-size:20px;font-weight:700;color:white;letter-spacing:-0.02em;">
                          A new client just signed up!
                        </div>
                      </td>
                    </tr>
                  </table>

                  <!-- Client details -->
                  <table width="100%" cellpadding="0" cellspacing="0"
                    style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
                    border-radius:12px;margin-bottom:24px;">
                    <tr>
                      <td style="padding:20px 22px;">
                        <table width="100%" cellpadding="0" cellspacing="0">

                          <tr>
                            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:rgba(255,255,255,0.35);font-size:12px;">Business</span>
                            </td>
                            <td align="right" style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:white;font-size:14px;font-weight:600;">{business_name}</span>
                            </td>
                          </tr>

                          <tr>
                            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:rgba(255,255,255,0.35);font-size:12px;">Email</span>
                            </td>
                            <td align="right" style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:#25D366;font-size:14px;">{client_email}</span>
                            </td>
                          </tr>

                          <tr>
                            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:rgba(255,255,255,0.35);font-size:12px;">Plan</span>
                            </td>
                            <td align="right" style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="background:{plan_color};color:white;padding:2px 10px;
                                border-radius:100px;font-size:12px;font-weight:600;">
                                {plan.title()}
                              </span>
                            </td>
                          </tr>

                          <tr>
                            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:rgba(255,255,255,0.35);font-size:12px;">Duration</span>
                            </td>
                            <td align="right" style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:white;font-size:14px;">{duration}</span>
                            </td>
                          </tr>

                          <tr>
                            <td style="padding:8px 0;">
                              <span style="color:rgba(255,255,255,0.35);font-size:12px;">Amount Paid</span>
                            </td>
                            <td align="right" style="padding:8px 0;">
                              <span style="color:#25D366;font-size:18px;font-weight:700;">
                                ₦{amount_naira:,}
                              </span>
                            </td>
                          </tr>

                        </table>
                      </td>
                    </tr>
                  </table>

                  <!-- Action note -->
                  <table width="100%" cellpadding="0" cellspacing="0"
                    style="background:rgba(251,191,36,0.07);border:1px solid rgba(251,191,36,0.2);
                    border-left:3px solid #fbbf24;border-radius:0 10px 10px 0;margin-bottom:28px;">
                    <tr>
                      <td style="padding:14px 16px;">
                        <span style="font-size:13px;color:#fbbf24;font-weight:600;">⚡ Action required</span><br>
                        <span style="font-size:13px;color:rgba(255,255,255,0.55);line-height:1.6;">
                          This client is awaiting your activation. Log into the admin panel
                          to review and activate their account so they can go live.
                        </span>
                      </td>
                    </tr>
                  </table>

                  <!-- CTA button -->
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td align="center">
                        <a href="{admin_url}" style="display:inline-block;background:#075e54;
                          color:white;text-decoration:none;padding:14px 36px;border-radius:10px;
                          font-size:15px;font-weight:600;letter-spacing:-0.01em;">
                          Activate Client in Admin →
                        </a>
                      </td>
                    </tr>
                  </table>

                </td>
              </tr>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 0 0 0;text-align:center;">
              <span style="font-size:12px;color:rgba(255,255,255,0.2);">
                BotMart Admin Notification · You're receiving this because you're the account owner
              </span>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


    try:
        subject = f"🎉 New Client: {business_name} — {plan.title()} Plan ({duration})"
        _smtp_send(admin_email, subject, html)
        print(f"[email] Admin notified of new client: {business_name}")
    except Exception as e:
        print(f"[email] Admin notification failed: {e}")
        # Never raise — don't let email failure break the payment flow



def send_renewal_notification(client_email, business_name, plan, months, amount_naira):
    """
    Notifies the BotMart owner when an existing client renews.
    Triggered from paystack_webhook / renew_verify for renewals.
    """
    admin_email = os.getenv('ADMIN_NOTIFY_EMAIL')
    if not admin_email:
        return

    today    = date.today().strftime("%d %b %Y")
    duration = {1: '1 Month', 3: '3 Months', 6: '6 Months', 12: '12 Months'}.get(months, f'{months} Months')
    plan_colors = {'starter': '#6b7280', 'growth': '#2563eb', 'pro': '#7c3aed'}
    plan_color  = plan_colors.get(plan, '#6b7280')

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0d1117;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0d1117;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="580" cellpadding="0" cellspacing="0" style="max-width:580px;width:100%;">

          <tr>
            <td style="padding:0 0 28px 0;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <span style="font-size:22px;font-weight:800;color:white;letter-spacing:-0.03em;">
                      🤖 Bot<span style="color:#25D366;">Mart</span>
                    </span>
                  </td>
                  <td align="right">
                    <span style="background:rgba(56,189,248,0.1);border:1px solid rgba(56,189,248,0.25);
                      color:#38bdf8;padding:4px 12px;border-radius:100px;font-size:11px;
                      font-family:monospace;letter-spacing:0.1em;">RENEWAL</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td style="background:#161b22;border:1px solid rgba(255,255,255,0.07);
              border-radius:16px;overflow:hidden;">
              <tr>
                <td style="background:linear-gradient(90deg,#0284c7,#38bdf8);height:4px;
                  display:block;line-height:4px;font-size:4px;">&nbsp;</td>
              </tr>
              <tr>
                <td style="padding:32px;">

                  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                    <tr>
                      <td style="width:56px;vertical-align:middle;">
                        <div style="width:52px;height:52px;background:rgba(56,189,248,0.1);
                          border:1px solid rgba(56,189,248,0.2);border-radius:14px;
                          text-align:center;line-height:52px;font-size:24px;">🔄</div>
                      </td>
                      <td style="padding-left:16px;vertical-align:middle;">
                        <div style="font-size:11px;font-family:monospace;letter-spacing:0.12em;
                          text-transform:uppercase;color:rgba(255,255,255,0.35);margin-bottom:4px;">
                          Subscription Renewed — {today}
                        </div>
                        <div style="font-size:20px;font-weight:700;color:white;letter-spacing:-0.02em;">
                          {business_name} just renewed!
                        </div>
                      </td>
                    </tr>
                  </table>

                  <table width="100%" cellpadding="0" cellspacing="0"
                    style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
                    border-radius:12px;margin-bottom:24px;">
                    <tr>
                      <td style="padding:20px 22px;">
                        <table width="100%" cellpadding="0" cellspacing="0">
                          <tr>
                            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:rgba(255,255,255,0.35);font-size:12px;">Business</span>
                            </td>
                            <td align="right" style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:white;font-size:14px;font-weight:600;">{business_name}</span>
                            </td>
                          </tr>
                          <tr>
                            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:rgba(255,255,255,0.35);font-size:12px;">Email</span>
                            </td>
                            <td align="right" style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:#38bdf8;font-size:14px;">{client_email}</span>
                            </td>
                          </tr>
                          <tr>
                            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:rgba(255,255,255,0.35);font-size:12px;">Plan</span>
                            </td>
                            <td align="right" style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="background:{plan_color};color:white;padding:2px 10px;
                                border-radius:100px;font-size:12px;font-weight:600;">{plan.title()}</span>
                            </td>
                          </tr>
                          <tr>
                            <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:rgba(255,255,255,0.35);font-size:12px;">Duration</span>
                            </td>
                            <td align="right" style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                              <span style="color:white;font-size:14px;">{duration}</span>
                            </td>
                          </tr>
                          <tr>
                            <td style="padding:8px 0;">
                              <span style="color:rgba(255,255,255,0.35);font-size:12px;">Amount Paid</span>
                            </td>
                            <td align="right" style="padding:8px 0;">
                              <span style="color:#38bdf8;font-size:18px;font-weight:700;">₦{amount_naira:,}</span>
                            </td>
                          </tr>
                        </table>
                      </td>
                    </tr>
                  </table>

                  <div style="text-align:center;font-size:13px;color:rgba(255,255,255,0.35);
                    background:rgba(255,255,255,0.03);border-radius:10px;padding:14px;">
                    No action required — their subscription has been automatically extended.
                  </div>

                </td>
              </tr>
            </td>
          </tr>

          <tr>
            <td style="padding:24px 0 0 0;text-align:center;">
              <span style="font-size:12px;color:rgba(255,255,255,0.2);">
                BotMart Admin Notification · You're receiving this because you're the account owner
              </span>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    try:
        subject = f"🔄 Renewal: {business_name} — {plan.title()} Plan ₦{amount_naira:,}"
        _smtp_send(admin_email, subject, html)
        print(f"[email] Admin notified of renewal: {business_name}")
    except Exception as e:
        print(f"[email] Renewal notification failed: {e}")