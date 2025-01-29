from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import jwt
import hashlib
from typing import Optional
import sqlite3

app = FastAPI()

# Настройка CORS
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

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class UserStats(BaseModel):
    total_games: int
    best_score: int
    average_score: float
    last_game_date: Optional[datetime]

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
        
        # Создание таблицы пользователей
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Создание таблицы счета
        c.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Добавляем индексы для оптимизации запросов
        c.execute('CREATE INDEX IF NOT EXISTS idx_scores_user_id ON scores(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_scores_score ON scores(score)')
        
        conn.commit()
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
    except Exception as e:
        print(f"Error saving user: {e}")
        raise e
    finally:
        conn.close()

@app.post("/register", response_model=UserOut)
async def register(user: UserCreate):
    try:
        create_tables()
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

        # Получение ID нового пользователя
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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login(user: UserCreate):
    users = load_database()
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scores")
async def save_score(score_data: ScoreCreate, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization format")
        
        token = authorization.split(" ")[1]
        user_id = verify_token(token)
        
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        # Сохраняем каждый результат игры
        current_time = datetime.now(timezone.utc).isoformat()
        c.execute('''
            INSERT INTO scores (user_id, score, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, score_data.score, current_time))
            
        conn.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

@app.get("/leaderboard")
async def get_leaderboard():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    
    try:
        # Получение лучших результатов каждого игрока
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

@app.patch("/change-password")
async def change_password(password_data: PasswordChange, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    try:
        token = authorization.split(" ")[1]
        user_id = verify_token(token)
        
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        c.execute("SELECT password FROM users WHERE id = ?", (user_id,))
        result = c.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        current_hashed = result[0]
        
        if not verify_password(password_data.current_password, current_hashed):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        new_hashed = hash_password(password_data.new_password)
        c.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (new_hashed, user_id)
        )
        conn.commit()
        
        return {"message": "Password successfully changed"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

@app.get("/user-stats", response_model=dict)
async def get_user_stats():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        # Получаем полную статистику по каждому игроку
        c.execute("""
            WITH PlayerStats AS (
                SELECT 
                    u.username,
                    COUNT(*) as games_played,
                    MAX(s.score) as best_score,
                    AVG(s.score) as avg_score
                FROM users u
                JOIN scores s ON u.id = s.user_id
                GROUP BY u.id, u.username
            ),
            LastScores AS (
                SELECT 
                    u.username,
                    s.score,
                    s.created_at,
                    ROW_NUMBER() OVER (PARTITION BY u.id ORDER BY s.created_at DESC) as rn
                FROM users u
                JOIN scores s ON u.id = s.user_id
            )
            SELECT 
                p.username,
                p.games_played,
                p.best_score,
                ROUND(p.avg_score, 1) as avg_score,
                GROUP_CONCAT(
                    CASE WHEN l.rn <= 5 THEN l.score END
                ) as last_five_scores
            FROM PlayerStats p
            LEFT JOIN LastScores l ON p.username = l.username
            GROUP BY 
                p.username, 
                p.games_played, 
                p.best_score, 
                p.avg_score
            ORDER BY p.best_score DESC
        """)
        
        rows = c.fetchall()
        
        if not rows:
            return {
                "players": [],
                "message": "Нет данных о играх"
            }
        
        players_stats = []
        for username, games_played, best_score, avg_score, last_scores in rows:
            # Преобразуем строку последних результатов в список
            last_scores_list = []
            if last_scores:
                last_scores_list = [int(s) for s in last_scores.split(',') if s][:5]
            
            players_stats.append({
                "username": username,
                "games_played": games_played,
                "best_score": best_score,
                "average_score": float(avg_score),
                "last_scores": last_scores_list
            })
        
        return {
            "players": players_stats
        }
        
    except Exception as e:
        print(f"Error in get_user_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

@app.delete("/delete-account")
async def delete_account(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    try:
        token = authorization.split(" ")[1]
        user_id = verify_token(token)
        
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        # Удаляем все результаты пользователя
        c.execute("DELETE FROM scores WHERE user_id = ?", (user_id,))
        
        # Удаляем самого пользователя
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        return {"message": "Account successfully deleted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import uvicorn
    create_tables()
    uvicorn.run(app, host="127.0.0.1", port=8001)
