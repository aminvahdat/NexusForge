#!/usr/bin/env python3
"""Insert admin user directly via asyncpg with bcrypt password hash."""
import asyncio
import bcrypt
import asyncpg

DB_URL = "postgresql://postgres:postgres@postgres:5432/nexusforge"

async def seed():
    conn = await asyncpg.connect(DB_URL)
    hash_pw = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
    await conn.execute("""
        INSERT INTO users (email, username, password_hash, is_active, is_superuser, email_verified)
        VALUES ($1, $2, $3, TRUE, TRUE, TRUE)
        ON CONFLICT (email) DO NOTHING
    """, "admin@nexusforge.io", "admin", hash_pw)
    row = await conn.fetchrow("SELECT email, is_active, is_superuser FROM users WHERE email = $1", "admin@nexusforge.io")
    if row:
        print(f"Admin user verified: {row['email']} active={row['is_active']} superuser={row['is_superuser']}")
    else:
        print("WARNING: admin not inserted")
    await conn.close()

asyncio.run(seed())
