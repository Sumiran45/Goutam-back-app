from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routes import activity, auth, shop, articles, admin, user, doctor, symptoms
from database import init_indexes, db

app = FastAPI()
@app.on_event("startup")
async def startup_event():
    await init_indexes()

@app.middleware("http")
async def log_request(request: Request, call_next):
    print(f"Request method: {request.method}")
    print(f"Request headers: {request.headers}")
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081","http://127.0.0.1:8081","*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Custom-Header"],  # Allowed headers
)

doctor_collection = db["doctors"]

async def create_geo_index():
    await doctor_collection.create_index([("location", "2dsphere")])

app.include_router(auth.router)
app.include_router(shop.product_router)
app.include_router(articles.router)
app.include_router(admin.router)
app.include_router(user.router)
app.include_router(doctor.router)
app.include_router(activity.router)
app.include_router(symptoms.router)


