"""Configuration settings"""
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    stripe_secret_key: str = Field(..., env="STRIPE_SECRET_KEY")
    tavily_api_key: str = Field(..., env="TAVILY_API_KEY")
    firecrawl_api_key: str = Field(..., env="FIRECRAWL_API_KEY")
    
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4000
    
    weight_price: float = 0.30
    weight_availability: float = 0.20
    weight_quality: float = 0.20
    weight_time: float = 0.10
    weight_risk: float = 0.10
    weight_distance: float = 0.10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
