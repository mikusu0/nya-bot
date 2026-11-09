import asyncpg, asyncio, os, aiofiles
from typing import Dict, Optional
from core.logger import logger
from config import SERVER_IP, SERVER_PORT, SERVER_DB_USER, SERVER_DB_PASSWORD, SERVER_DB_NAME
from dataclasses import dataclass, asdict

VALID_COLUMNS = {"messages", "exp", "level", "balance"}
lock = asyncio.Lock()
pool: Optional[asyncpg.pool.Pool] = None

@dataclass
class UserData:
    user_id: int
    messages: int = 0
    exp: int = 0
    level: int = 0
    balance: int = 0

    def __iter__(self):
        return iter(asdict(self).items())
    

class Database:
    @classmethod
    async def create_pool(self):
        global pool
        if pool is not None: return

        logger.info("🛢️ Creating database connection pool...")
        try:
            pool = await asyncpg.create_pool(
                host=SERVER_IP,
                port=SERVER_PORT,
                user=SERVER_DB_USER,
                password=SERVER_DB_PASSWORD,
                database=SERVER_DB_NAME,
                min_size=1,
                max_size=10
            )
            async with pool.acquire() as connection:
                connection: asyncpg.Connection
                await connection.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    messages INTEGER DEFAULT 0,
                    exp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 0,
                    balance INTEGER DEFAULT 0
                )
                ''')

            logger.info("🛢️✅ Database connection pool created successfully.")
        except Exception as e:
            logger.error(f"🛢️❌ Failed to create database connection pool: {e}")
            raise e

    @classmethod
    async def close_pool(self):
        global pool
        if pool is not None:
            await pool.close()
            pool = None
            logger.info("🛢️✅ Database connection pool closed.")
    
    @staticmethod
    async def _release(connection: asyncpg.Connection):
        global pool
        if pool is None:
            raise RuntimeError("🛢️❌ Database pool is not initialized.")
        await pool.release(connection)

    @classmethod
    async def ensure_user(self, user_id: int):
        async with pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING",
                user_id
            )

    @classmethod
    async def add_value_user_data(cls, user_id: int, column: str, value):
        if column not in VALID_COLUMNS:
            raise ValueError("Invalid colomn name.")
        
        await cls.ensure_user(user_id)
        async with pool.acquire() as connection:
            await connection.execute(
                f"UPDATE users SET {column} = {column} + $1 WHERE user_id = $2",
                value, user_id
            )

    @classmethod
    async def set_value_user_data(cls, user_id, column, value):
        if column not in VALID_COLUMNS:
            raise ValueError("Invalid colomn name.")
        
        await cls.ensure_user(user_id)
        async with await pool.acquire() as connection:
            await connection.execute(
                f"UPDATE users SET {column} = $1 WHERE user_id = $2",
                value, user_id
            )

    @classmethod
    async def set_multi_value_user_data(cls, user_id, data: Dict[str, any]):
        if not data:
            return

        for column in data.keys():
            if column not in VALID_COLUMNS:
                raise ValueError(f"Invalid column name: {column}")

        await cls.ensure_user(user_id)

        colums = ", ".join([f"{col} = ${idx+1}" for idx, col in enumerate(data.keys())])
        values = list(data.values()) + [user_id]

        async with pool.acquire() as connection:
            await connection.execute(
                f"UPDATE users SET {colums} WHERE user_id = ${len(values)}",
                *values
            )

    @classmethod
    async def get_value_user_data(cls, user_id, column) -> Optional[int | str]:
        if column not in VALID_COLUMNS:
            raise ValueError("Invalid colomn name.")
        
        if pool is None:
            raise RuntimeError("Database not connected.")
        
        await cls.ensure_user(user_id)
        async with pool.acquire() as connection:
            result = await connection.fetchrow(
                f"SELECT {column} FROM users WHERE user_id = $1",
                user_id
            )
            if result is None:
                return None
            return result[column]

    @classmethod
    async def get_user_data(cls, user_id: int, data: Optional[list[str]] = None) -> UserData:
        if pool is None:
            raise RuntimeError("Database not connected.")
        
        if data is None:
            columns = list(VALID_COLUMNS)
        else:
            invalid = [col for col in data if col not in VALID_COLUMNS]
            if invalid:
                raise ValueError(f"Invalid colomn names: {', '.join(invalid)}")
            columns = data
        
        columns_str = ", ".join(columns)

        await cls.ensure_user(user_id)
        async with pool.acquire() as connection:
            result = await connection.fetchrow(
                f"SELECT {columns_str} FROM users WHERE user_id = $1",
                user_id
            )
            if result is None:
                return None
            
            kwargs = {col: result[col] for col in columns}
            kwargs["user_id"] = user_id
            return UserData(**kwargs)

        

    @classmethod
    async def sync_user_level(cls, user_id: int) -> None:
        data = await cls.get_user_data(user_id, data=["exp", "level"])
        if data is None:
            return
        
        exp = data.exp
        level = data.level

        while True:
            level_up_cost = (level + 1) * 25
            if exp < level_up_cost:
                break
            exp -= level_up_cost
            level += 1

        await cls.set_multi_value_user_data(user_id, {"exp": exp, "level": level})

    @classmethod
    async def get_level_up_cost(cls, user_id: int) -> int:
        data = await cls.get_user_data(user_id, data=["level"])
        if data is None:
            return 25
        return (data.level + 1) * 25

# JSON

# def load_json(path):
#     if not os.path.exists(path) or os.path.getsize(path) == 0:
#         with open(path, "w", encoding="utf-8") as f:
#             json.dump({}, f, ensure_ascii=False, indent=4)

#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f) or {}

# def save_json(path, data):
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(data, f, ensure_ascii=False, indent=4)

# async def async_load_json(path):
#     async with lock:
#         return await asyncio.to_thread(load_json, path)

# async def async_save_json(path, data):
#     async with lock:
#         await asyncio.to_thread(save_json, path, data)

# def sync_data(user_id, data):
#     data_template = {}

#     if user_id not in data:
#         data[user_id] = copy.deepcopy(data_template)
#     else:
#         for key, value in data_template.items():
#             if key not in data[user_id]:
#                 data[user_id][key] = value
