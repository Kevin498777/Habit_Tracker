# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/habit_tracker')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')