from pymem import Pymem
from pymem.process import module_from_name
import time
import keyboard
import struct

class DotaMemoryScanner:
    def __init__(self):
        try:
            self.pm = Pymem("dota2.exe")
            self.client = module_from_name(self.pm.process_handle, "client.dll")
            self.engine = module_from_name(self.pm.process_handle, "engine2.dll")
            print("Connected to Dota 2 process")
            print(f"client.dll base: {hex(self.client.lpBaseOfDll)}")
            print(f"engine2.dll base: {hex(self.engine.lpBaseOfDll)}")
        except Exception as e:
            print(f"Failed to connect to Dota 2: {str(e)}")
            exit(1)

    def scan_for_hp_value(self, target_hp):
        """Scan memory for current HP value to find potential addresses"""
        print(f"\nScanning for HP value: {target_hp}")
        
        # Convert target HP to different formats for scanning
        patterns = [
            target_hp.to_bytes(4, byteorder='little'),  # 32-bit little endian
            target_hp.to_bytes(4, byteorder='big'),     # 32-bit big endian
            str(target_hp).encode('ascii')              # ASCII string
        ]

        found_addresses = []
        for pattern in patterns:
            # Scan client.dll memory region
            results = self.pm.pattern_scan_module(
                pattern,
                self.client,
                return_multiple=True
            )
            if results:
                found_addresses.extend(results)

        return found_addresses

    def scan_pointer_path(self, final_address):
        """Find possible pointer paths to an address"""
        print(f"\nScanning for pointer paths to {hex(final_address)}")
        
        # Scan for addresses that contain our target address
        possible_pointers = []
        
        # Get memory regions to scan
        scan_start = self.client.lpBaseOfDll
        scan_end = scan_start + self.client.SizeOfImage
        
        # Scan in chunks to avoid memory issues
        chunk_size = 0x1000
        current_addr = scan_start
        
        while current_addr < scan_end:
            try:
                # Read a chunk of memory
                chunk = self.pm.read_bytes(current_addr, chunk_size)
                
                # Look for potential pointers in the chunk
                for i in range(0, len(chunk) - 8, 4):
                    value = struct.unpack("<Q", chunk[i:i+8])[0]
                    if value == final_address:
                        pointer = current_addr + i
                        offset = pointer - self.client.lpBaseOfDll
                        possible_pointers.append((pointer, offset))
                        print(f"Found pointer at {hex(pointer)} (offset: {hex(offset)})")
                
            except:
                pass
            current_addr += chunk_size
        
        return possible_pointers

    def monitor_with_pointers(self, base_addresses):
        """Monitor addresses and their pointer paths"""
        print("\nMonitoring addresses and their pointers...")
        print("1. Take note of addresses that change with your HP")
        print("2. Look for consistent pointer paths")
        print("3. Press ESC to stop monitoring")
        
        previous_values = {}
        pointer_paths = {}
        
        for addr in base_addresses:
            try:
                previous_values[addr] = self.pm.read_int(addr)
                # Find pointers to this address
                pointer_paths[addr] = self.scan_pointer_path(addr)
            except:
                previous_values[addr] = None

        while True:
            if keyboard.is_pressed('esc'):
                break

            for addr in base_addresses:
                try:
                    current = self.pm.read_int(addr)
                    if current != previous_values[addr]:
                        offset = addr - self.client.lpBaseOfDll
                        print(f"\nValue changed at {hex(addr)} (offset: {hex(offset)})")
                        print(f"Previous: {previous_values[addr]} -> Current: {current}")
                        
                        # Show pointer paths
                        if addr in pointer_paths:
                            print("Possible pointer paths:")
                            for ptr, off in pointer_paths[addr]:
                                print(f"  client.dll+{hex(off)} -> {hex(addr)}")
                        
                        previous_values[addr] = current
                except:
                    continue
            
            time.sleep(0.1)

def main():
    print("\nDota 2 HP Offset Finder")
    print("----------------------")
    print("Steps to find HP offset:")
    print("1. Start Dota 2 and pick any hero")
    print("2. Note your exact HP value")
    print("3. Enter that HP value when prompted")
    print("4. Change your HP in game (take damage or heal)")
    print("5. Watch for addresses that change with your HP")
    print("6. Look for consistent pointer paths")
    print("\nPress Enter to start...")
    input()

    scanner = DotaMemoryScanner()
    
    while True:
        try:
            current_hp = int(input("\nEnter your current HP value in game: "))
            break
        except ValueError:
            print("Please enter a valid number")

    addresses = scanner.scan_for_hp_value(current_hp)
    
    if not addresses:
        print("No addresses found containing the HP value")
        return

    print(f"\nFound {len(addresses)} potential addresses")
    scanner.monitor_with_pointers(addresses)

if __name__ == "__main__":
    main()
