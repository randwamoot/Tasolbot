import smtplib
import socket
import re

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_gmail_address(email):
    return email.lower().endswith('@gmail.com') or email.lower().endswith('@googlemail.com')

def check_email_exists(email):
    """Direct Google SMTP Checker without Telegram drama"""
    if not is_valid_email(email) or not is_gmail_address(email):
        return False, "Invalid Gmail Format"
    
    try:
        mx_host = 'gmail-smtp-in.l.google.com'
        server = smtplib.SMTP()
        server.timeout = 10
        
        server.connect(mx_host, 25)
        server.helo(server.local_hostname)
        server.mail('test@example.com')
        
        code, message = server.rcpt(email)
        server.quit()
        
        if code == 250:
            return True, "Email address exists"
        else:
            return False, "Email address does not exist"
            
    except Exception as e:
        # IP Block ya Network issue hone par fallback safety
        return False, f"Check Failed: {str(e)}"
