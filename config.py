MONGO_URI = "mongodb+srv://anshuaastha09:frxHxweaEf6Bw9nl@cluster0.xbycnex.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "fastapi_app"
JWT_SECRET = "Aastha123"  
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# import os
# from dotenv import load_dotenv
# from pymongo import MongoClient
#
# load_dotenv()
#
# MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
# client = MongoClient(MONGO_URI)
# db = client["myapp"]
# SECRET_KEY = os.getenv("SECRET_KEY", "secret123")
# ALGORITHM = "HS256"
