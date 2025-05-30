
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain_core.messages import HumanMessage, AIMessage
from langfuse.callback import CallbackHandler
import re
from typing import Optional
import logging
import os

# Configure logging settings for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER", "your-email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "your-app-password")
EMAIL_SERVER = os.getenv("EMAIL_SERVER", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL")




def get_langfuse_handler():
    langfuse_handler = CallbackHandler(
    public_key=LANGFUSE_PUBLIC_KEY,
    secret_key=LANGFUSE_SECRET_KEY,
    host=LANGFUSE_BASE_URL
)
    return langfuse_handler

# Helper function to extract email using regex pattern
def extract_email(text: str) -> Optional[str]:
    """Extract email from text using regex."""
    logger.debug(f"Extracting email from text: {text}")
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    if match:
        logger.debug(f"Email found: {match.group(0)}")
        return match.group(0)
    logger.debug("No email found")
    return None



# Helper function to extract 6-digit OTP from text
def extract_otp(text: str) -> tuple[str, bool]:
    """Extract 6-digit OTP from text."""
    logger.debug(f"Extracting OTP from text: {text}")
    otp_pattern = r'(?<!\d)\d{6}(?!\d)'
    match = re.search(otp_pattern, text)
    if match:
        logger.debug(f"OTP found: {match.group(0)}")
        return match.group(0), True
    logger.debug("No OTP found")
    return "", False

# Function to send OTP via email using SMTP
def send_email_with_otp(to_email: str, otp: str) -> bool:
    """Send email with OTP to the user."""
    logger.debug(f"Preparing to send OTP email to: {to_email} with OTP: {otp}")
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = "Your OTP for Historical Monuments Bot"
        
        body = f"""
        Hello,
        
        Thank you for your interest in historical monuments!
        
        Your OTP for email verification is: {otp}
        
        Please enter this code in our chat to complete the verification.
        
        Best Regards,
        Historical Monuments Bot
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        logger.debug("Connecting to email server...")
        server = smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_APP_PASSWORD)
        
        logger.debug("Sending email...")
        server.send_message(msg)
        server.quit()
        
        logger.info(f"OTP email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def message_parser(user_message: str, var_dict: dict) -> dict:
    """
    Parse user message and update session variables accordingly.
    Returns updated var_dict.
    """
    # Create a copy to avoid modifying the original
    updated_dict = var_dict.copy()
    
    # Check for OTP verification first
    user_otp, is_otp = extract_otp(user_message)
    gen_otp = updated_dict.get("otp", "000000")
    
    if is_otp and str(user_otp) == str(gen_otp):
        updated_dict["is_verified"] = True
        logger.info("User OTP verified successfully in message parser.")
        return updated_dict
    
    # Check for email if verification hasn't started
    if not updated_dict.get("verification_started", False):
        user_email = extract_email(user_message)
        if user_email:
            if send_email_with_otp(user_email, str(gen_otp)):
                updated_dict["verification_started"] = True
                updated_dict["user_email"] = user_email
                logger.info(f"Email verification started for {user_email}")
            else:
                logger.error("Failed to send OTP email")
    
    return updated_dict

def stream_graph(graph_app, configuration, user_message, random_otp, is_verification):
    """
    Stream graph responses with proper error handling.
    """
    try:
        for message, metadata in graph_app.stream(
            {
                "messages": [HumanMessage(content=user_message)], 
                "otp": random_otp, 
                "IsVerificationStarted": is_verification
            }, 
            stream_mode="messages", 
            config=configuration
        ):
            if hasattr(message, 'content') and message.content and isinstance(message, AIMessage):
                yield f"data: {message.content}\n\n"
    except Exception as e:
        logger.error(f"Error in stream_graph: {str(e)}")
        yield f"data: Sorry, there was an error processing your request.\n\n"