import requests
import base64
import io
import os
import logging
from flask import Flask, render_template, request
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
if not RESEND_API_KEY:
    logging.error("RESEND_API_KEY not set in environment variables")

def generate_pdf(topic):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 16)
    c.drawString(100, 750, f"eBook on {topic}")
    c.setFont("Helvetica", 12)
    c.drawString(100, 730, "Generated using AI-powered tools.")
    content = f"This is an example eBook on {topic}.\nThis content was generated using AI.\n"
    y_position = 710
    for line in content.split("\n"):
        c.drawString(100, y_position, line)
        y_position -= 20
    c.save()
    buffer.seek(0)
    return buffer
    @app.route('/', methods=["GET", "HEAD"])
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error rendering index.html: {e}")
        return "Internal Server Error", 500

@app.route('/generate', methods=['GET'])
def generate():
    try:
        topic = request.form['topic']
        email = request.form['email']
        logging.info(f"Generating PDF for topic: {topic}")

        buffer = generate_pdf(topic)
        encoded_pdf = base64.b64encode(buffer.read()).decode()

        data = {
            "from": "your-email@onresend.com",
            "to": [email],
            "subject": f"Your eBook on {topic}",
            "text": f"Hi! Here is your eBook on {topic}.",
            "attachments": [
                {
                    "filename": f"{topic.replace(' ', '_')}.pdf",
                    "content": encoded_pdf,
                    "content_type": "application/pdf"
                }
            ]
        }

        response = requests.get(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json=data
        )

        if response.status_code == 200:
            logging.info("Email sent successfully")
            return "eBook sent to your email!"
        else:
            logging.error(f"Email sending failed: {response.text}")
            return f"Failed to send email: {response.text}"
    except Exception as e:
        logging.exception("An error occurred in /generate")
        return f"Internal error: {str(e)}"

@app.after_request
def add_google_analytics(response):
    google_analytics_script = """
    <script async src="https://www.googletagmanager.com/gtag/js?id=UA-XXXXXXXXX-X"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'UA-XXXXXXXXX-X');
    </script>
    """
    if response.content_type == "text/html; charset=utf-8":
        response.set_data(response.get_data().replace(b"</body>", google_analytics_script.encode() + b"</body>"))
    return response

if __name__ == "__main__":
    app.run(debug=True)
