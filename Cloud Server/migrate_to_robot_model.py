"""
Migration script to convert ViaDevice to Robot + UserRobot model.
Run this once on your server to migrate existing data.

Usage: python migrate_to_robot_model.py
"""

from main import app, db
from models import Account, Robot, UserRobot, ViaDevice
from datetime import datetime

def migrate():
    with app.app_context():
        print("Starting migration from ViaDevice to Robot + UserRobot...")
        
        # Check if old via_device table exists
        via_devices = ViaDevice.query.all()
        
        if not via_devices:
            print("No ViaDevice records found. Database might already be migrated.")
            return
        
        print(f"Found {len(via_devices)} ViaDevice records to migrate...")
        
        # Migrate each ViaDevice to Robot + UserRobot
        for via_device in via_devices:
            print(f"\nMigrating: {via_device.device_name}")
            
            # Check if robot already exists with this address
            robot = Robot.query.filter_by(
                viam_robot_address=via_device.viam_robot_address
            ).first()
            
            if not robot:
                # Create new robot
                robot = Robot(
                    robot_name=via_device.device_name,
                    viam_robot_address=via_device.viam_robot_address,
                    status=via_device.status,
                    last_connected=via_device.last_connected,
                    created_at=via_device.created_at
                )
                db.session.add(robot)
                db.session.flush()  # Get the robot ID
                print(f"  Created new Robot: {robot.robot_name}")
            else:
                print(f"  Robot already exists: {robot.robot_name}")
            
            # Check if user already has this robot
            existing_user_robot = UserRobot.query.filter_by(
                account_id=via_device.account_id,
                robot_id=robot.id
            ).first()
            
            if not existing_user_robot:
                # Create UserRobot connection
                user_robot = UserRobot(
                    account_id=via_device.account_id,
                    robot_id=robot.id,
                    viam_api_key=via_device.viam_api_key,
                    viam_api_key_id=via_device.viam_api_key_id,
                    added_at=via_device.created_at
                )
                db.session.add(user_robot)
                print(f"  Created UserRobot connection for account {via_device.account_id}")
            else:
                print(f"  UserRobot connection already exists")
        
        try:
            db.session.commit()
            print("\n✓ Migration completed successfully!")
            print("\nIMPORTANT: You can now delete the old via_device table if desired.")
            print("To drop the via_device table, run:")
            print('  python -c "from main import db; db.engine.execute(\'DROP TABLE IF EXISTS via_device\')"')
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Migration failed: {e}")
            raise

if __name__ == '__main__':
    migrate()
