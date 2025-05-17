from flask import Flask, request, render_template_string
import requests
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your.email@gmail.com"
SMTP_PASSWORD = "your-email-app-password"

GUMROAD_LINK = "https://gumroad.com/l/yourproduct"  # optional promo link

# Simple HTML form for topic + email
HTML_FORM = """
<!doctype html>
<title>AI eBook Generator</title>
<h2>Generate your AI-powered eBook</h2>
<form method=post>
  Topic: <input type=text name=topic required><br>
  Your Email: <input type=email name=email required><br>
  <input type=submit value="Generate eBook">
</form>
{% if message %}
<p>{{ message }}</p>
{% endif %}
"""

def generate_ebook_content(topic):
    prompt = f"Write a detailed eBook about: {topic}"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    return content

def send_email(recipient, subject, body):
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = SMTP_USERNAME
    msg["To"] = recipient

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    if request.method == "POST":
        topic = request.form.get("topic")
        email = request.form.get("email")
        try:
            ebook_content = generate_ebook_content(topic)
            # Optionally add Gumroad promo at the end
            ebook_content += f"\n\nEnjoyed this eBook? Check out more at {GUMROAD_LINK}"
            send_email(email, f"Your AI-Generated eBook on {topic}", ebook_content)
            message = f"Success! The eBook on '{topic}' was sent to {email}."
        except Exception as e:
            message = f"Error: {str(e)}"
    return render_template_string(HTML_FORM, message=message)

if __name__ == "__main__":
    app.run(debug=True)
