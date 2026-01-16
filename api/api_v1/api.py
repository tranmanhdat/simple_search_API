from fastapi import FastAPI, APIRouter
from endpoint import router
api_router = APIRouter()

api_router.add_api_route("/", router=router, tags=["API V1"])