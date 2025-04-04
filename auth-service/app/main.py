from fastapi import FastAPI
from app.api.v1.api import api_router


app = FastAPI()

# APIルーターの登録
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)