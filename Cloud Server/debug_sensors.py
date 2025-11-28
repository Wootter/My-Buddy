"""Debug script to check raw sensor readings from Viam"""

import asyncio
from viam.robot.client import RobotClient
from viam.components.sensor import Sensor as ViamSensor

async def debug_sensors():
    # Get credentials (you'll need to fill these in)
    API_KEY = input("Enter Viam API Key: ")
    API_KEY_ID = input("Enter Viam API Key ID: ")
    ROBOT_ADDRESS = input("Enter Robot Address: ")
    
    opts = RobotClient.Options.with_api_key(
        api_key=API_KEY,
        api_key_id=API_KEY_ID
    )
    robot = await RobotClient.at_address(ROBOT_ADDRESS, opts)
    
    try:
        print("\n=== Checking all sensors ===\n")
        
        # Check VEML7700
        print("1. VEML7700 Light Sensor:")
        try:
            veml = ViamSensor.from_robot(robot, "VEML7700")
            readings = await veml.get_readings()
            print(f"   Raw readings: {readings}")
        except Exception as e:
            print(f"   ERROR: {e}")
        
        # Check DHT22
        print("\n2. DHT22 Sensor:")
        try:
            dht = ViamSensor.from_robot(robot, "dht22_sensor")
            readings = await dht.get_readings()
            print(f"   Raw readings: {readings}")
        except Exception as e:
            print(f"   ERROR: {e}")
        
        # Check MH-SR602
        print("\n3. MH-SR602 Motion Sensor:")
        try:
            motion = ViamSensor.from_robot(robot, "MH-SR602")
            readings = await motion.get_readings()
            print(f"   Raw readings: {readings}")
        except Exception as e:
            print(f"   ERROR: {e}")
            
    finally:
        await robot.close()

if __name__ == "__main__":
    asyncio.run(debug_sensors())
