import os
import random
import re
from flask import render_template, Flask, request, jsonify, session
from langgraph.graph import StateGraph, END, START, add_messages
import smtplib
from email.mime.text import MIMEText
from langgraph.checkpoint.memory import MemorySaver
from email.mime.multipart import MIMEMultipart

import logging
from typing import Annotated, TypedDict, Optional

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import random
import re
from langchain_community.tools.tavily_search import TavilySearchResults

# Configure logging settings for debugging
logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG for extensive logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
import os
from dotenv import load_dotenv
load_dotenv()

# Configure environment variables for API keys and email service settings
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER", "your-email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "your-app-password")
EMAIL_SERVER = os.getenv("EMAIL_SERVER", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))

# Initialize Google's Generative AI model
logger.debug("Initializing LLM with model: gemini-2.0-flash-exp")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY)

# Initialize memory saver for conversation state
memory = MemorySaver()
application = None

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

def otp_length_check(text: str) -> bool:
    """
    Checks if the input contains exactly 6 digits.
    Returns True if the OTP is valid, otherwise False.
    """
    digits = re.findall(r'\d+', text)  # Extract digits only
    otp_candidate = ''.join(digits)  # Combine digit sequences

    # Check if the OTP is exactly 6 digits
    return len(otp_candidate)

# Helper function to extract 6-digit OTP from text
def extract_otp(text: str) -> Optional[str]:
    """Extract 6-digit OTP from text."""
    logger.debug(f"Extracting OTP from text: {text}")
    otp_pattern = r'\b\d{6}\b'
    match = re.search(otp_pattern, text)
    if match:
        logger.debug(f"OTP found: {match.group(0)}")
        return match.group(0)
    logger.debug("No OTP found")
    return None

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

# System prompt for the monument chatbot defining its behavior and capabilities
mon_prompt = """
You are a Monuments Researcher, an expert in historical monuments, their history, and their geographical locations. You only discuss topics related to historical monuments, their significance, and locations.
You also have ability to send email to users an OTP and verify it.
IsEmailVerificationStarted: {}
TASK: If the user mentions names of places, you should use the tools at your disposal to:
    - Identify a historical monument near that location.
    - Provide a brief history about it.
    - Mention how far it is from the specified place.
    - Your goal is to subtly and politely request the user's email so you can send them monument-related details, travel tips, or additional information.
    - If

STRICT GUIDELINES:

    - If the user asks something not relevant to monument, understand what they are saying and then reply that you are a monuments bot and you only talk about, monuments, their history and locations and significance.
    - Always stick to monuments and places; Any unrelated topics should be handled in a fun but strict way.
    - Guide the user slowly to provide their emails. First converse with them normally and then ask them for email details to provide detailed information on the queries.
    - When using tools, only query for monument details based on the relevant user-provided information.
    - Email is the only way to send details. Do not suggest any other methods

CRITICAL INSTRUCTIONS:
    - Do not ask for the user's email directly. First converse with them, ask leading question and provide suggestions about travel plans (ONLY RELATED TO HISTORICAL MONUMENTS) and clarify their queries. Once they are satisfied with the conversation, you can ask for their email.
    - Do not provide any information about the monuments directly. Use the tools to provide the information.
    - **Do not ever say you cant send email or verify email address. If the user mentions something about email, tell them that they can send their email and you will verify it.**
    - You can verify email and send otp. Never say you cannot verify or send OTP

SAMPLE CONVERSATION BETWEEN BOT AND USER:
Bot: Hey I am a historical agent AI, You can ask anything around it.
User: Hey, I am travelling to Noida next month for official work can you suggest me something
be visit.
Bot: Hey, have you visited Taj Mahal in Agra before?
User: No, this is my first visit to India.
Bot: Great, I think you must visit Taj Mahal in Agra, Agra is arnd 200Km from Noida and
once can easily take a cab from Noida to Agra.
User: Thanks.
Bot: If you can share your email, I can send few details related to Taj Mahal.
User: No Thanks, I am in a hurry. later.
Bot: There are many places arnd Agra which one should visit. Since you are leaving I
suggest you share your email and I can share lot of places to visit around.
User, Thanks, my email is abc@xyz.com
Bot: Thanks for providing your email will shoot an email your way soon.

NOTES: 
    - *ANSWER REGARDING MONUMENTS, PLACES OR ANYTHING RELATED TO MONUMENTS SHOULD BE GIVEN AFTER USING THE TOOL*
    - If IsEmailVerificationStarted is True, then you should only ask the user the OTP. If they try to talk something else, pls remind them politely to first verify the OTP. 
    - If IsEmailVerificationStarted is False, then you must converse like a Monuments Bot only.

"""

# Initialize system message and search tools


search_tool = TavilySearchResults(max_results=2)
tools = [search_tool]

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(tools)

# Define the structure for chat state
class BasicChatBot(TypedDict):
    messages: Annotated[list, add_messages]
    otp: Optional[str]
    user_email: Optional[str]
    otp_verified: Optional[bool]
    user_entered_otp: Optional[str]
    IsVerificationStarted: Optional[bool]

# Agent function to handle monument-related queries
def monument_agent(state: BasicChatBot):
    logger.debug("Entering monument_agent...")
    
    messages = state["messages"]
    verification_boolean = state["IsVerificationStarted"]
    sys_msg = SystemMessage(mon_prompt.format(verification_boolean))
    return {"messages": [llm_with_tools.invoke([sys_msg] + messages)]}

# Agent function to handle email and OTP verification process   
def verification_agent(state: BasicChatBot):
    logger.debug("Entering verification_agent...")
    
    if state["user_entered_otp"]:
        logger.debug("User entered OTP.")
        entered_otp = state["user_entered_otp"]
        rand_otp = state["otp"]
        logging.info(f"Entered OTP: {entered_otp}, Random OTP: {rand_otp}")
        if str(entered_otp) == str(rand_otp):
            logger.debug("OTP verified.")
            return {"messages": [AIMessage("Your email has been verified successfully. Will send you a message soon. Glad to be of help. Have a nice day!")]}
        else:
            logger.debug("OTP not verified.")
            return {"messages": [AIMessage("The OTP you have entered is incorrect. Please try again.")]}
        
    elif state["user_email"]:
        if not state["user_entered_otp"]:
            logger.debug("User email detected, starting verification...")
           
            user_email = state["user_email"]
            rand_otp = state["otp"]
            
            logger.debug(f"Generated OTP: {rand_otp}")
            is_email_sent = send_email_with_otp(user_email, rand_otp)

            if is_email_sent:
                logger.debug("Email sent successfully.")
                return {"messages": [AIMessage("I have sent an OTP to your email. Please enter the OTP to verify your email.")]}
            else:
                logger.error("Failed to send email.")
                return {"messages": [AIMessage("The email you have provided is invalid. Please provide a valid email address")]}
    else:
        logger.debug("No email provided.")
        
        return {"messages": [AIMessage("Please provide an email address to verify your email")]}

# Router function to direct conversation flow based on user input
def router(state: BasicChatBot):
    logger.debug("Entering router...")

    user_message = state["messages"][-1].content
    logger.debug(f"User message: {user_message}")
    
    user_entered_email = extract_email(str(user_message))
    user_entered_otp = extract_otp(str(user_message))

    if user_entered_email:
        logger.info("User entered email.")
        logger.debug(f"User email is: {user_entered_email}")
        return "email_verification"
    elif user_entered_otp:
        logger.info("User entered OTP.")
        rand_otp = state["otp"]
        if user_entered_otp == rand_otp:
            logger.debug("OTP verified.")
            return "email_verification"

        return "email_verification"
    else:
        logger.debug("No email or OTP detected. Routing to monuments_knowledge.")
        return "monuments_knowledge"

# Function to create and configure the conversation workflow graph
def create_graph():
    logger.debug("Creating LangGraph workflow...")
    global memory
    workflow = StateGraph(BasicChatBot)

    workflow.add_node("reasoner", monument_agent)
    workflow.add_node("email_verification", verification_agent)

    workflow.add_node("tools", ToolNode(tools)) # for the tools

    logger.debug("Adding conditional edges...")
    workflow.add_conditional_edges(START, router, {
        "monuments_knowledge": "reasoner",
        "email_verification": "email_verification",
    })

    workflow.add_conditional_edges("reasoner", tools_condition,)
    workflow.add_edge("tools", "reasoner")
    workflow.add_edge("email_verification", END)

    logger.debug("Compiling workflow...")
    app = workflow.compile(checkpointer=memory)
    logger.debug("Workflow compilation complete.")
    return app

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Create the graph application
application = create_graph()
config = {"configurable": {"thread_id": "1"}}

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route to initialize a new chat session
@app.route('/init_session', methods=['POST'])
def init_session():
    """Initialize a new chat session"""
    session['random_otp'] = random.randint(100000, 999999)
    session['otp_verified'] = False
    session['user_email'] = None
    session['messages'] = []
    session["IsVerificationStarted"] = False
    
    logger.debug(f"New session initialized with OTP: {session['random_otp']}")
    return jsonify({"status": "success", "message": "Session initialized"})

# Main chat endpoint to handle user messages
@app.route('/chat', methods=['POST'])
def chat():
    """Process user message and return bot response"""

    global memory, application, config
    data = request.json
    user_message = data.get('message', '')
    
    # Add the user message to the session message history
    if 'messages' not in session:
        session['messages'] = []
    
    session['messages'].append(user_message)
    
    # Check if OTP is already verified
    if session.get('otp_verified', False):
        return jsonify({
            "response": "Thank you for your verification. Session is complete.",
            "session_complete": True
        })
    
    # Process the message based on its content
    if extract_email(user_message):
        user_email = extract_email(user_message)
        session['user_email'] = user_email
        
        response = application.invoke({
            "messages": [HumanMessage(user_message)], 
            "user_email": user_email,
            "IsVerificationStarted": True, 
            "otp": session['random_otp'], 
            "user_entered_otp": "",
            "otp_verified": False
        }, config=config)
        
        bot_response = response["messages"][-1].content
        session["IsVerificationStarted"] = True
        
    elif (extract_otp(user_message) or otp_length_check(user_message) > 1) and session.get('IsVerificationStarted', False):
        user_entered_otp = extract_otp(user_message)

        # ✅ Check if OTP contains exactly 6 digits
        if otp_length_check(user_message) != 6:
            logging.info("Entered length check condition")
            return jsonify({
                "response": "Invalid OTP. Please provide a valid 6-digit OTP.",
                "session_complete": False
            })
        
        response = application.invoke({
            "messages": [HumanMessage(user_message)], 
            "user_entered_otp": user_entered_otp, 
            "otp": session['random_otp'], 
            "user_email": session.get('user_email', ''),
            "IsVerificationStarted": True,
            "otp_verified": False
        }, config=config)
        
        bot_response = response["messages"][-1].content
        
        # Check if OTP is verified
        if str(user_entered_otp) == str(session['random_otp']):
            session['otp_verified'] = True

            memory = MemorySaver()  # Create a new memory instance
            application = create_graph()  # Recreate the graph with fresh memory
            
            # Also clear the session messages
            session['messages'] = []

            return jsonify({
                "response": bot_response,
                "session_complete": True
            })
        
        else:
            return jsonify({
                "response": "The OTP you have entered is incorrect. Please try again.",
                "session_complete": False
            })
    else:
        response = application.invoke({
            "messages": [HumanMessage(user_message)],
            "otp": session.get('random_otp', random.randint(100000, 999999)),
            "user_email": session.get('user_email', ''),
            "user_entered_otp": "",
            "IsVerificationStarted": False,
            "otp_verified": False
        }, config=config)
        
        bot_response = response["messages"][-1].content
    
    return jsonify({
        "response": bot_response,
        "session_complete": session.get('otp_verified', False)
    })

# Route to reset the chat session
@app.route('/reset_session', methods=['POST'])
def reset_session():
    """Reset the entire chat session"""
    global memory, application, config
    
    # Create fresh instances
    memory = MemorySaver()
    application = create_graph()
    
    # Clear Flask session data
    session.clear()
    
    # Initialize a new session
    session['random_otp'] = random.randint(100000, 999999)
    session['otp_verified'] = False
    session['user_email'] = None
    session['messages'] = []
    
    logger.debug("Session completely reset")
    return jsonify({"status": "success", "message": "Session reset"})

# Run the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)