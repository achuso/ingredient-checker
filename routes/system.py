from fastapi import APIRouter, Response

router = APIRouter()

@router.get("/")
def list_routes():
    return {"message": "Ingredient Checker API is up and alive!"}

 # Just a warm-up run by clients periodically, can't afford server cron :(
@router.get("/warm")
def warm():
    return Response(status_code=204)
