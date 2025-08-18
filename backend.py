from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "🚀 Backend is running successfully on Railway!"}

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Chat API
@app.post("/api/chat")
async def chat(message: dict):
    user_input = message.get("text", "")
    return {"reply": f"You said: {user_input}"}
