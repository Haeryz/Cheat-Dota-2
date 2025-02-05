import time
import keyboard
import warnings
from pymem import Pymem
from pymem.process import module_from_name

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

class Dota2Memory:
    def __init__(self):
        try:
            self.pm = Pymem("dota2.exe")
            self.module = module_from_name(self.pm.process_handle, "client.dll").lpBaseOfDll
            print("Successfully connected to Dota 2 process")
        except Exception as e:
            print(f"Failed to connect to Dota 2: {str(e)}")
            print("Make sure Dota 2 is running")
            exit(1)

    def read_hp(self):
        try:
            # These offsets need to be updated after Dota 2 patches
            # You'll need to find current offsets using tools like Cheat Engine
            player_base = self.module + 0x0  # Replace with actual offset
            hp_offset = 0x0  # Replace with actual offset
            
            hp_address = self.pm.read_int(player_base)
            hp_address = self.pm.read_int(hp_address + hp_offset)
            
            return self.pm.read_int(hp_address)
        except Exception as e:
            print(f"Failed to read HP: {str(e)}")
            return 0

def main():
    try:
        print("Testing keyboard access...")
        keyboard.press_and_release('shift')
        print("Keyboard access OK")
        
        dota = Dota2Memory()
        print("\nMonitoring started! Press Ctrl+C to stop.")
        print(f"Watching for HP <= {min_hp} to trigger {armlet_button} key")
        print("-" * 50)
        
        while True:
            current_hp = dota.read_hp()
            print(f"Current HP: {current_hp}", end='\r')
            
            if current_hp <= min_hp and current_hp > 0:
                print(f'\nABUZE!! HP triggered at: {current_hp}')
                keyboard.press(armlet_button)
                keyboard.release(armlet_button)
                print(f"Sent keyboard input: {armlet_button}")
                time.sleep(cooldown)
            
            time.sleep(0.01)  # Small delay to prevent excessive CPU usage
            
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        exit(1)

if __name__ == "__main__":
    min_hp = 200
    armlet_button = 'x'
    cooldown = 0.5
    main()