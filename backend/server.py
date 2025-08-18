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
    state: str  # Estado (ex: SP, RJ, MG)
    city: str   # Cidade (ex: São Paulo, Rio de Janeiro)
    neighborhood: str  # Bairro (ex: Centro, Vila Olímpia)
    street: str  # Rua (ex: Rua das Flores, Av. Paulista)
    number: str  # Número (ex: 123, 456-A)
    resident_names: List[str]
    is_admin: bool = False
    is_vip: bool = False
    vip_expires_at: Optional[datetime] = None  # None = permanent VIP
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    state: str
    city: str
    neighborhood: str
    street: str
    number: str
    resident_names: List[str]

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    state: str
    city: str
    neighborhood: str
    street: str
    number: str
    resident_names: List[str]
    is_admin: bool = False
    is_vip: bool = False
    vip_expires_at: Optional[str] = None

class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    payment_method: str  # credit-card, pix, boleto
    status: str = "trial"  # trial, active, overdue, blocked, cancelled, expired
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    trial_end_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=30))
    next_payment: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=30))
    payment_due_date: Optional[datetime] = None  # Data limite para pagamento (trial_end + 5 dias)
    grace_period_end: Optional[datetime] = None  # Fim do período de graça
    is_trial: bool = True
    amount: float = 30.00
    billing_cycle: str = "monthly"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_payment_date: Optional[datetime] = None
    blocked_at: Optional[datetime] = None

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
    state: str
    city: str
    neighborhood: str
    street: str
    number: str
    location: Optional[dict] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class AlertCreate(BaseModel):
    type: str

class AlertResponse(BaseModel):
    id: str
    type: str
    user_name: str
    state: str
    city: str
    neighborhood: str
    street: str
    number: str
    timestamp: str
    is_active: bool

class PaymentResponse(BaseModel):
    success: bool
    message: str
    payment_url: Optional[str] = None
    pix_code: Optional[str] = None
    boleto_url: Optional[str] = None

class SubscriptionStatus(BaseModel):
    has_subscription: bool
    status: str  # trial, active, overdue, blocked, cancelled, expired
    days_remaining: Optional[int] = None
    is_blocked: bool = False
    trial_end_date: Optional[str] = None
    payment_due_date: Optional[str] = None
    grace_period_end: Optional[str] = None
    message: str
    needs_payment: bool = False

class PaymentConfirmation(BaseModel):
    subscription_id: str
    payment_method: str
    transaction_id: Optional[str] = None

class HelpMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    user_email: str
    user_address: str  # Endereço completo formatado
    message: str
    status: str = "pending"  # pending, read, resolved
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    admin_response: Optional[str] = None
    resolved_at: Optional[datetime] = None

class HelpMessageCreate(BaseModel):
    message: str

class HelpMessageResponse(BaseModel):
    id: str
    user_name: str
    user_email: str
    user_address: str
    message: str
    status: str
    created_at: str
    admin_response: Optional[str] = None

class AdminSetRequest(BaseModel):
    email: EmailStr
    is_admin: bool
    is_vip: bool = False
    vip_permanent: bool = True

class AdminStats(BaseModel):
    total_users: int
    total_subscriptions: int
    active_subscriptions: int
    trial_subscriptions: int
    blocked_subscriptions: int
    total_alerts: int
    pending_help_messages: int

class EmergencyNotification(BaseModel):
    alert_id: str
    alert_type: str
    requester_name: str
    requester_address: str
    target_users: List[str]  # List of user IDs to notify
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_silent_for_requester: bool = True  # Requester gets silent notification

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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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

def is_vip_active(user: User) -> bool:
    """Check if user has active VIP status"""
    if not user.is_vip:
        return False
    
    # If vip_expires_at is None, it's permanent VIP
    if user.vip_expires_at is None:
        return True
    
    # Check if VIP hasn't expired
    now = datetime.now(timezone.utc)
    return user.vip_expires_at > now

async def ensure_admin_exists():
    """Ensure julio.csds@hotmail.com is set as permanent admin"""
    admin_email = "julio.csds@hotmail.com"
    
    # Check if admin user exists
    admin_user = await db.users.find_one({"email": admin_email})
    
    if admin_user:
        # Update existing user to be admin/VIP if not already
        if not admin_user.get("is_admin") or not admin_user.get("is_vip"):
            await db.users.update_one(
                {"email": admin_email},
                {"$set": {
                    "is_admin": True,
                    "is_vip": True,
                    "vip_expires_at": None  # Permanent VIP
                }}
            )
            print(f"✅ Updated {admin_email} to permanent admin/VIP status")
    else:
        print(f"ℹ️  Admin user {admin_email} does not exist yet. Will be set when they register.")

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user and verify admin privileges"""
    user = await get_current_user(credentials)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

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
        datetime_fields = [
            'created_at', 'timestamp', 'start_date', 'next_payment', 
            'trial_end_date', 'payment_due_date', 'grace_period_end', 
            'last_payment_date', 'blocked_at', 'vip_expires_at', 
            'resolved_at', 'cancelled_at'
        ]
        for key, value in item.items():
            if key in datetime_fields and isinstance(value, str):
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
    
    # Check if this is the admin email
    is_admin_email = user_data.email.lower() == "julio.csds@hotmail.com"
    
    # Create user
    user = User(
        name=user_data.name,
        email=user_data.email,
        state=user_data.state,
        city=user_data.city,
        neighborhood=user_data.neighborhood,
        street=user_data.street,
        number=user_data.number,
        resident_names=user_data.resident_names,
        is_admin=is_admin_email,
        is_vip=is_admin_email,
        vip_expires_at=None if is_admin_email else None  # Permanent VIP for admin
    )
    
    # Store user with hashed password
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    user_dict = prepare_for_mongo(user_dict)
    
    await db.users.insert_one(user_dict)
    
    if is_admin_email:
        print(f"✅ Admin user registered: {user_data.email}")
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    response_user = UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        state=user.state,
        city=user.city,
        neighborhood=user.neighborhood,
        street=user.street,
        number=user.number,
        resident_names=user.resident_names,
        is_admin=user.is_admin,
        is_vip=user.is_vip,
        vip_expires_at=user.vip_expires_at.isoformat() if user.vip_expires_at else None
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
    
    # Check if this is admin email and ensure admin status
    if login_data.email.lower() == "julio.csds@hotmail.com":
        if not user_doc.get("is_admin") or not user_doc.get("is_vip"):
            await db.users.update_one(
                {"email": login_data.email},
                {"$set": {
                    "is_admin": True,
                    "is_vip": True,
                    "vip_expires_at": None
                }}
            )
            user_doc["is_admin"] = True
            user_doc["is_vip"] = True
            user_doc["vip_expires_at"] = None
    
    # Create access token
    access_token = create_access_token(data={"sub": user_doc["id"]})
    
    user_doc = parse_from_mongo(user_doc)
    response_user = UserResponse(
        id=user_doc["id"],
        name=user_doc["name"],
        email=user_doc["email"],
        state=user_doc.get("state", "SP"),  # Default for existing users
        city=user_doc.get("city", "São Paulo"),  # Default for existing users
        neighborhood=user_doc["neighborhood"],
        street=user_doc["street"],
        number=user_doc["number"],
        resident_names=user_doc["resident_names"],
        is_admin=user_doc.get("is_admin", False),
        is_vip=user_doc.get("is_vip", False),
        vip_expires_at=user_doc.get("vip_expires_at").isoformat() if user_doc.get("vip_expires_at") else None
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
        "status": {"$nin": ["cancelled", "expired"]}
    })
    
    if existing_sub:
        raise HTTPException(status_code=400, detail="Usuário já possui assinatura ativa")
    
    # Calculate dates for new billing logic
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=30)
    payment_due = trial_end + timedelta(days=5)  # 5 days grace period
    
    # Create subscription with trial status
    subscription = Subscription(
        user_id=current_user.id,
        payment_method=subscription_data.payment_method,
        status="trial",
        trial_end_date=trial_end,
        next_payment=trial_end,
        payment_due_date=payment_due,
        grace_period_end=payment_due,
        is_trial=True
    )
    
    subscription_dict = subscription.dict()
    subscription_dict = prepare_for_mongo(subscription_dict)
    
    await db.subscriptions.insert_one(subscription_dict)
    
    # Generate payment response based on method
    payment_response = PaymentResponse(success=True, message="Assinatura criada com sucesso! Período gratuito de 30 dias iniciado.")
    
    if subscription_data.payment_method == "pix":
        payment_response.pix_code = "09b74dd4-64da-4563-b769-95cec83659f0"
        payment_response.message = "Assinatura criada! Você terá 30 dias gratuitos. Use este código PIX quando necessário."
    elif subscription_data.payment_method == "boleto":
        payment_response.boleto_url = "https://exemplo.com/boleto/123456"
        payment_response.message = "Assinatura criada! Você terá 30 dias gratuitos. Boleto disponível quando necessário."
    elif subscription_data.payment_method == "credit-card":
        # In production, this would integrate with Mercado Pago
        payment_response.payment_url = "link.mercadopago.com.br/hopez"
        payment_response.message = "Assinatura criada! Você terá 30 dias gratuitos. Cartão será cobrado após o período."
    
    return payment_response

@api_router.get("/subscription-status", response_model=SubscriptionStatus)
async def get_subscription_status(current_user: User = Depends(get_current_user)):
    """Check user's subscription status and determine if app should be blocked"""
    
    # VIP users bypass all subscription checks
    if is_vip_active(current_user):
        return SubscriptionStatus(
            has_subscription=True,
            status="vip",
            is_blocked=False,
            message="Status VIP - Acesso liberado permanentemente!" if current_user.is_admin else "Status VIP ativo",
            needs_payment=False
        )
    
    # Find user's subscription
    subscription_doc = await db.subscriptions.find_one({
        "user_id": current_user.id,
        "status": {"$nin": ["cancelled", "expired"]}
    })
    
    if not subscription_doc:
        return SubscriptionStatus(
            has_subscription=False,
            status="none",
            is_blocked=True,
            message="Nenhuma assinatura encontrada. Faça sua assinatura para usar o aplicativo.",
            needs_payment=True
        )
    
    subscription_doc = parse_from_mongo(subscription_doc)
    now = datetime.now(timezone.utc)
    
    # During trial period
    if subscription_doc["status"] == "trial":
        trial_end = subscription_doc["trial_end_date"]
        if now < trial_end:
            days_remaining = (trial_end - now).days
            return SubscriptionStatus(
                has_subscription=True,
                status="trial",
                days_remaining=days_remaining,
                is_blocked=False,
                trial_end_date=trial_end.strftime("%d/%m/%Y"),
                message=f"Período gratuito! Restam {days_remaining} dias até vencimento.",
                needs_payment=False
            )
        else:
            # Trial expired, check grace period
            grace_end = subscription_doc["grace_period_end"]
            if now < grace_end:
                days_remaining = (grace_end - now).days
                # Update status to overdue
                await db.subscriptions.update_one(
                    {"id": subscription_doc["id"]},
                    {"$set": {"status": "overdue"}}
                )
                return SubscriptionStatus(
                    has_subscription=True,
                    status="overdue",
                    days_remaining=days_remaining,
                    is_blocked=False,
                    payment_due_date=subscription_doc["payment_due_date"].strftime("%d/%m/%Y"),
                    grace_period_end=grace_end.strftime("%d/%m/%Y"),
                    message=f"Período de pagamento! Restam {days_remaining} dias para pagar R$30,00.",
                    needs_payment=True
                )
            else:
                # Grace period expired, block user
                if subscription_doc["status"] != "blocked":
                    await db.subscriptions.update_one(
                        {"id": subscription_doc["id"]},
                        {"$set": {"status": "blocked", "blocked_at": now.isoformat()}}
                    )
                return SubscriptionStatus(
                    has_subscription=True,
                    status="blocked",
                    is_blocked=True,
                    message="Assinatura bloqueada! Pague R$30,00 para reativar o aplicativo.",
                    needs_payment=True
                )
    
    # Active subscription
    elif subscription_doc["status"] == "active":
        next_payment = subscription_doc["next_payment"]
        if now < next_payment:
            days_remaining = (next_payment - now).days
            return SubscriptionStatus(
                has_subscription=True,
                status="active",
                days_remaining=days_remaining,
                is_blocked=False,
                message=f"Assinatura ativa! Próximo pagamento em {days_remaining} dias.",
                needs_payment=False
            )
        else:
            # Payment overdue, enter grace period
            grace_end = next_payment + timedelta(days=5)
            if now < grace_end:
                days_remaining = (grace_end - now).days
                await db.subscriptions.update_one(
                    {"id": subscription_doc["id"]},
                    {"$set": {"status": "overdue", "payment_due_date": grace_end.isoformat()}}
                )
                return SubscriptionStatus(
                    has_subscription=True,
                    status="overdue",
                    days_remaining=days_remaining,
                    is_blocked=False,
                    payment_due_date=grace_end.strftime("%d/%m/%Y"),
                    message=f"Pagamento em atraso! Restam {days_remaining} dias para pagar R$30,00.",
                    needs_payment=True
                )
            else:
                # Block user
                await db.subscriptions.update_one(
                    {"id": subscription_doc["id"]},
                    {"$set": {"status": "blocked", "blocked_at": now.isoformat()}}
                )
                return SubscriptionStatus(
                    has_subscription=True,
                    status="blocked",
                    is_blocked=True,
                    message="Assinatura bloqueada! Pague R$30,00 para reativar o aplicativo.",
                    needs_payment=True
                )
    
    # Already blocked
    elif subscription_doc["status"] == "blocked":
        return SubscriptionStatus(
            has_subscription=True,
            status="blocked",
            is_blocked=True,
            message="Assinatura bloqueada! Pague R$30,00 para reativar o aplicativo.",
            needs_payment=True
        )
    
    # Default fallback
    return SubscriptionStatus(
        has_subscription=False,
        status="unknown",
        is_blocked=True,
        message="Status desconhecido. Entre em contato com o suporte.",
        needs_payment=True
    )

@api_router.post("/confirm-payment")
async def confirm_payment(
    payment_data: PaymentConfirmation,
    current_user: User = Depends(get_current_user)
):
    """Confirm payment and reactivate subscription"""
    
    # Find subscription
    subscription_doc = await db.subscriptions.find_one({
        "id": payment_data.subscription_id,
        "user_id": current_user.id
    })
    
    if not subscription_doc:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    
    now = datetime.now(timezone.utc)
    next_payment = now + timedelta(days=30)  # Next billing cycle
    
    # Update subscription to active
    await db.subscriptions.update_one(
        {"id": payment_data.subscription_id},
        {"$set": {
            "status": "active",
            "last_payment_date": now.isoformat(),
            "next_payment": next_payment.isoformat(),
            "is_trial": False,
            "blocked_at": None
        }}
    )
    
    return {"success": True, "message": "Pagamento confirmado! Assinatura reativada com sucesso."}

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
        state=current_user.state,
        city=current_user.city,
        neighborhood=current_user.neighborhood,
        street=current_user.street,
        number=current_user.number,
        location={
            "lat": -23.55 + (0.01 * hash(current_user.id) % 100 - 50) / 5000,
            "lng": -46.63 + (0.01 * hash(current_user.id) % 100 - 50) / 5000
        }
    )
    
    alert_dict = alert.dict()
    alert_dict = prepare_for_mongo(alert_dict)
    
    await db.alerts.insert_one(alert_dict)
    
    # Find all users on the same street for emergency notifications
    same_street_users = []
    users_cursor = db.users.find({
        "state": current_user.state,
        "city": current_user.city,
        "neighborhood": current_user.neighborhood,
        "street": current_user.street,
        "id": {"$ne": current_user.id}  # Exclude the requester
    })
    
    async for user in users_cursor:
        same_street_users.append(user["id"])
    
    # Create emergency notification record
    notification = EmergencyNotification(
        alert_id=alert.id,
        alert_type=alert_data.type,
        requester_name=current_user.name,
        requester_address=f"{current_user.street}, {current_user.number}, {current_user.neighborhood}, {current_user.city} - {current_user.state}",
        target_users=same_street_users,
        is_silent_for_requester=True
    )
    
    notification_dict = notification.dict()
    notification_dict = prepare_for_mongo(notification_dict)
    await db.emergency_notifications.insert_one(notification_dict)
    
    return {
        "message": f"Alerta de {alert_data.type} enviado com sucesso!",
        "alert_id": alert.id,
        "notification_sent_to": len(same_street_users),
        "silent_for_requester": True,
        "target_address": f"Rua {current_user.street}, {current_user.neighborhood}"
    }

@api_router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(current_user: User = Depends(get_current_user)):
    # Get alerts from same street (more precise than neighborhood)
    alerts_cursor = db.alerts.find({
        "state": current_user.state,
        "city": current_user.city,
        "neighborhood": current_user.neighborhood,
        "street": current_user.street,
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
            state=alert.get("state", "SP"),
            city=alert.get("city", "São Paulo"),
            neighborhood=alert["neighborhood"],
            street=alert["street"],
            number=alert["number"],
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
        resident_names=current_user.resident_names,
        is_admin=current_user.is_admin,
        is_vip=current_user.is_vip,
        vip_expires_at=current_user.vip_expires_at.isoformat() if current_user.vip_expires_at else None
    )

# Help/Support routes
@api_router.post("/help")
async def send_help_message(
    help_data: HelpMessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Send help message to SafeZone support"""
    help_message = HelpMessage(
        user_id=current_user.id,
        user_name=current_user.name,
        user_email=current_user.email,
        message=help_data.message
    )
    
    help_dict = help_message.dict()
    help_dict = prepare_for_mongo(help_dict)
    
    await db.help_messages.insert_one(help_dict)
    
    return {"success": True, "message": "Sua mensagem foi enviada com sucesso! Nossa equipe responderá em breve."}

@api_router.post("/cancel-subscription")
async def cancel_subscription(current_user: User = Depends(get_current_user)):
    """Cancel user's subscription"""
    
    # VIP users cannot cancel (they don't have paid subscriptions)
    if is_vip_active(current_user):
        raise HTTPException(status_code=400, detail="Usuários VIP não possuem assinatura para cancelar")
    
    # Find user's subscription
    subscription_doc = await db.subscriptions.find_one({
        "user_id": current_user.id,
        "status": {"$nin": ["cancelled", "expired"]}
    })
    
    if not subscription_doc:
        raise HTTPException(status_code=404, detail="Nenhuma assinatura ativa encontrada")
    
    # Cancel subscription
    now = datetime.now(timezone.utc)
    await db.subscriptions.update_one(
        {"id": subscription_doc["id"]},
        {"$set": {
            "status": "cancelled",
            "cancelled_at": now.isoformat()
        }}
    )
    
    return {"success": True, "message": "Assinatura cancelada com sucesso"}

# Admin routes
@api_router.get("/admin/stats", response_model=AdminStats)
async def get_admin_stats(current_admin: User = Depends(get_current_admin)):
    """Get admin statistics dashboard"""
    
    # Count users
    total_users = await db.users.count_documents({})
    
    # Count subscriptions by status
    total_subs = await db.subscriptions.count_documents({})
    active_subs = await db.subscriptions.count_documents({"status": "active"})
    trial_subs = await db.subscriptions.count_documents({"status": "trial"})
    blocked_subs = await db.subscriptions.count_documents({"status": "blocked"})
    
    # Count alerts
    total_alerts = await db.alerts.count_documents({})
    
    # Count pending help messages
    pending_help = await db.help_messages.count_documents({"status": "pending"})
    
    return AdminStats(
        total_users=total_users,
        total_subscriptions=total_subs,
        active_subscriptions=active_subs,
        trial_subscriptions=trial_subs,
        blocked_subscriptions=blocked_subs,
        total_alerts=total_alerts,
        pending_help_messages=pending_help
    )

@api_router.get("/admin/users")
async def get_all_users(current_admin: User = Depends(get_current_admin)):
    """Get all users for admin management"""
    
    users_cursor = db.users.find({}).sort("created_at", -1)
    users = await users_cursor.to_list(length=None)
    
    response_users = []
    for user in users:
        user = parse_from_mongo(user)
        response_users.append({
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "neighborhood": user["neighborhood"],
            "is_admin": user.get("is_admin", False),
            "is_vip": user.get("is_vip", False),
            "created_at": user["created_at"].strftime("%d/%m/%Y %H:%M")
        })
    
    return response_users

@api_router.get("/admin/help-messages")
async def get_help_messages(current_admin: User = Depends(get_current_admin)):
    """Get all help messages for admin review"""
    
    messages_cursor = db.help_messages.find({}).sort("created_at", -1)
    messages = await messages_cursor.to_list(length=None)
    
    response_messages = []
    for msg in messages:
        msg = parse_from_mongo(msg)
        response_messages.append(HelpMessageResponse(
            id=msg["id"],
            user_name=msg["user_name"],
            user_email=msg["user_email"],
            message=msg["message"],
            status=msg["status"],
            created_at=msg["created_at"].strftime("%d/%m/%Y %H:%M"),
            admin_response=msg.get("admin_response")
        ))
    
    return response_messages

@api_router.post("/admin/set-admin")
async def set_user_admin(
    admin_data: AdminSetRequest,
    current_admin: User = Depends(get_current_admin)
):
    """Set user as admin/VIP (admin only)"""
    
    # Find user by email
    user_doc = await db.users.find_one({"email": admin_data.email})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Prepare update data
    update_data = {
        "is_admin": admin_data.is_admin,
        "is_vip": admin_data.is_vip
    }
    
    # Set VIP expiration
    if admin_data.is_vip:
        if admin_data.vip_permanent:
            update_data["vip_expires_at"] = None  # Permanent VIP
        else:
            # Could add date picker in future for temporary VIP
            update_data["vip_expires_at"] = None
    else:
        update_data["vip_expires_at"] = None
    
    await db.users.update_one(
        {"email": admin_data.email},
        {"$set": update_data}
    )
    
    action = "promovido a" if admin_data.is_admin else "removido de"
    vip_text = " e VIP" if admin_data.is_vip else ""
    
    return {"success": True, "message": f"Usuário {admin_data.email} {action} admin{vip_text} com sucesso"}

@api_router.put("/admin/help-messages/{message_id}/respond")
async def respond_help_message(
    message_id: str,
    response_data: dict,
    current_admin: User = Depends(get_current_admin)
):
    """Respond to help message (admin only)"""
    
    admin_response = response_data.get("response", "")
    if not admin_response:
        raise HTTPException(status_code=400, detail="Resposta é obrigatória")
    
    now = datetime.now(timezone.utc)
    result = await db.help_messages.update_one(
        {"id": message_id},
        {"$set": {
            "admin_response": admin_response,
            "status": "resolved",
            "resolved_at": now.isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    
    return {"success": True, "message": "Resposta enviada com sucesso"}

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

@app.on_event("startup")
async def startup_event():
    """Initialize admin user on startup"""
    await ensure_admin_exists()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()