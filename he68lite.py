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

        # Default state
        self.r, self.g, self.b = 255, 0 ,0
        self.brightness = 4
        self.speed = 2
        self.mode = 0x08
        self.is_rainbow = False # Should be on byte 4

        self.MODES = {
            'colorful_cross': 0x03, 'wave': 0x04, 'ripple': 0x05,
            'starlight': 0x06, 'stream': 0x07, 'shadow': 0x08,
            'mountain_wave': 0x09, 'sine_wave': 0x0a, 'color_spring': 0x0b,
            'flower_wave': 0x0c, 'kill_two_birds': 0x0e,
            'circle_wave': 0x0f, 'snow_trace': 0x13
        }

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
                'color': [self.r, self.g, self.b],  # Saved as an array
                'brightness': self.brightness,
                'speed': self.speed,
                'mode': self.mode,
                'is_rainbow': self.is_rainbow
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
            except Exception:
                pass


    def close(self):
        usb.util.dispose_resources(self.device)
        try:
            self.device.attach_kernel_driver(2)
        except Exception as e:
            print(f"Error reattaching driver: {e}")