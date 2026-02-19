import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email_notification(to_email, business_name, sender_number, message_text):
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv("MAIL_FROM")
        msg['To'] = to_email
        msg['Subject'] = f"🔔 New Human Handoff Request - {business_name}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #075e54;">New Customer Needs Attention</h2>
            <p>A customer has requested to speak with a human agent.</p>
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Business</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{business_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Customer Number</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{sender_number}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Last Message</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{message_text}</td>
                </tr>
            </table>
            <p style="margin-top: 20px;">Please follow up with this customer as soon as possible.</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(os.getenv("MAIL_SERVER"), int(os.getenv("MAIL_PORT")))
        server.starttls()
        server.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
        server.sendmail(os.getenv("MAIL_FROM"), to_email, msg.as_string())
        server.quit()
        print(f"Email notification sent to {to_email}")

    except Exception as e:
        print(f"Email failed: {e}")