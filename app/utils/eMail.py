import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import EmailStr

def send_email(email: EmailStr, download_link: str):
    sender_email = "your_email@gmail.com"  # Replace with your email address
    app_password = "your_app_password"  # Replace with your app password or email password
    
    # Create a multipart message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = "Your Video is Ready for Download"
    
    # The email body
    body = f"Hi there,\n\nYour video is ready for download: {download_link}\n\nBest regards,"
    message.attach(MIMEText(body, "plain"))
    
    try:
        # Log in to server using secure context and send email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, email, message.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")