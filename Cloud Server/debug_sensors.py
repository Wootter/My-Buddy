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
        
        # Check DHT22 Temperature & Humidity
        print("1. DHT22 Temperature & Humidity Sensor:")
        try:
            dht = ViamSensor.from_robot(robot, "dht22_sensor")
            readings = await dht.get_readings()
            print(f"   Raw readings: {readings}")
            if 'temperature_celsius' in readings:
                print(f"   → Temperature: {readings['temperature_celsius']}°C")
            if 'humidity_percent' in readings:
                print(f"   → Humidity: {readings['humidity_percent']}%")
        except Exception as e:
            print(f"   ERROR: {e}")
        
        # Check VEML7700
        print("\n2. VEML7700 Light Sensor:")
        try:
            veml = ViamSensor.from_robot(robot, "VEML7700")
            readings = await veml.get_readings()
            print(f"   Raw readings: {readings}")
            if 'lux' in readings:
                print(f"   → Light Level: {readings['lux']} lux")
        except Exception as e:
            print(f"   ERROR: {e}")
        
        # Check MH-SR602
        print("\n3. MH-SR602 Motion Sensor:")
        try:
            motion = ViamSensor.from_robot(robot, "MH-SR602")
            readings = await motion.get_readings()
            print(f"   Raw readings: {readings}")
            if 'motion_detected' in readings:
                status = "MOTION DETECTED" if readings['motion_detected'] else "No motion"
                print(f"   → Status: {status}")
        except Exception as e:
            print(f"   ERROR: {e}")
            
    finally:
        await robot.close()

if __name__ == "__main__":
    asyncio.run(debug_sensors())
