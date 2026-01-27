import os
from cryptography.fernet import Fernet
from extensions import db
from models import UserRobot
from dotenv import load_dotenv
from main import app  # Import your Flask app

load_dotenv()

def migrate_encrypt_viam_keys():
    with app.app_context():
        f = UserRobot.get_fernet()
        user_robots = UserRobot.query.all()
        updated = 0
        for ur in user_robots:
            # Encrypt viam_api_key if not already encrypted
            if ur._viam_api_key and len(ur._viam_api_key) < 44:
                ur._viam_api_key = f.encrypt(ur._viam_api_key.encode()).decode()
                updated += 1
            # Encrypt viam_api_key_id if not already encrypted
            if ur._viam_api_key_id and len(ur._viam_api_key_id) < 44:
                ur._viam_api_key_id = f.encrypt(ur._viam_api_key_id.encode()).decode()
                updated += 1
        if updated:
            db.session.commit()
            print(f"Encrypted {updated} fields in UserRobot table.")
        else:
            print("No fields needed encryption. All credentials are already encrypted.")

if __name__ == "__main__":
    migrate_encrypt_viam_keys()
