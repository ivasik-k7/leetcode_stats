from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.endpoints import router as statistic_router

app = FastAPI(
    title="LeetcodeStats",
    description="Simple Python API for Leetcode statistics",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(statistic_router, prefix="/api/v1/statistic", tags=["Statistic"])


@app.exception_handler(404)
async def custom_404_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": "Resource not found"},
    )


@app.exception_handler(500)
async def custom_500_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )


@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
