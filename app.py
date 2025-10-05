from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import httpx
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="Weather Summary API")

# Pydantic model for request validation
class LocationRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude must be between -90 and 90")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude must be between -180 and 180")
    
    @field_validator('latitude', 'longitude')
    def validate_coordinates(cls, v, field):
        if not isinstance(v, (int, float)):
            raise ValueError(f'{field.name} must be a valid number')
        return float(v)

# Pydantic model for response
class WeatherResponse(BaseModel):
    summary: str
    latitude: float
    longitude: float

# Open-Meteo API URL (hardcoded as requested)
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

async def fetch_weather_data(latitude: float, longitude: float) -> dict:
    """Fetch weather data from Open-Meteo API"""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m",
        "timezone": "auto"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(OPEN_METEO_URL, params=params, timeout=10.0)
            print(response.json())


            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to fetch weather data: {str(e)}")

async def get_gemini_summary(weather_data: dict) -> str:
    """Get human-like weather summary from Gemini LLM using Google client"""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not found in environment variables")
    
    # Extract weather information
    current = weather_data.get("current", {})
    temperature = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    
    # Create prompt for Gemini   #Based on this you can optimise your Prompt Token Usage (MONEY) and your LLM Response

    prompt = f"""Based on the following weather data. Generate me a 2 liner Summary.

Temperature: {temperature}°C
Humidity: {humidity}%

Make it conversational and include practical advice if relevant."""
    
    try:
        # Use Gemini 2.5 Flash model
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        
        if not response.text:
            raise HTTPException(status_code=502, detail="Gemini returned empty response")
        
        return response.text.strip()
        
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to get Gemini summary: {str(e)}")

@app.post("/weather-summary", response_model=WeatherResponse)
async def get_weather_summary(location: LocationRequest):
    """
    Get a human-like weather summary for the given coordinates.
    
    - **latitude**: Latitude coordinate (-90 to 90)
    - **longitude**: Longitude coordinate (-180 to 180)
    """
    try:
        # Step 1: Fetch weather data from Open-Meteo
        weather_data = await fetch_weather_data(location.latitude, location.longitude)
        
        # Step 2: Get AI summary from Gemini
        summary = await get_gemini_summary(weather_data)
        
        # Step 3: Return structured response
        return WeatherResponse(
            summary=summary,
            latitude=location.latitude,
            longitude=location.longitude
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Weather Summary API",
        "endpoint": "/weather-summary",
        "method": "POST",
        "example": {
            "latitude": 40.7128,
            "longitude": -74.0060
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)