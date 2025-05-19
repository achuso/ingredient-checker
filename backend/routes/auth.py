from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel, EmailStr

from services.auth import login
from services.auth import register

from typing import List

router = APIRouter(prefix="/auth", tags=["auth"])

# Request models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class UpdateRestrictionsRequest(BaseModel):
    restriction_ids: List[str]

# Endpoints
@router.post("/login")
async def login_user(data: LoginRequest):
    return await login.login_user(data.email, data.password)

@router.post("/register")
async def register_user(data: RegisterRequest):
    return await register.register_user(data.email, data.password)

# NOT IMPLEMENTED YET
@router.post("/forgot_password")
async def forgot_password(data: ForgotPasswordRequest):
    return {"message": f"Forgot password triggered for {data.email}"}
@router.put("/user/update_restrictions")
async def update_restrictions(data: UpdateRestrictionsRequest):
    return {"message": "Restrictions updated", "restrictions": data.restriction_ids}
