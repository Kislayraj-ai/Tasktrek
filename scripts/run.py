import os
import sys
import django
from pathlib import Path

# --- 1. MANUALLY SET DJANGO SETTINGS MODULE ---
settings_path = "Taskmanagement.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_path)

# --- 2. Add project to Python path ---
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# --- 3. Initialize Django ---
try:
    django.setup()
except Exception as e:
    print(f"❌ Failed to setup Django: {e}")
    sys.exit(1)

# --- 4. Now import models ---
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from dashboard.models import UserRole, Role

def main():
    users_data = [
        {
            "username": "admin",
            "password": "test123",
            "email": "admin@example.com",
            "is_superuser": True,
            "is_staff": True,
            "role_id": 1
        }
    ]

    for data in users_data:
        try:
            # Create user
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "password": make_password(data["password"]),
                    "is_superuser": data["is_superuser"],
                    "is_staff": data["is_staff"],
                    "is_active": True
                }
            )
            
            # Assign role
            role = Role.objects.get(id=data["role_id"])
            UserRole.objects.update_or_create(user=user, defaults={"role": role})
            
            print(f"✅ {'Created' if created else 'Updated'} {user.username} (Role: {role.name})")
        except Exception as e:
            print(f"❌ Error processing {data['username']}: {e}")

if __name__ == "__main__":
    main()