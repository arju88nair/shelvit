from dotenv import load_dotenv
import os
load_dotenv()

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
MONGODB_SETTINGS = os.getenv('MONGODB_SETTINGS')
