import sys
import argparse
import os
from he68lite import *

def elevate():
    if os.getuid() != 0:
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

def main():
    # Makes sure the script runs with elevated permissions
    elevate()

    parser = argparse.ArgumentParser(description='HE68Lite Keyboard Control')
    parser.add_argument('--color', type=int, nargs=3, metavar=('R', 'G', 'B'), help='Set the keyboard color (RGB)')
    parser.add_argument('--brightness', type=int, default=4, help='Set the keyboard brightness (0-4)')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    keyboard = HE68Lite()

    if args.color: keyboard.set_color(*args.color)

    if args.brightness is not None: keyboard.set_brightness(args.brightness)

    keyboard.close()

if __name__ == "__main__":
    main()