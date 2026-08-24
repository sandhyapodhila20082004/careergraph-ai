import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "default-dev-key")
    
    # CognoDB / Neo4j Connection Credentials
    COGNODB_URI = os.getenv("COGNODB_URI", "bolt://localhost:7687")
    COGNODB_USERNAME = os.getenv("COGNODB_USERNAME", "cognodb")
    COGNODB_PASSWORD = os.getenv("COGNODB_PASSWORD", "")
    
    # Driver config
    MAX_CONNECTION_LIFETIME = 3600
    MAX_CONNECTION_POOL_SIZE = 50
    CONNECTION_TIMEOUT = 5.0  # seconds