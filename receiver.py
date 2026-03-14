import numpy as np
import sounddevice as sd
from scipy.signal import butter, filtfilt

# --- Configuration ---
TARGET_FREQ = 18000.0
BANDWIDTH = 500.0     # Look at 19.5kHz to 20.5kHz
FS = 48000            # Sample rate (must match transmitter)
RECORD_SECONDS = 60   # How long to listen
UNIT_DURATION = 0.15  # Must match transmitter (80ms)
THRESHOLD_MULTIPLIER = 0.5

# Reverse Morse Dictionary for decoding
MORSE_DICT = {
    '.-': 'a', '-...': 'b', '-.-.': 'c', '-..': 'd', '.': 'e',
    '..-.': 'f', '--.': 'g', '....': 'h', '..': 'i', '.---': 'j',
    '-.-': 'k', '.-..': 'l', '--': 'm', '-.': 'n', '---': 'o',
    '.--.': 'p', '--.-': 'q', '.-.': 'r', '...': 's', '-': 't',
    '..-': 'u', '...-': 'v', '.--': 'w', '-..-': 'x', '-.--': 'y',
    '--..': 'z'
}

def decode_live_audio():
    print(f"Listening for {RECORD_SECONDS} seconds... Send your message now!")

    # Capture audio directly from the laptop microphone
    recording = sd.rec(int(RECORD_SECONDS * FS), samplerate=FS, channels=1, dtype='float32')
    sd.wait()  # Block execution until the recording window finishes

    print("Processing signal...")
    data = recording[:, 0]

    # 1. Bandpass Filter (Isolate 20kHz)
    nyq = 0.5 * FS
    b, a = butter(5, [(TARGET_FREQ - BANDWIDTH) / nyq, (TARGET_FREQ + BANDWIDTH) / nyq], btype='band')
    filtered_data = filtfilt(b, a, data)

    # 2. Envelope Detection (Full-wave rectification + smoothing)
    rectified = np.abs(filtered_data)
    window_size = int(FS * UNIT_DURATION / 4)
    envelope = np.convolve(rectified, np.ones(window_size)/window_size, mode='same')

    # 3. Thresholding (Convert to binary 1s and 0s)
    fixed_min_threshold=0.010
    binary_signal = (envelope > fixed_min_threshold).astype(int)

    # 4. Extract Timings
    changes = np.diff(binary_signal)
    edges = np.where(changes != 0)[0]

    if len(edges) == 0:
        return "No pulses detected."

    # Parse lengths of pulses (ON) and gaps (OFF)
    message = ""
    current_symbol = ""
    samples_per_unit = FS * UNIT_DURATION

    for i in range(len(edges) - 1):
        duration_samples = edges[i+1] - edges[i]

        # Calculate raw units and round to nearest whole block
        raw_units = duration_samples / samples_per_unit
        blocks = round(raw_units)

        # Ignore microscopic static spikes
        if blocks == 0:
            continue

        is_tone = binary_signal[edges[i] + 1] == 1

        if is_tone:
            # --- TONES (Dots vs Dashes) ---
            # Dots are ~1 block. Dashes are ~5 blocks.
            # We set the cutoff right in the middle at 3.
            if blocks <= 4:       
                current_symbol += "."
            else:                 
                current_symbol += "-"
        else:
            # --- SILENCES (Gaps) ---
            # Inside-letter gaps are ~2 blocks. Between-letter gaps are ~7 blocks.
            if blocks <= 7:
                # Just a gap inside the letter. Keep building it.
                pass
            elif blocks <= 12:
                # Gap between letters. Time to translate the symbol!
                if current_symbol:
                    decoded_letter = MORSE_DICT.get(current_symbol, '?')
                    if decoded_letter == '?':
                        print(f"DEBUG: I heard [{current_symbol}] but that's not a real letter!")
                    message += decoded_letter
                    current_symbol = ""
            else:
                # Massive gap. End of a word.
                if current_symbol:
                    decoded_letter = MORSE_DICT.get(current_symbol, '?')
                    if decoded_letter == '?':
                        print(f"DEBUG: I heard [{current_symbol}] but that's not a real letter!")
                    message += decoded_letter + " "
                    current_symbol = ""

    # Catch the very last symbol when the audio cuts off
    if current_symbol:
        decoded_letter = MORSE_DICT.get(current_symbol, '?')
        message += decoded_letter

    return message.strip()

if __name__ == "__main__":
    result = decode_live_audio()
    print(f"\n--- Decoded Message --- \n{result}\n-----------------------")