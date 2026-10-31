from fastapi import FastAPI

app = FastAPI(title="Subscription Management API")

@app.get("/")
def home():
    return {"message": "Backend is running!"}