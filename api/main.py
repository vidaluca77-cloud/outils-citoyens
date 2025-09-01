from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import time
import openai
from openai import OpenAI
from typing import Dict, Any, List
import logging
from jinja2 import Template
import prompting

app = FastAPI(title="Outils Citoyens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://outils-citoyens-three.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# Include chat router
try:
    from chat import router as chat_router
    app.include_router(chat_router)
except ImportError:
    logger.warning("Chat router not available")

# Include legal router  
try:
    from legal.router import router as legal_router
    app.include_router(legal_router)
except ImportError:
    logger.warning("Legal router not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
