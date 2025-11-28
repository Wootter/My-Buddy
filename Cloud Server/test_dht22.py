#!/usr/bin/env python3
"""
Quick DHT22 diagnostic script
"""
import asyncio
from viam.robot.client import RobotClient
from viam.components.sensor import Sensor as ViamSensor

async def test_dht22():
    # Replace with your actual credentials
    API_KEY = input("Enter your Viam API Key: ")
    API_KEY_ID = input("Enter your Viam API Key ID: ")
    ROBOT_ADDRESS = input("Enter your Robot Address: ")
    
    opts = RobotClient.Options.with_api_key(
        api_key=API_KEY,
        api_key_id=API_KEY_ID
    )
    
    print(f"Connecting to {ROBOT_ADDRESS}...")
    robot = await RobotClient.at_address(ROBOT_ADDRESS, opts)
    
    try:
        print("\n=== AVAILABLE COMPONENTS ===")
        for resource in robot.resource_names:
            print(f"  {resource}")
        
        print("\n=== TESTING DHT22 ===")
        
        # Test different possible component names
        possible_names = ['dht22_sensor', 'dht22', 'DHT22', 'temperature_sensor']
        
        for name in possible_names:
            try:
                print(f"\nTrying component name: '{name}'")
                sensor = ViamSensor.from_robot(robot, name)
                print(f"  ✓ Got sensor object: {type(sensor)}")
                
                readings = await sensor.get_readings()
                print(f"  ✓ Readings: {readings}")
                
                # Check for expected keys
                if 'temperature_celsius' in readings:
                    print(f"    → Temperature: {readings['temperature_celsius']}°C")
                if 'humidity_percent' in readings:
                    print(f"    → Humidity: {readings['humidity_percent']}%")
                
                break  # Found working component
                
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                
    finally:
        await robot.close()

if __name__ == "__main__":
    asyncio.run(test_dht22())