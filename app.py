import os
import io
import csv
import base64
import logging
import requests
from openai import OpenAI  # Updated import
from flask import Flask, render_template, request, redirect, url_for, flash
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "defaultsecret")
logging.basicConfig(level=logging.DEBUG)

# API Keys
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client (new method)
client = OpenAI(api_key=OPENAI_API_KEY)

# Save lead
def save_lead(email, topic):
    with open("leads.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([email, topic])
    logging.info(f"Saved lead: {email} | {topic}")

# Generate content with GPT (new method)
def generate_content(topic):
    prompt = f"Write a detailed short eBook about '{topic}' including useful tips, strategies, and examples."
    response = client.chat.completions.create(
        model="gpt-4o",  # Or "gpt-4-turbo" if you prefer
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Create PDF from content
def generate_pdf(topic, content):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 16)
    c.drawString(100, 750, f"eBook: {topic}")
    c.setFont("Helvetica", 12)
    y = 730
    for line in content.split('\n'):
        for wrapped in [line[i:i+90] for i in range(0, len(line), 90)]:
            c.drawString(100, y, wrapped)
            y -= 20
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 750
    c.save()
    buffer.seek(0)
    return buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            topic = request.form['topic']
            email = request.form['email']

            # Save the lead
            save_lead(email, topic)

            # Generate content and PDF
            content = generate_content(topic)
            pdf_buffer = generate_pdf(topic, content)
            encoded_pdf = base64.b64encode(pdf_buffer.read()).decode()

            # Send email using Resend
            data = {
                "from": "your-email@onresend.com",
                "to": [email],
                "subject": f"Your eBook on {topic}",
                "text": f"Hi! Attached is your eBook on {topic}.",
                "attachments": [
                    {
                        "filename": f"{topic.replace(' ', '_')}.pdf",
                        "content": encoded_pdf,
                        "content_type": "application/pdf"
                    }
                ]
            }

            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=data
            )

            if response.status_code == 200:
                flash("Your eBook was sent successfully!")
            else:
                flash("Failed to send email. Please try again.")

        except Exception as e:
            logging.exception("Error during eBook generation")
            flash(f"An error occurred: {str(e)}")

        return redirect(url_for('index'))

    return render_template('index.html')

@app.after_request
def add_google_analytics(response):
    script = """
    <script async src="https://www.googletagmanager.com/gtag/js?id=UA-XXXXXXXXX-X"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'UA-XXXXXXXXX-X');
    </script>
    """
    if response.content_type == "text/html; charset=utf-8":
        response.set_data(response.get_data().replace(b"</body>", script.encode() + b"</body>"))
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
