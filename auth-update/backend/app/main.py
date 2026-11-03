from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, admin

app = FastAPI(title="Smart Hospital Queue System")

# React frontend (Vite) ko backend se baat karne ki ijazat
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/")
def home():
    return {"message": "Smart Hospital API chal rahi hai"}
