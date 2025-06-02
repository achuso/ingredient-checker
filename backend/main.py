from fastapi import FastAPI
from mangum import Mangum

from routes import auth_router, analyze_router, system_router, scans_router

app = FastAPI()

app.include_router(system_router)    # '/' and '/warm'
app.include_router(analyze_router)   # '/analyze/process'
app.include_router(auth_router)      # '/auth/*'
app.include_router(scans_router)     # '/scans' and '/scans/{scan_id}'

# Lambda handler for AWS API Gateway
handler = Mangum(app)
