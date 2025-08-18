from fastapi import FastAPI, APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import hashlib
import jwt
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "safezone-secret-key-change-in-production"
ALGORITHM = "HS256"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    street: str
    number: str
    neighborhood: str
    resident_names: List[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    street: str
    number: str
    neighborhood: str
    resident_names: List[str]

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    street: str
    number: str
    neighborhood: str
    resident_names: List[str]

class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    payment_method: str  # credit-card, pix, boleto
    status: str = "active"  # active, cancelled, expired
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    next_payment: datetime
    is_trial: bool = True
    amount: float = 30.00
    billing_cycle: str = "monthly"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SubscriptionCreate(BaseModel):
    payment_method: str
    card_number: Optional[str] = None
    card_name: Optional[str] = None
    card_expiry: Optional[str] = None
    card_cvv: Optional[str] = None

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # invasão, roubo, emergência
    user_id: str
    user_name: str
    street: str
    number: str
    neighborhood: str
    location: Optional[dict] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class AlertCreate(BaseModel):
    type: str

class AlertResponse(BaseModel):
    id: str
    type: str
    user_name: str
    street: str
    number: str
    neighborhood: str
    timestamp: str
    is_active: bool

class PaymentResponse(BaseModel):
    success: bool
    message: str
    payment_url: Optional[str] = None
    pix_code: Optional[str] = None
    boleto_url: Optional[str] = None

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = security):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    """Parse datetime strings back from MongoDB"""
    if isinstance(item, dict):
        for key, value in item.items():
            if key in ['created_at', 'timestamp', 'start_date', 'next_payment'] and isinstance(value, str):
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
    return item

# Routes
@api_router.get("/")
async def root():
    return {"message": "SafeZone API - Segurança Comunitária"}

# Authentication routes
@api_router.post("/register")
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    user = User(
        name=user_data.name,
        email=user_data.email,
        street=user_data.street,
        number=user_data.number,
        neighborhood=user_data.neighborhood,
        resident_names=user_data.resident_names
    )
    
    # Store user with hashed password
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    user_dict = prepare_for_mongo(user_dict)
    
    await db.users.insert_one(user_dict)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    response_user = UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        street=user.street,
        number=user.number,
        neighborhood=user.neighborhood,
        resident_names=user.resident_names
    )
    
    return {"user": response_user, "access_token": access_token, "token_type": "bearer"}

@api_router.post("/login")
async def login_user(login_data: UserLogin):
    # Find user by email
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    # Verify password
    if not verify_password(login_data.password, user_doc["password"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    # Create access token
    access_token = create_access_token(data={"sub": user_doc["id"]})
    
    user_doc = parse_from_mongo(user_doc)
    response_user = UserResponse(
        id=user_doc["id"],
        name=user_doc["name"],
        email=user_doc["email"],
        street=user_doc["street"],
        number=user_doc["number"],
        neighborhood=user_doc["neighborhood"],
        resident_names=user_doc["resident_names"]
    )
    
    return {"user": response_user, "access_token": access_token, "token_type": "bearer"}

# Payment routes
@api_router.post("/create-subscription")
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_user)
):
    # Check if user already has an active subscription
    existing_sub = await db.subscriptions.find_one({
        "user_id": current_user.id,
        "status": "active"
    })
    
    if existing_sub:
        raise HTTPException(status_code=400, detail="Usuário já possui assinatura ativa")
    
    # Calculate next payment date (1 month from now for trial)
    next_payment = datetime.now(timezone.utc) + timedelta(days=30)
    
    # Create subscription
    subscription = Subscription(
        user_id=current_user.id,
        payment_method=subscription_data.payment_method,
        next_payment=next_payment
    )
    
    subscription_dict = subscription.dict()
    subscription_dict = prepare_for_mongo(subscription_dict)
    
    await db.subscriptions.insert_one(subscription_dict)
    
    # Generate payment response based on method
    payment_response = PaymentResponse(success=True, message="Assinatura criada com sucesso!")
    
    if subscription_data.payment_method == "pix":
        payment_response.pix_code = "09b74dd4-64da-4563-b769-95cec83659f0"
        payment_response.message = "Use o código PIX para pagamento instantâneo"
    elif subscription_data.payment_method == "boleto":
        payment_response.boleto_url = "https://exemplo.com/boleto/123456"
        payment_response.message = "Boleto gerado com sucesso. Vencimento em 2 dias úteis."
    elif subscription_data.payment_method == "credit-card":
        # In production, this would integrate with Mercado Pago
        payment_response.payment_url = "link.mercadopago.com.br/hopez"
        payment_response.message = "Cartão processado com sucesso!"
    
    return payment_response

# Alert routes
@api_router.post("/alerts")
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user)
):
    alert = Alert(
        type=alert_data.type,
        user_id=current_user.id,
        user_name=current_user.resident_names[0] if current_user.resident_names else current_user.name,
        street=current_user.street,
        number=current_user.number,
        neighborhood=current_user.neighborhood,
        location={
            "lat": -23.55 + (0.01 * hash(current_user.id) % 100 - 50) / 5000,
            "lng": -46.63 + (0.01 * hash(current_user.id) % 100 - 50) / 5000
        }
    )
    
    alert_dict = alert.dict()
    alert_dict = prepare_for_mongo(alert_dict)
    
    await db.alerts.insert_one(alert_dict)
    
    return {"message": f"Alerta de {alert_data.type} enviado com sucesso!", "alert_id": alert.id}

@api_router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(current_user: User = Depends(get_current_user)):
    # Get alerts from same neighborhood
    alerts_cursor = db.alerts.find({
        "neighborhood": current_user.neighborhood,
        "is_active": True
    }).sort("timestamp", -1).limit(10)
    
    alerts = await alerts_cursor.to_list(length=None)
    
    response_alerts = []
    for alert in alerts:
        alert = parse_from_mongo(alert)
        response_alerts.append(AlertResponse(
            id=alert["id"],
            type=alert["type"],
            user_name=alert["user_name"],
            street=alert["street"],
            number=alert["number"],
            neighborhood=alert["neighborhood"],
            timestamp=alert["timestamp"].strftime("%d/%m/%Y %H:%M"),
            is_active=alert["is_active"]
        ))
    
    return response_alerts

@api_router.put("/alerts/{alert_id}/stop")
async def stop_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    # Only allow the alert creator to stop it
    result = await db.alerts.update_one(
        {"id": alert_id, "user_id": current_user.id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    
    return {"message": "Alerta interrompido com sucesso"}

# User profile route
@api_router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        street=current_user.street,
        number=current_user.number,
        neighborhood=current_user.neighborhood,
        resident_names=current_user.resident_names
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()