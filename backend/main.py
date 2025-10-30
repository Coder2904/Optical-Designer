"""
Optical Setup Simulation Backend

Copy the complete backend code from the FastAPI artifact here.
The code includes:
- OpticalPhysics class
- RayTracer class
- FrequencySweepAnalyzer class
- All API endpoints
"""

from fastapi import FastAPI

app = FastAPI(title="Optical Simulation API")

@app.get("/")
async def root():
    return {"message": "Please copy the complete backend code from the artifact"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
