from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# Health check route
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Simple chatbot route (dummy echo for now)
@app.post("/api/chat")
async def chat(message: dict):
    user_input = message.get("text", "")
    return {"reply": f"You said: {user_input}"}
