import uuid
import random
from graph import create_graph
from utils import message_parser, stream_graph
from langchain_core.messages import HumanMessage
from fastapi import FastAPI, Request, Path, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Annotated

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


graph_app = create_graph()
session = {}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    new_thread = str(uuid.uuid4())
    random_otp = random.randint(100000, 999999)
    session[new_thread] = {"otp": random_otp,
                           "verification_started": False, "is_verified": False}
    return templates.TemplateResponse("chatbox.html", {"request": request, "thread_id": new_thread})


@app.get("/chat")
async def chat(query: Annotated[str, Path(..., title="User query", description="User query")],
               thread_id: Annotated[str, Query(..., title="Thread ID", description="Thread ID")]):
    state_vars = session[thread_id]
    new_state_vars = message_parser(var_dict=state_vars, user_message=query)
    session[thread_id] = new_state_vars
    config = {"configurable": {"thread_id": thread_id}}

    return StreamingResponse(stream_graph(
        graph_app, config, query, state_vars["otp"], state_vars["verification_started"]), media_type="text/event-stream")

# if __name__ == "__main__":
#     while not is_done:
#         user_message = str(input("USER:"))
#         if user_message.lower() == "exit":
#             is_done = True
#             break

#         state_vars = message_parser(var_dict=state_vars, user_message=user_message)
#         is_verification = state_vars["verification_started"]
#         is_verified = state_vars["is_verified"]
#         print(f"Is verification started: {is_verification}")
#         print(f"Is verified: {is_verified}")

#         for message_chunk, metadata in graph_app.stream({"messages": [HumanMessage(content=user_message)],
#                                                         "otp":random_otp,
#                                                         "IsVerificationStarted":is_verification},stream_mode="messages", config=config):
#             if message_chunk.content:
#                 print(message_chunk.content, end="|", flush=True)
#         if is_verified:
#             print("\nOTP verified successfully. You can now proceed with the session.")
#             is_done = True
#             break


