from fastapi import FastAPI
from mangum import Mangum
from routes import upload

app = FastAPI()

# Routes
app.include_router(upload.router)

# AWS Lambda handler
handler = Mangum(app)