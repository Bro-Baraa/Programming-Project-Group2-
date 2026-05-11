#!/usr/bin/env python3
"""
Initialize the database and create the first admin user.
Run this after setting up the backend to create test accounts.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Base, User
from app.auth import get_password_hash

# Create tables
print("📦 Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created!")

# Create admin user
db = SessionLocal()

print("\n👤 Creating admin user...")

existing_admin = db.query(User).filter(User.email == "admin@school.be").first()
if existing_admin:
    print("ℹ️  Admin user already exists (admin@school.be)")
else:
    admin = User(
        email="admin@school.be",
        password_hash=get_password_hash("admin123"),
        first_name="Admin",
        last_name="User",
        role="admin",
        is_active=True
    )
    db.add(admin)
    db.commit()
    print("✅ Admin user created: admin@school.be / admin123")

# Create some test users
test_users = [
    {"email": "student1@school.be", "password": "student123", "first_name": "Jan", "last_name": "Peeters", "role": "student"},
    {"email": "student2@school.be", "password": "student123", "first_name": "Marie", "last_name": "Verhoeven", "role": "student"},
    {"email": "commissie1@school.be", "password": "commissie123", "first_name": "Peter", "last_name": "Smit", "role": "committee"},
    {"email": "docent1@school.be", "password": "docent123", "first_name": "Ann", "last_name": "Claessens", "role": "teacher"},
    {"email": "mentor1@school.be", "password": "mentor123", "first_name": "Bram", "last_name": "Janssens", "role": "mentor"},
]

print("\n👥 Creating test users...")
for user_data in test_users:
    existing = db.query(User).filter(User.email == user_data["email"]).first()
    if existing:
        print(f"ℹ️  User exists: {user_data['email']}")
        continue
    
    user = User(
        email=user_data["email"],
        password_hash=get_password_hash(user_data["password"]),
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        role=user_data["role"],
        is_active=True
    )
    db.add(user)
    print(f"✅ Created: {user_data['email']} ({user_data['role']})")

db.commit()
db.close()

print("\n" + "="*50)
print("🎉 Setup complete!")
print("="*50)
print("\nTest credentials:")
print("  admin@school.be      / admin123      (admin)")
print("  student1@school.be   / student123    (student)")
print("  student2@school.be   / student123    (student)")
print("  commissie1@school.be / commissie123  (committee)")
print("  docent1@school.be    / docent123     (teacher)")
print("  mentor1@school.be    / mentor123     (mentor)")
print("\nNext steps:")
print("  1. Start the backend: uvicorn app.main:app --reload")
print("  2. Open frontend: http://localhost:8080/index-api.html")
print("  3. Login with any of the accounts above")
print("")