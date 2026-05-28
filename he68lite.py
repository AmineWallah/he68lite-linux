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
        self.MODES = {
            'colorful_cross': 0x03, 'wave': 0x04, 'ripple': 0x05,
            'starlight': 0x06, 'stream': 0x07, 'shadow': 0x08,
            'mountain_wave': 0x09, 'sine_wave': 0x0a, 'color_spring': 0x0b,
            'flower_wave': 0x0c, 'kill_two_birds': 0x0e,
            'circle_wave': 0x0f, 'snow_trace': 0x13
        }

        self.KEYS = {
            # Take note that there is a 'ghost' 6th row hence why some numbers are skipped
            'esc': 0x01, 'tab': 0x02, 'caps': 0x03, 'lshift': 0x04, 'lctrl': 0x05,
            '1': 0x07, 'q': 0x08, 'a': 0x09, 'z': 0x0A, 'win': 0x0B,
            '2': 0x0D, 'w': 0x0E, 's': 0x0F, 'x': 0x10, 'lalt': 0x11,
            '3': 0x13, 'e': 0x14, 'd': 0x15, 'c': 0x16,
            '4': 0x19, 'r': 0x1A, 'f': 0x1B, 'v': 0x1C,
            '5': 0x1F, 't': 0x20, 'g': 0x21, 'b': 0x22,
            '6': 0x25, 'y': 0x26, 'h': 0x27, 'n': 0x28, 'space': 0x29,
            '7': 0x2B, 'u': 0x2C, 'j': 0x2D, 'm': 0x2E,
            '8': 0x31, 'i': 0x32, 'k': 0x33, ',': 0x34,
            '9': 0x37, 'o': 0x38, 'l': 0x39, '.': 0x3A, 'ralt': 0x3B,
            '0': 0x3D, 'p': 0x3E, ';': 0x3F, '/': 0x40,
            '-': 0x43, '[': 0x44, "'": 0x45,
            '=': 0x49, ']': 0x4A, '\\': 0x50,
            'backspace': 0x4F, 'enter': 0x51, 'rshift': 0x4C,
            'fn': 0x41, 'rctrl': 0x47,
            'home': 0x55, 'del': 0x56, 'pgup': 0x57, 'pgdn': 0x58,
            'up': 0x52, 'left': 0x4D, 'down': 0x53, 'right': 0x59
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

    def set_key_actuation(self, key_name, distance_mm, save=True):
        key_name = str(key_name).lower()
        if key_name not in self.KEYS:
            print(f"Invalid key name: {key_name}")
            return

        key_id = self.KEYS[key_name]

        # Ensure distance is within safe range (safe_distance is an estimate for now, needs to be confirmed later on)
        safe_distance = max(0.1, min(4.0, float(distance_mm)))
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

    def set_keyboard_actuation(self, distance_mm):
        # Set actuation for all keys simultaneously
        for key in self.KEYS:
            self.set_key_actuation(key, distance_mm, save=False)

        self._save_state()

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