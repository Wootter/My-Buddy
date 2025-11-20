"""
Migration script to convert ViaDevice to Robot + UserRobot model.
Run this once on your server to migrate existing data.

Usage: python migrate_to_robot_model.py
"""

from main import app, db
from models import Account, Robot, UserRobot
from datetime import datetime

def migrate():
    with app.app_context():
        print("Starting migration from ViaDevice to Robot + UserRobot...")
        
        # Check if via_device table still exists in database
        try:
            result = db.session.execute(db.text("SELECT COUNT(*) FROM via_device"))
            count = result.scalar()
            
            if count == 0:
                print("No ViaDevice records found. Database might already be migrated.")
                return
            
            print(f"Found {count} ViaDevice records to migrate...")
            
            # Get all records from via_device table (raw SQL since model is deleted)
            via_devices = db.session.execute(db.text("""
                SELECT id, account_id, device_name, viam_api_key, viam_api_key_id, 
                       viam_robot_address, status, last_connected, created_at
                FROM via_device
            """)).fetchall()
            
            # Migrate each ViaDevice to Robot + UserRobot
            for via_device in via_devices:
                account_id, device_name, api_key, key_id, robot_address = (
                    via_device[1], via_device[2], via_device[3], via_device[4], via_device[5]
                )
                status, last_connected, created_at = (
                    via_device[6], via_device[7], via_device[8]
                )
                
                print(f"\nMigrating: {device_name}")
                
                # Check if robot already exists with this address
                robot = Robot.query.filter_by(
                    viam_robot_address=robot_address
                ).first()
                
                if not robot:
                    # Create new robot
                    robot = Robot(
                        robot_name=device_name,
                        viam_robot_address=robot_address,
                        status=status or 'disconnected',
                        last_connected=last_connected,
                        created_at=created_at
                    )
                    db.session.add(robot)
                    db.session.flush()
                    print(f"  Created new Robot: {robot.robot_name}")
                else:
                    print(f"  Robot already exists: {robot.robot_name}")
                
                # Check if user already has this robot
                existing_user_robot = UserRobot.query.filter_by(
                    account_id=account_id,
                    robot_id=robot.id
                ).first()
                
                if not existing_user_robot:
                    # Create UserRobot connection
                    user_robot = UserRobot(
                        account_id=account_id,
                        robot_id=robot.id,
                        viam_api_key=api_key,
                        viam_api_key_id=key_id,
                        added_at=created_at
                    )
                    db.session.add(user_robot)
                    print(f"  Created UserRobot connection for account {account_id}")
                else:
                    print(f"  UserRobot connection already exists")
            
            db.session.commit()
            print("\n✓ Migration completed successfully!")
            print("\nIMPORTANT: You can now delete the old via_device table if desired.")
            print("To drop the via_device table, run:")
            print('  python3 -c "from main import db; db.engine.execute(\'DROP TABLE IF EXISTS via_device\')"')
            
        except Exception as e:
            if "no such table: via_device" in str(e):
                print("✓ via_device table doesn't exist - already migrated!")
            else:
                print(f"Error during migration: {e}")
                db.session.rollback()
                raise

if __name__ == '__main__':
    migrate()
