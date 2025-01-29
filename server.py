from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import hashlib
from typing import Optional
import sqlite3

app = FastAPI()

# CORS settings remain unchanged
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"

DATABASE_FILE = "my_database.db"

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

class ScoreCreate(BaseModel):
    score: int

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

def create_tables():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        # Создаем таблицу пользователей
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Создаем таблицу счета
        c.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        print("Tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        conn.close()

def load_database():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    users = []
    for row in rows:
        # Преобразуем дату только если она строка
        created_at = row[3]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        users.append({
            "id": row[0],
            "username": row[1],
            "password": row[2],
            "created_at": created_at,
        })
    conn.close()
    return users

def save_user(user):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO users (username, password, created_at)
            VALUES (?, ?, ?)
        ''', (user["username"], user["password"], user["created_at"]))
        conn.commit()
        print(f"User saved successfully: {user['username']}")
    except Exception as e:
        print(f"Error saving user: {e}")
        raise e
    finally:
        conn.close()

@app.post("/register", response_model=UserOut)
async def register(user: UserCreate):
    try:
        create_tables()  # Create tables if they don't exist
        users = load_database()

        if not user.username or not user.password:
            raise HTTPException(status_code=400, detail="Username and password are required")

        if len(user.username) < 3:
            raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")

        if len(user.password) < 4:
            raise HTTPException(status_code=400, detail="Password must be at least 4 characters long")

        if any(u["username"] == user.username for u in users):
            raise HTTPException(status_code=400, detail="Username already exists")

        new_user = {
            "id": None,
            "username": user.username,
            "password": hash_password(user.password),
            "created_at": datetime.utcnow().isoformat(),
        }

        save_user(new_user)

        # Get the newly created user's id
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("SELECT last_insert_rowid()")
        new_user["id"] = c.fetchone()[0]
        conn.close()

        return UserOut(
            id=new_user["id"],
            username=new_user["username"],
            created_at=datetime.fromisoformat(new_user["created_at"]),
        )
    except Exception as e:
        print(f"Registration error: {str(e)}")  # Для отладки
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login(user: UserCreate):
    users = load_database()

    # Find the user in the database
    db_user = next((u for u in users if u["username"] == user.username), None)
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_token(db_user["id"])
    return {"token": token, "success": True}

@app.get("/me", response_model=UserOut)
async def me(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    try:
        token = authorization.split(" ")[1]
        user_id = verify_token(token)
        
        users = load_database()
        user = next((u for u in users if u["id"] == user_id), None)
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # Убедимся, что created_at это строка перед преобразованием
        created_at = user["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif not isinstance(created_at, datetime):
            created_at = datetime.utcnow()

        return UserOut(
            id=user["id"],
            username=user["username"],
            created_at=created_at,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Error in /me endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scores")
async def save_score(score_data: ScoreCreate, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Проверяем формат токена
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization format")
        
        token = authorization.split(" ")[1]
        user_id = verify_token(token)
        
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        # Проверяем лучший результат пользователя
        c.execute('''
            SELECT score FROM scores 
            WHERE user_id = ? 
            ORDER BY score DESC 
            LIMIT 1
        ''', (user_id,))
        best_score = c.fetchone()
        
        # Если это первый результат или новый рекорд
        if not best_score or score_data.score > best_score[0]:
            # Сначала удаляем все предыдущие результаты пользователя
            c.execute('''
                DELETE FROM scores 
                WHERE user_id = ?
            ''', (user_id,))
            
            # Затем добавляем новый рекорд
            c.execute('''
                INSERT INTO scores (user_id, score, created_at)
                VALUES (?, ?, ?)
            ''', (user_id, score_data.score, datetime.utcnow().isoformat()))
            
            conn.commit()
            print(f"New record saved: user_id={user_id}, score={score_data.score}")
        
        return {"success": True}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Error saving score: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

@app.get("/leaderboard")
async def get_leaderboard():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    
    try:
        # Получаем лучшие результаты каждого игрока
        c.execute('''
            WITH RankedScores AS (
                SELECT 
                    u.username,
                    s.score,
                    ROW_NUMBER() OVER (PARTITION BY u.id ORDER BY s.score DESC) as rn
                FROM scores s
                JOIN users u ON s.user_id = u.id
            )
            SELECT username, score
            FROM RankedScores
            WHERE rn = 1
            ORDER BY score DESC
            LIMIT 3
        ''')
        rows = c.fetchall()
        
        # Форматируем результаты
        results = []
        for i, (username, score) in enumerate(rows, 1):
            results.append({
                "position": i,
                "username": username,
                "score": score
            })
        
        return results
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    
    # Создаем таблицы при запуске
    create_tables()
    
    # Проверяем существование таблиц
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    print("Existing tables:", tables)
    conn.close()
    
    uvicorn.run(app, host="127.0.0.1", port=8001)
