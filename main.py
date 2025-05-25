from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import hashlib
from twilio.rest import Client

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def init_db():
    conn = sqlite3.connect('adi.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
init_db()
class User(BaseModel):
    username: str
    password: str

def get_db_connection():
    conn = sqlite3.connect('adi.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def read_root():
    return FileResponse("app/static/index.html")

@app.post("/register")
async def register(user: User):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user.username, hashed_password))
        conn.commit()
        conn.close()
        return {"message": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database is locked. Try again shortly.")

@app.get("/users")
def get_users():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return [dict(user) for user in users]

@app.post("/login")
async def login(user: User):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (user.username, hashed_password))
        user = cursor.fetchone()
        conn.close()
        if user:
            return {"message": "Login successful", "user": dict(user)}
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")
    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database is locked. Try again shortly.")
account_sid = 'AC49e5db752175e0f01eabc9acfe26de0b'  
auth_token = '426a9ea3edb31c9af9f662d4e48a5cca' 
twilio_number = '+12342175725'  
@app.post("/send-alert")
def send_alert():
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            to="+919942673363",  
            from_=twilio_number,
            body="HEY, THIS IS TO INFORM YOU THAT 'ALERT ALERT ALERT !!!!! AMBULANCE COMING OVER PLEASE CLEAR UP ANY CONGESTION AT NEAREST TRAFFIC LIGHT'"
        )
        return {"message": "Alert sent successfully", "sid": message.sid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))