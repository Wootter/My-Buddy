"""LLM handler module for picoLLM responses"""
import picollm
import threading
from tts_piper import speak


def setup_llm(access_key, model_path):
    """
    Initialize picoLLM language model
    
    Args:
        access_key: Picovoice access key
        model_path: Path to picoLLM model
        
    Returns:
        Initialized picoLLM instance
    """
    pllm = picollm.create(
        access_key=access_key,
        model_path=model_path
    )
    return pllm


def generate_response(pllm, user_input, system_prompt="You are Buddy, an offline home assistant. Be brief and helpful."):
    """
    Generate LLM response and stream it to TTS
    
    Args:
        pllm: Initialized picoLLM instance
        user_input: User's message
        system_prompt: System prompt for LLM behavior
        
    Returns:
        Full generated response text
    """
    buffer = []
    
    def stream_callback(token):
        """Called for each generated token"""
        print(token, end='', flush=True)
        buffer.append(token)
        
        # Speak complete sentences as they're generated
        if token in '.!?\n':
            sentence = ''.join(buffer).strip()
            if sentence:
                threading.Thread(target=speak, args=(sentence,), daemon=True).start()
            buffer.clear()
    
    # Generate response
    pllm.generate(
        prompt=f"{system_prompt}\n\nUser: {user_input}\nBuddy:",
        completion_token_limit=50,
        stop_phrases=['\n'],
        temperature=0,
        stream_callback=stream_callback
    )
    
    # Speak any remaining text
    if buffer:
        sentence = ''.join(buffer).strip()
        if sentence:
            threading.Thread(target=speak, args=(sentence,), daemon=True).start()
    
    return ''.join(buffer)
