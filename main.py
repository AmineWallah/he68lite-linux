import usb.core
import usb.util
import argparse
import sys

class HE68Lite:
    def __init__(self):
        self.r = 255
        self.g = 0
        self.b = 0
        self.brightness = 4

        # Checking if keyboard is plugged in
        self.device = usb.core.find(idVendor=0x3151, idProduct=0x5029)
        if self.device is None:
            raise ValueError('Keyboard not found')

        # Detach driver from interface 2
        if self.device.is_kernel_driver_active(2):
            self.device.detach_kernel_driver(2)

    def set_color(self, r, g, b):
        self.r = r
        self.g = g
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

    def close(self):
        usb.util.dispose_resources(self.device)
        try:
            self.device.attach_kernel_driver(2)
        except Exception as e:
            print(f"Error reattaching driver: {e}")


def main():
    parser = argparse.ArgumentParser(description='HE68Lite Keyboard Control')
    parser.add_argument('--color', type=int, nargs=3, metavar=('R', 'G', 'B'), help='Set the keyboard color (RGB)')
    parser.add_argument('--brightness', type=int, default=4, help='Set the keyboard brightness (0-4)')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    
    args = parser.parse_args()

    keyboard = HE68Lite()

    if args.color: keyboard.set_color(*args.color) # light blue btw

    if args.brightness is not None: keyboard.set_brightness(args.brightness)

    keyboard.close()

if __name__ == "__main__":
    main()