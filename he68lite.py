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
        self.config_dir = Path.home() / ".config" / "he68lite"
        self.config_file = self.config_dir / "state.json"

        self.r = 255
        self.g = 0
        self.b = 0
        self.brightness = 4

        # Load state from config file if exists
        self._load_state()

        # Checking if keyboard is plugged in
        self.device = usb.core.find(idVendor=0x3151, idProduct=0x5029)
        if self.device is None:
            raise ValueError('Keyboard not found')

        # Detach driver from interface 2
        if self.device.is_kernel_driver_active(2):
            self.device.detach_kernel_driver(2)

    def set_color(self, r, g, b):
        if r < 0 or r > 255: r = 0
        self.r = r
        if g < 0 or g > 255: g = 0
        self.g = g
        if b < 0 or b > 255: b = 0
        self.b = b
        self._send_update()

    def set_brightness(self, level):
        if level < 0: level = 0
        if level > 4: level = 4
        self.brightness = level
        self._send_update()

    def _send_update(self):
        payload = [0x07, 0x08, 0x03, self.brightness, 0x07, self.r, self.g, self.b]

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
                'brightness': self.brightness
            }, f, indent=4)

    def _load_state(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    state = json.load(f)

                    # Grab the array (defaulting to current colors if missing)
                    saved_color = state.get('color', [self.r, self.g, self.b])

                    self.r, self.g, self.b = saved_color

                    self.brightness = state.get('brightness', self.brightness)
            except Exception:
                pass


    def close(self):
        usb.util.dispose_resources(self.device)
        try:
            self.device.attach_kernel_driver(2)
        except Exception as e:
            print(f"Error reattaching driver: {e}")