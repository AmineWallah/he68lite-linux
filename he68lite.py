import usb.core
import usb.util
import json
import os
import pwd
from pathlib import Path

class HE68Lite:
    def __init__(self):
        # Check if script is running under sudo
        sudo_user = os.environ.get('SUDO_USER')

        if sudo_user:
            # Get the real home directory of the sudo user
            real_home = Path(pwd.getpwnam(sudo_user).pw_dir)
        else:
            real_home = Path.home()

        # Path for user home directory
        self.config_dir = real_home / ".config" / "he68lite"
        self.config_file = self.config_dir / "state.json"

        # Constants
        self.KEYS = {
            'esc': 0x01, 'tab': 0x02, 'caps': 0x03, 'lshift': 0x04, 'lctrl': 0x05,
            '1': 0x07, '2': 0x0D, '3': 0x13, '4': 0x19, '5': 0x1F,
            '6': 0x25, '7': 0x2B, '8': 0x31, '9': 0x37, '0': 0x3D,
            'q': 0x08, 'w': 0x0E, 'e': 0x14, 'r': 0x1A, 't': 0x20,
            'y': 0x26, 'u': 0x2C, 'i': 0x32, 'o': 0x38, 'p': 0x3E,
            'a': 0x09, 's': 0x0F, 'd': 0x15, 'f': 0x1B, 'g': 0x21,
            'h': 0x27, 'j': 0x2D, 'k': 0x33, 'l': 0x39,
            'z': 0x10, 'x': 0x16, 'c': 0x1C, 'v': 0x22, 'b': 0x28,
            'n': 0x2E, 'm': 0x34,
            ',': 0x3A, '.': 0x40, '/': 0x46, ';': 0x3F, "'": 0x45,
            '[': 0x44, ']': 0x4A, '-': 0x43, '=': 0x49, '\\': 0x50,
            'space': 0x29, 'win': 0x0B, 'lalt': 0x11, 'ralt': 0x3B,
            'fn': 0x41, 'rctrl': 0x47, 'rshift': 0x4C,
            'enter': 0x51, 'backspace': 0x4F,
            'up': 0x52, 'down': 0x53, 'left': 0x4D, 'right': 0x59,
            'home': 0x55, 'del': 0x56, 'pgup': 0x57, 'pgdn': 0x58
        }




        # Default state
        self.r, self.g, self.b = 255, 0 ,0
        self.brightness = 4
        self.speed = 2
        self.mode = 0x08
        self.is_rainbow = False # Should be on byte 4
        self.actuations = {key: 2.0 for key in self.KEYS}

        # Load state from config file if exists
        self._load_state()

        # Checking if keyboard is plugged in
        self.device = usb.core.find(idVendor=0x3151, idProduct=0x5029)
        if self.device is None:
            raise ValueError('Keyboard not found')

        # Detach driver from interface 2
        if self.device.is_kernel_driver_active(2):
            self.device.detach_kernel_driver(2)
    def set_mode(self, mode_input):
        mode_keys = list(self.MODES.keys())
        mode_values = list(self.MODES.values())

        try:
            mode_index = int(mode_input) - 1
            if mode_index < 0 or mode_index >= len(mode_keys):
                print(f"Invalid mode. Available modes: {', '.join(mode_keys)}")
                return
            else:
                mode_value = mode_values[mode_index]
                self.mode = mode_value
                self._send_update()
                return
        except ValueError:
            pass # If input is not a number, try to match by name

        target_mode = str(mode_input).lower().replace(' ', '_')
        if target_mode in self.MODES:
            self.mode = self.MODES[target_mode]
            self._send_update()
            return
        else:
            print(f"Invalid mode. Available modes: {', '.join(mode_keys)}")

    def set_color(self, r, g, b):
        self.r = max(0, min(255, r))
        self.g = max(0, min(255, g))
        self.b = max(0, min(255, b))

        self.is_rainbow = False
        self._send_update()

    def set_rainbow(self, enable=True):
        self.is_rainbow = enable
        self._send_update()

    def set_brightness(self, level):
        if level < 0: level = 0
        if level > 4: level = 4
        self.brightness = level
        self._send_update()

    def set_speed(self, level):
        self.speed = max(0, min(4, level))
        self._send_update()

    def set_key_actuation(self, key_name, distance_mm, save=True): # Faulty (check readme.md)
        key_name = str(key_name).lower()
        if key_name not in self.KEYS:
            print(f"Invalid key name: {key_name}")
            return

        key_id = self.KEYS[key_name]

        # Ensure distance is within safe range (safe_distance is an estimate for now, needs to be confirmed later on)
        safe_distance = max(0.1, min(3.0, float(distance_mm)))
        distance_int = round(safe_distance / 0.005)

        dist_lsb = distance_int & 0xFF
        dist_msb = (distance_int >> 8) & 0xFF

        # The keyboard requires TWO reports per key update:
        # Report 0x00 (Press Actuation) and Report 0x01 (Release/Rapid Trigger)
        for report_type in [0x00, 0x01]:
            payload = [0x65, report_type, 0x00, key_id, report_type, 0x00, 0x00]

            # Calculate the special 7-byte checksum for magnetic switches
            checksum = 0xFF - (sum(payload) & 0xFF)
            payload.append(checksum)

            payload.extend([dist_lsb, dist_msb])

            payload += [0x00] * (64 - len(payload))

            self.device.ctrl_transfer(
                bmRequestType=0x21,
                bRequest=0x09,
                wValue=0x0300,
                wIndex=0x0002,
                data_or_wLength=payload
            )

        self.actuations[key_name] = safe_distance

        if save:
            self._save_state()

        print(f"Set '{key_name.upper()}' to {safe_distance}mm")

    def _send_update(self):
        # Inverts the speed value to match the hardware
        hardware_speed = 4 - self.speed

        color_toggle = 0x08 if self.is_rainbow else 0x07
        color_data = [0xFA, 0xFF, 0xFA] if self.is_rainbow else [self.r, self.g, self.b]

        payload = [0x07, self.mode, hardware_speed, self.brightness, color_toggle] + color_data

        # Checksum so that the keyboard doesn't drop the payload
        checksum = 0xFF - (sum(payload) & 0xFF)
        payload.append(checksum)

        # Padding to match size
        payload += [0x00] * (64 - len(payload))

        self.device.ctrl_transfer(
            bmRequestType=0x21,
            bRequest=0x09,  # SET_REPORT
            wValue=0x0300,
            wIndex=0x0002,  # Our interface number
            data_or_wLength=payload
        )

        # Saves state in json file after applying changes
        self._save_state()

    def _save_state(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump({
                'color': [self.r, self.g, self.b],
                'brightness': self.brightness,
                'speed': self.speed,
                'mode': self.mode,
                'is_rainbow': self.is_rainbow,
                'actuations': self.actuations
            }, f, indent=4)

    def _load_state(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    s = json.load(f)

                    self.r, self.g, self.b = s.get('color', [self.r, self.g, self.b])
                    self.brightness = s.get('brightness', self.brightness)
                    self.speed = s.get('speed', self.speed)
                    self.mode = s.get('mode', self.mode)
                    self.is_rainbow = s.get('is_rainbow', self.is_rainbow)
                    self.actuations = s.get('actuations', self.actuations)  # <-- Added this line
            except Exception:
                pass


    def close(self):
        usb.util.dispose_resources(self.device)
        try:
            self.device.attach_kernel_driver(2)
        except Exception as e:
            print(f"Error reattaching driver: {e}")