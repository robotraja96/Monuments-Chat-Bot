# Import necessary libraries
from typing import Literal, TypedDict, Annotated
import operator
import uuid
import os

# LangChain and LangGraph specific imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel, Field
# Using Google Generative AI models
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

memory = InMemorySaver()

# --- 1. Define the Graph State ---
# The state will hold the messages and the chosen topic.


class AgentState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        messages: A list of messages in the conversation.
        topic: The esoteric topic identified by the triage agent.
    """
    messages: Annotated[list[BaseMessage], operator.add]
    topic: str  # Will hold 'alchemy', 'hermeticism', 'gnosticism', or 'general'

# --- 2. Define the Triage Agent with Structured Output ---

# Define the Pydantic model for structured output


class TopicClassifier(BaseModel):
    """
    Classifies the user's query into one of the predefined esoteric topics.
    """
    topic: Literal["alchemy", "hermeticism", "gnosticism", "general"] = Field(
        ...,
        description="The esoteric topic identified in the user's query. "
                    "Choose 'alchemy', 'hermeticism', 'gnosticism' if the query "
                    "is directly related to one of these. "
                    "Otherwise, choose 'general'."
    )

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# Initialize the LLM for the triage agent
# Using gemini-2.0-flash for triage
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=GOOGLE_API_KEY)

# Bind the structured output to the LLM
triage_llm = llm.with_structured_output(TopicClassifier)

# Define the prompt for the triage agent - NOW ACCEPTS ALL MESSAGES
triage_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a highly specialized triage agent. Your task is to classify "
               "the user's query into one of the following esoteric topics: "
               "'alchemy', 'hermeticism', 'gnosticism'. "
               "If the query does not clearly fit into these categories, classify it as 'general'.\n"
               "Consider the entire conversation history to make your decision.\n"
               "Respond ONLY with the structured output."),
               MessagesPlaceholder("messages"),
    # The prompt now uses the 'messages' variable to pass the full history
    # LangChain's ChatPromptTemplate can directly handle a list of BaseMessages
    # when passed to invoke or stream.
])

# Define the Triage Agent node function


def triage_agent_node(state: AgentState):
    """
    Node that classifies the user's query and updates the state with the identified topic.
    It now considers the entire conversation history for classification.
    """
    print("--- Triage Agent: Classifying query ---")
    # Pass all messages to the LLM for context
    all_messages = state["messages"]

    # Invoke the triage LLM with the structured output and the full message history
    # The ChatPromptTemplate will format the messages appropriately for the LLM
    response = triage_llm.invoke(
        triage_prompt.invoke({"messages": all_messages}))

    # Extract the topic from the structured response
    identified_topic = response.topic
    print(f"--- Triage Agent: Identified topic: {identified_topic} ---")

    # Return the updated state
    return {"topic": identified_topic}

# --- 3. Define the Esoteric Agents ---

# Initialize LLM for esoteric agents
# Using gemma-3n-e4b-it for esoteric agents
esoteric_llm = ChatGoogleGenerativeAI(model="gemma-3n-e4b-it")

# Define a generic prompt for esoteric agents - NOW ACCEPTS ALL MESSAGES
esoteric_prompt_template = ChatPromptTemplate.from_messages([
    ("human", "You are an expert on {topic}. Provide a concise and informative "
               "answer to the user's question, focusing solely on {topic}. "
               "Consider the entire conversation history for context."),
    MessagesPlaceholder("messages"), # Corrected: Use MessagesPlaceholder
])

# Define the Esoteric Agent node functions
def alchemy_agent_node(state: AgentState):
    """Node for the Alchemy expert agent."""
    print("--- Alchemy Agent: Answering query ---")
    all_messages = state["messages"] # Get all messages
    
    # Invoke the LLM with the alchemy-specific prompt and ALL messages
    # Corrected: Use prompt.invoke({"topic": ..., "messages": ...})
    response = esoteric_llm.invoke(esoteric_prompt_template.invoke(
        {"topic": "alchemy", "messages": all_messages}
    ))
    
    # Return the AI's response as a message
    return {"messages": [AIMessage(content=response.content)]}

def hermeticism_agent_node(state: AgentState):
    """Node for the Hermeticism expert agent."""
    print("--- Hermeticism Agent: Answering query ---")
    all_messages = state["messages"] # Get all messages
    # Corrected: Use prompt.invoke({"topic": ..., "messages": ...})
    response = esoteric_llm.invoke(esoteric_prompt_template.invoke(
        {"topic": "hermeticism", "messages": all_messages}
    ))
    return {"messages": [AIMessage(content=response.content)]}

def gnosticism_agent_node(state: AgentState):
    """Node for the Gnosticism expert agent."""
    print("--- Gnosticism Agent: Answering query ---")
    all_messages = state["messages"] # Get all messages
    # Corrected: Use prompt.invoke({"topic": ..., "messages": ...})
    response = esoteric_llm.invoke(esoteric_prompt_template.invoke(
        {"topic": "gnosticism", "messages": all_messages}
    ))
    return {"messages": [AIMessage(content=response.content)]}

def general_agent_node(state: AgentState):
    """Node for handling general queries (if no specific esoteric topic is identified)."""
    print("--- General Agent: Answering query ---")
    all_messages = state["messages"] # Get all messages
    # Corrected: Use prompt.invoke({"topic": ..., "messages": ...})
    response = esoteric_llm.invoke(esoteric_prompt_template.invoke(
        {"topic": "general esoteric knowledge", "messages": all_messages}
    ))
    return {"messages": [AIMessage(content=response.content)]}

# --- 4. Define the Conditional Edge Logic ---
def route_to_esoteric_agent(state: AgentState) -> str:
    """
    Determines the next node based on the 'topic' in the state.
    """
    topic = state["topic"]
    print(f"--- Router: Routing based on topic: {topic} ---")
    if topic == "alchemy":
        return "alchemy_agent"
    elif topic == "hermeticism":
        return "hermeticism_agent"
    elif topic == "gnosticism":
        return "gnosticism_agent"
    else:
        return "general_agent"

# --- 5. Build the LangGraph Graph ---
workflow = StateGraph(AgentState)


# Add nodes to the graph
workflow.add_node("triage_agent", triage_agent_node)
workflow.add_node("alchemy_agent", alchemy_agent_node)
workflow.add_node("hermeticism_agent", hermeticism_agent_node)
workflow.add_node("gnosticism_agent", gnosticism_agent_node)
workflow.add_node("general_agent", general_agent_node)

# Set the entry point
workflow.set_entry_point("triage_agent")

# Add conditional edge from triage agent
workflow.add_conditional_edges(
    "triage_agent",       # From this node
    route_to_esoteric_agent,  # Use this function to determine the next node
    {                     # Mapping of function return values to node names
        "alchemy_agent": "alchemy_agent",
        "hermeticism_agent": "hermeticism_agent",
        "gnosticism_agent": "gnosticism_agent",
        "general_agent": "general_agent",
    }
)

# Add edges from esoteric agents to END (since it's a single turn interaction)
workflow.add_edge("alchemy_agent", END)
workflow.add_edge("hermeticism_agent", END)
workflow.add_edge("gnosticism_agent", END)
workflow.add_edge("general_agent", END)

# Compile the graph
graph_app = workflow.compile(checkpointer=memory)


langgraph_thread_id = str(uuid.uuid4())  # Generate a random UUID
config = {"configurable": {"thread_id": langgraph_thread_id}}

# while True:
#     user_input = input("User: ")
#     if user_input.lower() == "exit":
#         break
#     for message_chunk, metadata in app.stream({"messages": [HumanMessage(content=user_input)], "topic": ""}, stream_mode="messages", config=config):
#         if message_chunk.content:
#             print(message_chunk.content, end="|", flush=True)

def astream_responses(messages):
    for message, metadata in graph_app.stream({"messages": messages, "topic": ""}, stream_mode="messages", config=config):
        yield f"data: {message.content}\n\n"


@app.get("/", response_class=HTMLResponse)
async def chatbox(request: Request):
    return templates.TemplateResponse("chatbox.html", {"request": request})

@app.get("/chat")
async def chat(query: str):
    return StreamingResponse(astream_responses([HumanMessage(content=query)]), media_type="text/event-stream")



