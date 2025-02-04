import cv2
import time
import numpy as np
import configparser
import easyocr
import keyboard
import multiprocessing as mp
import torch
import os
import warnings
from mss import mss

# Suppress PyTorch warnings
warnings.filterwarnings('ignore', category=FutureWarning)

def verify_cuda():
    if not torch.cuda.is_available():
        print("CUDA is not available. Please check your installation:")
        print("1. Run: pip uninstall torch torchvision")
        print("2. Run: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
        return False
    print(f"CUDA available: {torch.cuda.get_device_name(0)}")
    return True

if not verify_cuda():
    raise RuntimeError("CUDA initialization failed")

reader = easyocr.Reader(['en'], gpu=True)

def read_coordinates():
    try:
        config = configparser.ConfigParser()
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'settings.ini')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Settings file not found at: {config_path}")
            
        if not config.read(config_path):
            raise ValueError(f"Could not read settings file at: {config_path}")
        
        coordinates = config['DEFAULT']
        return map(int, (coordinates['x1'], coordinates['y1'], coordinates['x2'], coordinates['y2']))
    except Exception as e:
        print(f"\nError reading coordinates: {str(e)}")
        print("\nPlease ensure settings.ini exists in the same directory as main.py with format:")
        print("[DEFAULT]")
        print("x1=840")
        print("y1=1020")
        print("x2=910")
        print("y2=1044")
        exit(1)

def capture_screen(sct, region):
    screen = np.array(sct.grab(region))
    return cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)

def process_screen(screen):
    global min_hp
    global armlet_button
    global cooldown
    text = reader.readtext(screen, detail = 0)
    if len(text) > 0:
        hp = text[0]
        print(f"Detected HP: {hp}", end='\r')
        if hp.isdigit() and int(hp) <= min_hp:
            print('\nABUZE!! HP triggered at:', hp)
            try:
                # Single press
                keyboard.press(armlet_button)
                keyboard.release(armlet_button)
                print(f"Sent keyboard input: {armlet_button}")
                time.sleep(cooldown)
            except Exception as e:
                print(f"Keyboard input failed: {str(e)}")
    else:
        print("No HP value detected", end='\r')

def screen_processing(sct, region):
    print("\nMonitoring started! Press Ctrl+C to stop.")
    print(f"Watching for HP <= {min_hp} to trigger {armlet_button} key")
    print("-" * 50)
    while True:
        start_time = time.time()
        screen = capture_screen(sct, region)
        process_screen(screen)
        end_time = time.time()
        fps = 1 / (end_time - start_time)
        print(f'FPS: {round(fps)}   ', end='\r')

def main():
    try:
        # Test keyboard access
        print("Testing keyboard access...")
        keyboard.press_and_release('shift')  # Test if keyboard works
        print("Keyboard access OK")
        
        print("Reading coordinates from settings.ini...")
        x1, y1, x2, y2 = read_coordinates()
        print(f"Capture region set to: ({x1}, {y1}) to ({x2}, {y2})")
        
        with mss() as sct:
            region = {'top': y1, 'left': x1, 'width': x2-x1, 'height': y2-y1}
            screen_processing(sct, region)
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        exit(1)

if __name__ == "__main__":
    min_hp = 200
    armlet_button = 'x'
    cooldown = 0.5
    mp.set_start_method('spawn')
    main()