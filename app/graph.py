# Basic imports
import os
import logging
from typing import Annotated, TypedDict, Optional

# LangGraph and Langchain imports
from langgraph.graph import StateGraph, END, START, add_messages
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
from langgraph.checkpoint.memory import InMemorySaver
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Custom imports
from utils import message_parser
from prompts import mon_prompt, verification_prompt

# FastAPI imports

# Configure logging settings for debugging
logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG for extensive logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
import os
from dotenv import load_dotenv
load_dotenv()

# Configure environment variables for API keys and email service settings
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Google's Generative AI model
logger.debug("Initializing LLM with model: gemini-2.0-flash-exp")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY)

# Initialize memory saver for conversation state
memory = InMemorySaver()

# search tools

search_tool = TavilySearchResults(max_results=2)
tools = [search_tool]


# Define the structure for chat state
class BasicChatBot(TypedDict):
    messages: Annotated[list, add_messages]
    otp: Optional[str]
    IsVerificationStarted: Optional[bool]


# Router function to direct conversation flow based on user input
def router(state = BasicChatBot):
    logger.debug("Entering router...")
    if state["IsVerificationStarted"]:
        return "email_verification"
    else:
        return "monuments_knowledge"

# Agent function to handle monument-related queries
def monument_agent(state: BasicChatBot):
    logger.debug("Entering monument_agent...")
    
    messages = state["messages"]
    agent = create_react_agent(model=llm, tools=tools, prompt=mon_prompt)
    response = agent.invoke({"messages":messages})
    logger.debug(f"Agent response: {response}")
    return {"messages": response["messages"]}

# Agent function to handle email and OTP verification process   
def verification_agent(state: BasicChatBot):
    logger.debug("Entering verification_agent...")
    
    user_message = state["messages"][-1].content
    generated_otp = state["otp"]
    verification_instruction = PromptTemplate.from_template(template=verification_prompt)
    verification_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY)
    verification_message = verification_llm.invoke(verification_instruction.invoke({"user_message":user_message, "generated_otp":generated_otp})).content.strip()
    return {"messages":verification_message}


        


# Function to create and configure the conversation workflow graph
def create_graph():
    logger.debug("Creating LangGraph workflow...")
    workflow = StateGraph(BasicChatBot)

    workflow.add_node("reasoner", monument_agent)
    workflow.add_node("email_verification", verification_agent)
    logger.debug("Adding conditional edges...")
    workflow.add_conditional_edges(START, router, {
        "monuments_knowledge": "reasoner",
        "email_verification": "email_verification",
    })

    workflow.add_edge("reasoner", END)
    workflow.add_edge("email_verification", END)

    logger.debug("Compiling workflow...")
    app = workflow.compile(checkpointer=memory)
    logger.debug("Workflow compilation complete.")
    return app


