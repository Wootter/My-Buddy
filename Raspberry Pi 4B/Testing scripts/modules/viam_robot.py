"""Viam robot connection and control module"""
import asyncio
from viam.robot.client import RobotClient


async def connect_robot(robot_address, api_key_id, api_key):
    """
    Connect to Viam robot
    
    Args:
        robot_address: Robot address from Viam
        api_key_id: API key ID
        api_key: API key
        
    Returns:
        Connected RobotClient instance
    """
    opts = RobotClient.Options.with_api_key(
        api_key=api_key,
        api_key_id=api_key_id,
    )
    robot = await RobotClient.at_address(robot_address, opts)
    print("Connected to robot")
    return robot
