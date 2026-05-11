"""
Seed script to populate the database with test data.
Run this after starting the server to create sample users and data.
"""
import requests
import json

BASE_URL = "http://localhost:8001"

# Test users
USERS = [
    {"email": "admin@school.be", "password": "admin123", "first_name": "Admin", "last_name": "User", "role": "admin"},
    {"email": "student1@school.be", "password": "student123", "first_name": "Jan", "last_name": "Peeters", "role": "student"},
    {"email": "student2@school.be", "password": "student123", "first_name": "Marie", "last_name": "Verhoeven", "role": "student"},
    {"email": "commissie1@school.be", "password": "commissie123", "first_name": "Peter", "last_name": "Smit", "role": "committee"},
    {"email": "docent1@school.be", "password": "docent123", "first_name": "Ann", "last_name": "Claessens", "role": "teacher"},
    {"email": "mentor1@school.be", "password": "mentor123", "first_name": "Bram", "last_name": "Janssens", "role": "mentor"},
]

COMPETENCY_PROFILE = {
    "name": "Toegepaste Informatica 2024-2025",
    "version": "1.0",
    "academic_year": "2024-2025"
}

COMPETENCIES = [
    {"name": "Analyseren", "description": "Probleemanalyse en requirements bepalen", "weight": 30},
    {"name": "Ontwerpen", "description": "Technisch ontwerp en architectuur", "weight": 25},
    {"name": "Realiseren", "description": "Implementatie en coding", "weight": 25},
    {"name": "Testen", "description": "Kwaliteitsborging en testing", "weight": 20},
]


def get_token(email, password):
    """Login and get access token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def seed():
    print("🌱 Seeding database...")
    
    # Step 1: Create admin user first (we need to login as admin to create other users)
    # Since there's no user yet, we'll need to create the first one manually in DB
    # For this seed, let's assume admin exists or you create it manually
    
    print("\n1. Creating test users...")
    # For seeding, we need to be logged in as admin
    # Let's try logging in as the first user (should be admin)
    
    # Try to login with admin credentials
    admin_token = get_token("admin@school.be", "admin123")
    
    if not admin_token:
        print("❌ Could not login as admin. Make sure the database is initialized.")
        print("   You may need to manually create an admin user first.")
        return
    
    print("   ✅ Logged in as admin")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create users
    created_users = []
    for user in USERS[1:]:  # Skip admin, already exists
        try:
            response = requests.post(
                f"{BASE_URL}/auth/register",
                headers=headers,
                json=user
            )
            if response.status_code == 200:
                print(f"   ✅ Created user: {user['email']}")
                created_users.append(response.json())
            elif response.status_code == 400 and "already registered" in response.text:
                print(f"   ℹ️  User already exists: {user['email']}")
            else:
                print(f"   ❌ Failed to create {user['email']}: {response.text}")
        except Exception as e:
            print(f"   ❌ Error creating {user['email']}: {e}")
    
    # Create competency profile first
    print("\n2. Creating competency profile...")
    profile_id = None
    try:
        response = requests.post(
            f"{BASE_URL}/competencies/profiles",
            headers=headers,
            json=COMPETENCY_PROFILE
        )
        if response.status_code == 200:
            profile_data = response.json()
            profile_id = profile_data["id"]
            print(f"   ✅ Created profile: {COMPETENCY_PROFILE['name']} (ID: {profile_id})")
        elif response.status_code == 400:
            # Profile might already exist, try to get active one
            list_response = requests.get(f"{BASE_URL}/competencies/profiles?active_only=true", headers=headers)
            if list_response.status_code == 200:
                profiles = list_response.json()
                if profiles:
                    profile_id = profiles[0]["id"]
                    print(f"   ℹ️  Using existing profile (ID: {profile_id})")
        else:
            print(f"   ❌ Failed to create profile: {response.text}")
    except Exception as e:
        print(f"   ❌ Error creating profile: {e}")

    # Create competencies with profile_id
    if profile_id:
        print("\n3. Creating competencies...")
        for comp in COMPETENCIES:
            try:
                comp_data = {**comp, "profile_id": profile_id}
                response = requests.post(
                    f"{BASE_URL}/competencies",
                    headers=headers,
                    json=comp_data
                )
                if response.status_code == 200:
                    print(f"   ✅ Created competency: {comp['name']}")
                elif response.status_code == 400 and "already exists" in response.text:
                    print(f"   ℹ️  Competency already exists: {comp['name']}")
                else:
                    print(f"   ❌ Failed to create {comp['name']}: {response.text}")
            except Exception as e:
                print(f"   ❌ Error creating {comp['name']}: {e}")
    else:
        print("   ⚠️ Skipping competency creation - no profile available")
    
    print("\n✅ Seeding complete!")
    print("\nTest credentials:")
    for user in USERS:
        print(f"  {user['role']:12} | {user['email']:25} | {user['password']}")


if __name__ == "__main__":
    seed()