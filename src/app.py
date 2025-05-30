from src.graph import create_graph
from src.utils import message_parser, stream_graph, get_langfuse_handler
from src.session_manager import SessionManager
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Annotated
import uuid
import logging



# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


graph_app = create_graph()

# Langfuse handler
langfuse_handler = get_langfuse_handler()

  

# Global session manager
session_manager = SessionManager()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    new_thread = str(uuid.uuid4())
    session_manager.create_session(new_thread)
    return templates.TemplateResponse("chatbox.html", {
        "request": request, 
        "thread_id": new_thread
    })

@app.get("/session-status/{thread_id}")
async def get_session_status(thread_id: str):
    """Endpoint to check session status"""
    session = session_manager.get_session(thread_id)
    if not session:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    
    return JSONResponse({
        "session_active": session["session_active"],
        "is_verified": session["is_verified"],
        "verification_started": session["verification_started"]
    })

@app.get("/chat")
async def chat(query: Annotated[str, Query(..., title="User query", description="User query")],
               thread_id: Annotated[str, Query(..., title="Thread ID", description="Thread ID")]):
    
    session = session_manager.get_session(thread_id)
    if not session:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    
    # Check if session is still active
    if not session["session_active"]:
        return JSONResponse({"error": "Session has been terminated"}, status_code=403)
    
    logger.info(f"Received query: {query}")
    
    # Parse the message and update session
    updated_session = message_parser(var_dict=session.copy(), user_message=query)
    session_manager.update_session(thread_id, updated_session)
    
    # Get updated session state
    current_session = session_manager.get_session(thread_id)
    langfuse_handler.session_id = thread_id
    config = {"configurable": {"thread_id": thread_id}, "callbacks":[langfuse_handler]}
    
    def generate_response():
        for chunk in stream_graph(
            graph_app, 
            config, 
            query, 
            current_session["otp"], 
            current_session["verification_started"]
        ):
            yield chunk
        
        # After streaming is complete, check if we need to terminate
        final_session = session_manager.get_session(thread_id)
        if final_session and final_session["is_verified"]:
            # Send termination signal to frontend
            yield f"data: __SESSION_TERMINATED__\n\n"
            # Terminate the session
            session_manager.terminate_session(thread_id)
    
    return StreamingResponse(generate_response(), media_type="text/event-stream")

@app.delete("/session/{thread_id}")
async def cleanup_session(thread_id: str):
    """Endpoint to cleanup session when user starts new chat"""
    session_manager.cleanup_session(thread_id)
    return JSONResponse({"message": "Session cleaned up"})



