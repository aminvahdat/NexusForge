#!/usr/bin/env python3
"""Seed admin user with bcrypt hash."""
import sys, os
sys.path.insert(0, "/app")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/nexusforge")
os.environ.setdefault("JWT_SECRET_KEY", "nexusforge-secret-key-minimum-32-characters-long-ok")

from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash_pw = pwd_context.hash("password123")
print("Bcrypt hash:", hash_pw[:30] + "...")

engine = create_engine("postgresql+psycopg2://postgres:postgres@postgres:5432/nexusforge")
Session = sessionmaker(bind=engine)
session = Session()

# Create users table if missing (simplified — rely on migrations or existing schema)
session.execute(text("CREATE TABLE IF NOT EXISTS users (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), email VARCHAR(255) UNIQUE NOT NULL, username VARCHAR(50), password_hash VARCHAR(255) NOT NULL, is_active BOOLEAN DEFAULT TRUE, is_superuser BOOLEAN DEFAULT FALSE, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), last_login TIMESTAMP WITH TIME ZONE)"))
session.commit()

# Insert admin
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import insert
session.execute(text("""
    INSERT INTO users (email, username, password_hash, is_active, is_superuser)
    VALUES ('admin@nexusforge.io', 'admin', :hash, TRUE, TRUE)
    ON CONFLICT (email) DO NOTHING
"""), {"hash": hash_pw})
session.commit()

# Verify
row = session.execute(text("SELECT email, is_active FROM users WHERE email='admin@nexusforge.io'")).fetchone()
if row:
    print("Admin user verified:", row.email, "is_active=", row.is_active)
else:
    print("WARNING: admin not found after insert")
session.close()
