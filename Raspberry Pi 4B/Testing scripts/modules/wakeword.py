"""Wake word detection module using Picovoice Porcupine"""
import pvporcupine


def setup_wakeword(access_key, keyword_path):
    """
    Initialize Porcupine wake word detector
    
    Args:
        access_key: Picovoice access key
        keyword_path: Path to wake word model
        
    Returns:
        Initialized Porcupine instance
    """
    porcupine = pvporcupine.create(
        access_key=access_key,
        keyword_paths=[keyword_path],
    )
    return porcupine
