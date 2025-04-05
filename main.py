from fastapi import FastAPI
from mangum import Mangum

from routes import analyze
from routes import system

app = FastAPI()

# Routes
app.include_router(system.router)   # '/' and '/warm'
app.include_router(analyze.router)  # '/analyze'

# AWS Lambda handler
handler = Mangum(app)