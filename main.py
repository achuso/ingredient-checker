from fastapi import FastAPI
from mangum import Mangum

from routes import auth_router, analyze_router, system_router

app = FastAPI()

# Routes
app.include_router(system_router)   # '/' and '/warm'
app.include_router(analyze_router)  # '/analyze'
app.include_router(auth_router)     # '/auth/login', '/auth/register', etc.

# AWS Lambda handler
handler = Mangum(app)
