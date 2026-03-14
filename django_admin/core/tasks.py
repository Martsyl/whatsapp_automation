# core/tasks.py

import time
import os
import logging
import requests as http_requests
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# EMAIL TEMPLATE WRAPPER
# ─────────────────────────────────────────────

def wrap_with_template(subject, body, business_name, plan):
    """
    Professional email template — clean white layout similar to bank-style emails.
    Uses __PLACEHOLDER__ tokens to avoid f-string CSS brace conflicts.
    """
    base_url = os.getenv('BASE_URL', 'http://localhost:8001')
    whatsapp = os.getenv('SUPPORT_WHATSAPP', '2348000000000')

    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
  <title>__SUBJECT__</title>
</head>
<body style="margin:0;padding:0;background-color:#e8e8e8;
  font-family:Arial,Helvetica,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" border="0"
    style="background-color:#e8e8e8;padding:32px 16px;">
    <tr>
      <td align="center">

        <!-- Main card -->
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
          style="max-width:580px;background:#ffffff;
          border-radius:4px;overflow:hidden;
          box-shadow:0 2px 12px rgba(0,0,0,0.12);">

          <!-- ══════════════════════════════ -->
          <!--  HEADER BANNER                 -->
          <!-- ══════════════════════════════ -->
          <tr>
            <td style="background:linear-gradient(135deg,#064e3b 0%,#065f46 40%,#047857 70%,#059669 100%);
              padding:0;height:120px;position:relative;overflow:hidden;">

              <!-- Decorative background shapes -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                style="height:120px;">
                <tr>
                  <td style="padding:0 32px;vertical-align:middle;">

                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <!-- Logo left -->
                        <td style="vertical-align:middle;">
                          <table cellpadding="0" cellspacing="0" border="0">
                            <tr>
                              <td style="background:rgba(255,255,255,0.18);
                                border-radius:10px;padding:8px 14px;
                                vertical-align:middle;">
                                <span style="font-size:24px;vertical-align:middle;
                                  line-height:1;">&#x1F4AC;</span>
                                <span style="color:#ffffff;font-size:22px;
                                  font-weight:800;vertical-align:middle;
                                  margin-left:8px;letter-spacing:-0.5px;
                                  font-family:Arial,sans-serif;">
                                  BotMart
                                </span>
                              </td>
                            </tr>
                          </table>
                        </td>

                        <!-- Tagline right -->
                        <td style="text-align:right;vertical-align:middle;">
                          <span style="color:rgba(255,255,255,0.6);
                            font-size:11px;font-style:italic;
                            font-family:Arial,sans-serif;">
                            Automation that works for you
                          </span>
                        </td>
                      </tr>
                    </table>

                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- ══════════════════════════════ -->
          <!--  SUBJECT TITLE BAR             -->
          <!-- ══════════════════════════════ -->
          <tr>
            <td style="background:#f9fafb;border-bottom:2px solid #059669;
              padding:20px 32px;text-align:center;">
              <p style="margin:0;font-size:15px;font-weight:700;
                color:#111827;letter-spacing:0.5px;text-transform:uppercase;
                font-family:Arial,sans-serif;">
                __SUBJECT__
              </p>
            </td>
          </tr>

          <!-- ══════════════════════════════ -->
          <!--  BODY                          -->
          <!-- ══════════════════════════════ -->
          <tr>
            <td style="background:#ffffff;padding:36px 32px 28px;">

              <!-- Greeting -->
              <p style="margin:0 0 20px;font-size:15px;color:#111827;
                font-family:Arial,sans-serif;line-height:1.5;">
                Dear <strong>__BUSINESS_NAME__</strong>,
              </p>

              <!-- Body content -->
              <div style="font-size:15px;color:#374151;line-height:1.8;
                margin:0 0 28px;font-family:Arial,sans-serif;">
                __BODY__
              </div>

              <!-- Plan info table (Zenith-style data table) -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                style="border:1px solid #d1d5db;border-radius:6px;
                overflow:hidden;margin-bottom:28px;">

                <tr>
                  <td colspan="2" style="background:#f3f4f6;padding:12px 16px;
                    border-bottom:1px solid #d1d5db;">
                    <strong style="font-size:13px;color:#111827;
                      font-family:Arial,sans-serif;letter-spacing:0.3px;">
                      ACCOUNT DETAILS
                    </strong>
                  </td>
                </tr>

                <tr style="border-bottom:1px solid #e5e7eb;">
                  <td style="padding:12px 16px;font-size:13px;font-weight:600;
                    color:#374151;font-family:Arial,sans-serif;width:45%;
                    background:#fafafa;border-bottom:1px solid #e5e7eb;">
                    Business Name
                  </td>
                  <td style="padding:12px 16px;font-size:13px;color:#111827;
                    font-family:Arial,sans-serif;border-bottom:1px solid #e5e7eb;">
                    __BUSINESS_NAME__
                  </td>
                </tr>

                <tr style="border-bottom:1px solid #e5e7eb;">
                  <td style="padding:12px 16px;font-size:13px;font-weight:600;
                    color:#374151;font-family:Arial,sans-serif;
                    background:#fafafa;border-bottom:1px solid #e5e7eb;">
                    Active Plan
                  </td>
                  <td style="padding:12px 16px;font-size:13px;color:#111827;
                    font-family:Arial,sans-serif;border-bottom:1px solid #e5e7eb;">
                    <strong style="color:#065f46;">__PLAN__ Plan</strong>
                  </td>
                </tr>

                <tr style="border-bottom:1px solid #e5e7eb;">
                  <td style="padding:12px 16px;font-size:13px;font-weight:600;
                    color:#374151;font-family:Arial,sans-serif;
                    background:#fafafa;border-bottom:1px solid #e5e7eb;">
                    Platform
                  </td>
                  <td style="padding:12px 16px;font-size:13px;color:#111827;
                    font-family:Arial,sans-serif;border-bottom:1px solid #e5e7eb;">
                    BotMart WhatsApp Automation
                  </td>
                </tr>

                <tr>
                  <td style="padding:12px 16px;font-size:13px;font-weight:600;
                    color:#374151;font-family:Arial,sans-serif;background:#fafafa;">
                    Status
                  </td>
                  <td style="padding:12px 16px;font-size:13px;
                    font-family:Arial,sans-serif;">
                    <span style="background:#dcfce7;color:#166534;
                      font-size:12px;font-weight:700;padding:3px 10px;
                      border-radius:100px;">
                      ACTIVE
                    </span>
                  </td>
                </tr>

              </table>

              <!-- CTA Button -->
              <table cellpadding="0" cellspacing="0" border="0"
                style="margin-bottom:28px;">
                <tr>
                  <td style="background:#065f46;border-radius:4px;">
                    <a href="__BASE_URL__/login/"
                      style="display:inline-block;padding:13px 32px;
                      color:#ffffff;font-family:Arial,sans-serif;
                      font-size:14px;font-weight:700;text-decoration:none;
                      letter-spacing:0.5px;">
                      LOG IN TO DASHBOARD &rarr;
                    </a>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- ══════════════════════════════ -->
          <!--  SECURITY NOTICE               -->
          <!-- ══════════════════════════════ -->
          <tr>
            <td style="background:#fefce8;border-top:1px solid #fde68a;
              border-bottom:1px solid #fde68a;padding:16px 32px;">
              <p style="margin:0 0 6px;font-size:12px;font-weight:700;
                color:#92400e;font-family:Arial,sans-serif;
                letter-spacing:0.5px;">
                SECURITY NOTICE
              </p>
              <p style="margin:0;font-size:12px;color:#78350f;
                font-family:Arial,sans-serif;line-height:1.6;">
                BotMart will <strong>NEVER</strong> ask for your password,
                payment card details or OTP via email or WhatsApp.
                If you did not request this email, please ignore it or
                contact us immediately.
              </p>
            </td>
          </tr>

          <!-- ══════════════════════════════ -->
          <!--  WAYS TO REACH US              -->
          <!-- ══════════════════════════════ -->
          <tr>
            <td style="background:#ffffff;padding:24px 32px;
              border-top:1px solid #e5e7eb;">
              <p style="margin:0 0 10px;font-size:12px;font-weight:700;
                color:#111827;font-family:Arial,sans-serif;
                letter-spacing:0.5px;">
                WAYS TO REACH US
              </p>
              <p style="margin:0 0 12px;font-size:13px;color:#6b7280;
                font-family:Arial,sans-serif;line-height:1.7;">
                For support, visit your dashboard or chat with us directly
                on WhatsApp. Our team typically responds within minutes
                during business hours (Mon&ndash;Fri, 9am&ndash;6pm WAT).
              </p>

              <!-- WhatsApp + Social row -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="vertical-align:middle;">
                    <a href="https://wa.me/__WHATSAPP__"
                      style="display:inline-block;background:#25d366;
                      border-radius:4px;padding:8px 18px;
                      color:#ffffff;font-family:Arial,sans-serif;
                      font-size:13px;font-weight:700;text-decoration:none;">
                      &#x1F4AC; WhatsApp Us
                    </a>
                  </td>
                  <td style="text-align:right;vertical-align:middle;">
                    <table cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="padding:0 4px;">
                          <a href="https://facebook.com/botmart"
                            style="display:inline-block;background:#1877f2;
                            border-radius:50%;width:30px;height:30px;
                            text-align:center;line-height:30px;
                            text-decoration:none;color:#fff;
                            font-size:13px;font-weight:700;
                            font-family:Arial,sans-serif;">f</a>
                        </td>
                        <td style="padding:0 4px;">
                          <a href="https://wa.me/__WHATSAPP__"
                            style="display:inline-block;background:#25d366;
                            border-radius:50%;width:30px;height:30px;
                            text-align:center;line-height:30px;
                            text-decoration:none;color:#fff;
                            font-size:14px;font-family:Arial,sans-serif;">&#x1F4AC;</a>
                        </td>
                        <td style="padding:0 4px;">
                          <a href="https://twitter.com/botmart"
                            style="display:inline-block;background:#000000;
                            border-radius:50%;width:30px;height:30px;
                            text-align:center;line-height:30px;
                            text-decoration:none;color:#fff;
                            font-size:12px;font-weight:700;
                            font-family:Arial,sans-serif;">X</a>
                        </td>
                        <td style="padding:0 4px;">
                          <a href="https://linkedin.com/company/botmart"
                            style="display:inline-block;background:#0077b5;
                            border-radius:50%;width:30px;height:30px;
                            text-align:center;line-height:30px;
                            text-decoration:none;color:#fff;
                            font-size:11px;font-weight:700;
                            font-family:Arial,sans-serif;">in</a>
                        </td>
                        <td style="padding:0 4px;">
                          <a href="https://instagram.com/botmart"
                            style="display:inline-block;
                            background:radial-gradient(circle at 30% 107%,#fdf497 0%,#fd5949 45%,#d6249f 60%,#285aeb 90%);
                            border-radius:50%;width:30px;height:30px;
                            text-align:center;line-height:30px;
                            text-decoration:none;color:#fff;
                            font-size:11px;font-weight:700;
                            font-family:Arial,sans-serif;">IG</a>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- ══════════════════════════════ -->
          <!--  FOOTER                        -->
          <!-- ══════════════════════════════ -->
          <tr>
            <td style="background:#f3f4f6;border-top:1px solid #e5e7eb;
              padding:20px 32px;text-align:center;">
              <p style="margin:0 0 8px;font-size:12px;color:#6b7280;
                font-family:Arial,sans-serif;line-height:1.6;">
                &copy; 2026 BotMart &mdash; WhatsApp Automation for Every Business.
                Lagos, Nigeria.
              </p>
              <p style="margin:0;">
                <a href="__BASE_URL__/unsubscribe/"
                  style="color:#6b7280;font-size:11px;
                  font-family:Arial,sans-serif;text-decoration:underline;">
                  Unsubscribe
                </a>
                <span style="color:#d1d5db;padding:0 8px;">|</span>
                <a href="__BASE_URL__/privacy/"
                  style="color:#6b7280;font-size:11px;
                  font-family:Arial,sans-serif;text-decoration:underline;">
                  Privacy Policy
                </a>
                <span style="color:#d1d5db;padding:0 8px;">|</span>
                <a href="__BASE_URL__"
                  style="color:#6b7280;font-size:11px;
                  font-family:Arial,sans-serif;text-decoration:underline;">
                  botmart.app
                </a>
              </p>
            </td>
          </tr>

        </table>
        <!-- end card -->

      </td>
    </tr>
  </table>

</body>
</html>"""

    # Safe substitution — no f-string, no CSS brace conflicts
    html = html.replace('__SUBJECT__',       subject)
    html = html.replace('__BUSINESS_NAME__', business_name)
    html = html.replace('__BODY__',          body)
    html = html.replace('__PLAN__',          plan)
    html = html.replace('__BASE_URL__',      base_url)
    html = html.replace('__WHATSAPP__',      whatsapp)

    return html


# ─────────────────────────────────────────────
# SEND SINGLE EMAIL
# ─────────────────────────────────────────────

def send_single_email(to_email, subject, body):
    """Send one email via Resend API. Returns (success, error_msg)"""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        return False, "RESEND_API_KEY not configured"
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
                "html": body,
            },
            timeout=15
        )
        if response.status_code in (200, 201):
            return True, None
        else:
            return False, f"Resend error {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────
# SEND CAMPAIGN TASK
# ─────────────────────────────────────────────

@shared_task(bind=True, max_retries=3)
def send_campaign(self, campaign_id):
    """
    Main Celery task — sends campaign emails in batches of 50.
    Runs in background, updates progress in DB after each batch.
    Retries up to 3 times on unexpected failure with 60s delay.
    """
    from core.models import EmailCampaign, CampaignLog, Client

    logger.info(f"[send_campaign] Starting campaign id={campaign_id}")

    try:
        campaign = EmailCampaign.objects.get(id=campaign_id)
    except EmailCampaign.DoesNotExist:
        logger.error(f"[send_campaign] Campaign {campaign_id} not found — aborting")
        return

    if campaign.status not in ['queued', 'sending']:
        logger.warning(
            f"[send_campaign] Campaign {campaign_id} has status '{campaign.status}' — skipping"
        )
        return

    try:
        campaign.status = 'sending'
        campaign.save(update_fields=['status'])

        if campaign.recipient_type == 'all':
            clients = Client.objects.filter(is_active=True)
        elif campaign.recipient_type == 'plan':
            clients = Client.objects.filter(is_active=True, plan=campaign.target_plan)
        elif campaign.recipient_type == 'selected':
            clients = campaign.selected_clients.filter(is_active=True)
        else:
            clients = Client.objects.none()

        clients = list(clients)

        campaign.total_recipients = len(clients)
        campaign.save(update_fields=['total_recipients'])

        logger.info(
            f"[send_campaign] Campaign '{campaign.subject}' → {len(clients)} recipients"
        )

        BATCH_SIZE   = 50
        BATCH_DELAY  = 1.5
        sent_count   = 0
        failed_count = 0

        for i in range(0, len(clients), BATCH_SIZE):
            batch = clients[i:i + BATCH_SIZE]

            for client in batch:
                try:
                    log, created = CampaignLog.objects.get_or_create(
                        campaign=campaign,
                        client=client,
                        defaults={'email': client.email, 'status': 'pending'}
                    )

                    if not created and log.status == 'sent':
                        sent_count += 1
                        continue

                    raw_body = campaign.body.replace(
                        '{business_name}', client.business_name
                    ).replace(
                        '{email}', client.email
                    ).replace(
                        '{plan}', client.plan.title()
                    )

                    personalised_body = wrap_with_template(
                        subject=campaign.subject,
                        body=raw_body,
                        business_name=client.business_name,
                        plan=client.plan.title()
                    )

                    success, error = send_single_email(
                        client.email,
                        campaign.subject,
                        personalised_body
                    )

                    if success:
                        log.status  = 'sent'
                        log.sent_at = timezone.now()
                        sent_count += 1
                        logger.info(f"[send_campaign] Sent to {client.email}")
                    else:
                        log.status    = 'failed'
                        log.error_msg = error
                        failed_count += 1
                        logger.warning(
                            f"[send_campaign] Failed for {client.email}: {error}"
                        )

                    log.save()

                except Exception as per_client_error:
                    # One client failing should never stop the whole campaign
                    failed_count += 1
                    logger.error(
                        f"[send_campaign] Unexpected error for client {client.email}: "
                        f"{per_client_error}",
                        exc_info=True
                    )
                    try:
                        log.status    = 'failed'
                        log.error_msg = str(per_client_error)
                        log.save()
                    except Exception:
                        pass

            campaign.sent_count   = sent_count
            campaign.failed_count = failed_count
            campaign.save(update_fields=['sent_count', 'failed_count'])

            logger.info(
                f"[send_campaign] Batch {i // BATCH_SIZE + 1} done "
                f"— {sent_count} sent, {failed_count} failed"
            )

            if i + BATCH_SIZE < len(clients):
                time.sleep(BATCH_DELAY)

        campaign.status       = 'completed'
        campaign.sent_count   = sent_count
        campaign.failed_count = failed_count
        campaign.save(update_fields=['status', 'sent_count', 'failed_count'])

        logger.info(
            f"[send_campaign] Campaign '{campaign.subject}' complete "
            f"— {sent_count} sent, {failed_count} failed"
        )

    except Exception as e:
        # Unexpected task-level failure — mark campaign failed and retry
        logger.error(
            f"[send_campaign] Task failed for campaign {campaign_id}: {e}",
            exc_info=True
        )
        try:
            campaign.status = 'failed'
            campaign.save(update_fields=['status'])
        except Exception:
            pass
        # Retry with 60s delay, up to max_retries=3
        raise self.retry(exc=e, countdown=60)


# ─────────────────────────────────────────────
# SCHEDULED CAMPAIGN DISPATCHER
# ─────────────────────────────────────────────

@shared_task
def dispatch_scheduled_campaigns():
    """
    Runs every minute via Celery Beat.
    Picks up campaigns whose scheduled_at has passed and queues them.
    """
    from core.models import EmailCampaign

    try:
        now = timezone.now()
        due_campaigns = EmailCampaign.objects.filter(
            status='draft',
            scheduled_at__lte=now,
            scheduled_at__isnull=False
        )

        dispatched = 0
        for campaign in due_campaigns:
            try:
                campaign.status = 'queued'
                campaign.save(update_fields=['status'])
                send_campaign.delay(campaign.id)
                dispatched += 1
                logger.info(
                    f"[dispatch_scheduled_campaigns] Queued campaign: '{campaign.subject}' "
                    f"(id={campaign.id})"
                )
            except Exception as e:
                # One campaign failing should not stop others from being dispatched
                logger.error(
                    f"[dispatch_scheduled_campaigns] Failed to dispatch campaign "
                    f"id={campaign.id}: {e}",
                    exc_info=True
                )

        if dispatched:
            logger.info(
                f"[dispatch_scheduled_campaigns] {dispatched} campaign(s) dispatched"
            )

    except Exception as e:
        # Catch DB errors or any unexpected failure so Beat keeps running
        logger.error(
            f"[dispatch_scheduled_campaigns] Unexpected error: {e}",
            exc_info=True
        )