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
from typing import Annotated, Sequence, TypedDict, Optional

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent, ToolNode, tools_condition
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import random
import re
from langchain_community.tools.tavily_search import TavilySearchResults

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG for extensive logging
logger = logging.getLogger(__name__)

import os
from dotenv import load_dotenv
load_dotenv()

# Configure environment variables for OpenAI and email service
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER", "your-email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "your-app-password")
EMAIL_SERVER = os.getenv("EMAIL_SERVER", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))

# Initialize LLM
logger.debug("Initializing LLM with model: gemini-2.0-flash-exp")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY)

memory = MemorySaver()
application = None
# Helper functions
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




mon_prompt = """
You are a Monuments Researcher, an expert in historical monuments, their history, and their geographical locations. You only discuss topics related to historical monuments, their significance, and locations.

TASK: If the user mentions names of places, you should use the tools at your disposal to:
    - Identify a historical monument near that location.
    - Provide a brief history about it.
    - Mention how far it is from the specified place.
    - Your goal is to subtly and politely request the user's email so you can send them monument-related details, travel tips, or additional information.

Strict Guidelines:

    - If the user asks about general, personal, or derogatory topics, remind them that you are only a Monuments Conversational Bot and that you specialize in monuments, travel, and history.
    - Always stick to monuments and places; do not entertain unrelated discussions.
    - You should guide the user to provide their email address so that you can send details. Persuade them to your best if they do not provide it. If they refuse plainly say "No problem. Thank you, Have a nice day". But do this only after trying a few times to get their email.
    - When using tools, only query for monument details based on the relevant user-provided information.
    - Do not ask user for any other ways of sending. Email is the only way to send details.

CRITICAL INSTRUCTIONS:
    - Do not ask for the user's email directly. First converse with them, ask leading question and provide suggestions about travel plans (ONLY RELATED TO HISTORICAL MONUMENTS) and clarify their queries. Once they are satisfied with the conversation, you can ask for their email.
    - Do not provide any information about the monuments directly. Use the tools to provide the information.

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

NOTE: *ANSWER REGARDING MONUMENTS, PLACES OR ANYTHING RELATED TO MONUMENTS SHOULD BE GIVEN AFTER USING THE TOOL*
"""

sys_msg = SystemMessage(mon_prompt)

search_tool = TavilySearchResults(max_results=2)
tools = [search_tool]


llm_with_tools = llm.bind_tools(tools)

class BasicChatBot(TypedDict):
    messages: Annotated[list, add_messages]
    otp: Optional[str]
    user_email: Optional[str]
    otp_verified: Optional[bool]
    user_entered_otp: Optional[str]
    IsVerificationStarted: Optional[bool]



def monument_agent(state: BasicChatBot):
    logger.debug("Entering monument_agent...")
    
    messages = state["messages"]
    return {"messages": [llm_with_tools.invoke([sys_msg] + messages)]}
   


def verification_agent(state: BasicChatBot):
    logger.debug("Entering verification_agent...")
    # logging.info(f"State: {state}")

    
        
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
            # state["IsVerification_Started"] = True
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


# Node


def router(state: BasicChatBot):
    logger.debug("Entering router...")

    user_message = state["messages"][-1].content
    logger.debug(f"User message: {user_message}")
    
    user_entered_email = extract_email(str(user_message))
    user_entered_otp = extract_otp(str(user_message))

    if user_entered_email:
        logger.info("User entered email.")
        # state["user_email"] = user_entered_email
        logger.debug(f"User email is: {user_entered_email}")
        return "email_verification"
    elif user_entered_otp:
        logger.info("User entered OTP.")
        rand_otp = state["otp"]
        if user_entered_otp == rand_otp:
            logger.debug("OTP verified.")
            return "email_verification"

        # state["user_entered_otp"] = user_entered_otp
        return "email_verification"
    else:
        logger.debug("No email or OTP detected. Routing to monuments_knowledge.")
        return "monuments_knowledge"


# Define the LangGraph workflow
def create_graph():
    logger.debug("Creating LangGraph workflow...")
    global memory
    workflow = StateGraph(BasicChatBot)

    workflow.add_node("reasoner", monument_agent)
    workflow.add_node("email_verification", verification_agent)
    # Add nodes
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






# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Create the graph application

application = create_graph()
config = {"configurable": {"thread_id": "1"}}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init_session', methods=['POST'])
def init_session():
    """Initialize a new chat session"""
    session['random_otp'] = random.randint(100000, 999999)
    session['otp_verified'] = False
    session['user_email'] = None
    session['messages'] = []
    
    logger.debug(f"New session initialized with OTP: {session['random_otp']}")
    return jsonify({"status": "success", "message": "Session initialized"})

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
        
    elif extract_otp(user_message):
        user_entered_otp = extract_otp(user_message)
        
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

if __name__ == '__main__':
    # Make sure the templates folder exists
    # if not os.path.exists('templates'):
    #     os.makedirs('templates')
    
    # # Save the index.html to templates folder
    # with open('templates/index.html', 'w') as f:
    #     with open('index.html', 'r') as source:
    #         f.write(source.read())
    
    app.run(host='0.0.0.0', debug=True, port=8080)