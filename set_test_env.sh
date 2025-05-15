#!/bin/bash

# Script to set environment variables directly for testing email functionality

# Email Configuration
export EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
export EMAIL_HOST="smtp.gmail.com"
export EMAIL_PORT="587"
export EMAIL_USE_TLS="True"
export EMAIL_HOST_USER="mafikuzia@gmail.com"
export EMAIL_HOST_PASSWORD="kwjt twkz mmzd twty"
export DEFAULT_FROM_EMAIL="mafikuzia@gmail.com"

# Print the environment variables
echo "Environment variables set:"
echo "EMAIL_BACKEND: $EMAIL_BACKEND"
echo "EMAIL_HOST: $EMAIL_HOST" 
echo "EMAIL_PORT: $EMAIL_PORT"
echo "EMAIL_USE_TLS: $EMAIL_USE_TLS"
echo "EMAIL_HOST_USER: $EMAIL_HOST_USER"
echo "EMAIL_HOST_PASSWORD: [HIDDEN]"
echo "DEFAULT_FROM_EMAIL: $DEFAULT_FROM_EMAIL"

echo "To test email directly, run: python -c \"
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Create message
msg = MIMEMultipart()
msg['From'] = os.environ['DEFAULT_FROM_EMAIL']
msg['To'] = 'test@example.com'  # Replace with your test email
msg['Subject'] = 'Test Email from Direct Script'
body = 'This is a test email sent directly using SMTP to debug email configuration issues.'
msg.attach(MIMEText(body, 'plain'))

# Send the email
try:
    smtp = smtplib.SMTP(os.environ['EMAIL_HOST'], int(os.environ['EMAIL_PORT']))
    smtp.set_debuglevel(1)
    smtp.ehlo()
    
    if os.environ['EMAIL_USE_TLS'].lower() == 'true':
        smtp.starttls()
        smtp.ehlo()
    
    smtp.login(os.environ['EMAIL_HOST_USER'], os.environ['EMAIL_HOST_PASSWORD'])
    smtp.sendmail(os.environ['DEFAULT_FROM_EMAIL'], 'test@example.com', msg.as_string())
    smtp.quit()
    print('\\nEmail sent successfully!')
except Exception as e:
    print(f'\\nFailed to send email: {str(e)}')
\"" 