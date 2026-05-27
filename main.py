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

    mode_help_text = '''Set animation mode by name or number:
      1: colorful_cross   8: sine_wave
      2: wave             9: color_spring
      3: ripple          10: flower_wave
      4: starlight       11: kill_two_birds
      5: stream          12: circle_wave
      6: shadow (static) 13: snow_trace
      7: mountain_wave'''

    parser = argparse.ArgumentParser(description='HE68Lite Keyboard Control', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--color', type=int, nargs=3, metavar=('R', 'G', 'B'), help='Set the keyboard color (RGB)')
    parser.add_argument('--brightness', type=int, default=4, help='Set the keyboard brightness (0-4)')
    parser.add_argument('--speed', type=int, help='Set animation speed (0-4)')
    parser.add_argument('--mode', type=str, help=mode_help_text)

    # Doesn't need arguments, entering it turns it on
    parser.add_argument('--rainbow', action='store_true', help='Enable automatic rainbow colors')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    keyboard = HE68Lite()

    if args.mode: keyboard.set_mode(args.mode)
    if args.speed is not None: keyboard.set_speed(args.speed)
    if args.brightness is not None: keyboard.set_brightness(args.brightness)

    # If both --color and --rainbow, color wins.
    if args.color:
        keyboard.set_color(*args.color)
    elif args.rainbow:
        keyboard.set_rainbow(True)
    keyboard.close()

if __name__ == "__main__":
    main()