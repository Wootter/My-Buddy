"""Audio processing module using Koala and Cobra"""
import pvkoala
import pvcobra
from pvrecorder import PvRecorder


def setup_koala(access_key):
    """
    Initialize Koala noise suppression
    
    Args:
        access_key: Picovoice access key
        
    Returns:
        Initialized Koala instance
    """
    koala = pvkoala.create(access_key=access_key)
    return koala


def setup_cobra(access_key):
    """
    Initialize Cobra voice activity detection
    
    Args:
        access_key: Picovoice access key
        
    Returns:
        Initialized Cobra instance
    """
    cobra = pvcobra.create(access_key=access_key)
    return cobra


def setup_recorder(mic_index, frame_length):
    """
    Initialize microphone recorder
    
    Args:
        mic_index: Index of microphone to use
        frame_length: Frame length for recording
        
    Returns:
        Initialized PvRecorder instance
    """
    recorder = PvRecorder(
        device_index=mic_index,
        frame_length=frame_length,
    )
    recorder.start()
    return recorder


def select_microphone(mic_name_hints):
    """
    Auto-detect and select appropriate microphone
    
    Args:
        mic_name_hints: List of microphone name hints to match
        
    Returns:
        Index of selected microphone
        
    Raises:
        RuntimeError: If no suitable microphone found
    """
    devices = PvRecorder.get_available_devices()
    print("Available audio devices:")
    for i, d in enumerate(devices):
        print(f"  {i}: {d}")
    
    mic_index = None
    
    # Try known USB mic identifiers
    for i, d in enumerate(devices):
        if "monitor" in d.lower():
            continue
        if any(hint.lower() in d.lower() for hint in mic_name_hints):
            mic_index = i
            break
    
    # Fallback to first non-monitor device
    if mic_index is None:
        for i, d in enumerate(devices):
            if "monitor" not in d.lower():
                mic_index = i
                break
    
    if mic_index is None:
        raise RuntimeError("No usable capture microphone found")
    
    print(f"Using microphone: {devices[mic_index]}")
    return mic_index
