import numpy as np
import sounddevice as sd

# Configuration Parameters
FREQUENCY = 18000.0   
SAMPLE_RATE = 48000   
UNIT_DURATION = 0.150  

# Expanded Dictionary so you can type any word
MORSE_DICT = {
    'a': '.-', 'b': '-...', 'c': '-.-.', 'd': '-..', 'e': '.',
    'f': '..-.', 'g': '--.', 'h': '....', 'i': '..', 'j': '.---',
    'k': '-.-', 'l': '.-..', 'm': '--', 'n': '-.', 'o': '---',
    'p': '.--.', 'q': '--.-', 'r': '.-.', 's': '...', 't': '-',
    'u': '..-', 'v': '...-', 'w': '.--', 'x': '-..-', 'y': '-.--',
    'z': '--..'
}

def generate_morse_audio(text):
    audio_sequence = []
    
    for char in text.lower():
        if char not in MORSE_DICT:
            # Handle spaces between words
            if char == " ":
                audio_sequence.extend(np.zeros(int(SAMPLE_RATE * UNIT_DURATION * 10)))
            continue
            
        code = MORSE_DICT[char]
        
        for symbol in code:
            # DASHES are 8x duration
            duration = UNIT_DURATION if symbol == '.' else UNIT_DURATION * 8
            
            t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
            tone = np.sin(FREQUENCY * t * 2 * np.pi)
            
            fade_len = int(SAMPLE_RATE * 0.005) 
            if len(tone) > fade_len * 2:
                tone[:fade_len] *= np.linspace(0, 1, fade_len)
                tone[-fade_len:] *= np.linspace(1, 0, fade_len)
                
            audio_sequence.extend(tone)
            
            # GAP BETWEEN DOTS/DASHES (3x)
            silence = np.zeros(int(SAMPLE_RATE * UNIT_DURATION * 3))
            audio_sequence.extend(silence)
        
        # GAP BETWEEN LETTERS (7x)
        letter_gap = np.zeros(int(SAMPLE_RATE * UNIT_DURATION * 7))
        audio_sequence.extend(letter_gap)
        
    return np.array(audio_sequence, dtype=np.float32)

if __name__ == "__main__":
    # --- CHANGE: User input instead of hardcoded word ---
    word = input("Enter the word or message you want to transmit: ")
    
    print(f"Generating 18 kHz Morse code for '{word}'...")
    audio_data = generate_morse_audio(word)
    
    print("Playing audio... (Transmission in progress)")
    sd.play(audio_data, SAMPLE_RATE)
    
    sd.wait() 
    print("Playback complete.")