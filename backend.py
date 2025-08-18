from fastapi import FastAPI

# create a FastAPI app instance
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "🚀 Backend is running successfully on Railway!"}
