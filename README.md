# HE68Lite Linux
## About
**!! STILL IN VERY EARLY DEVELOPMENT !!**

Basic linux driver to interact with the Epomaker HE68 Lite keyboard considering there is no native driver for it out there.


## Dependencies
You will need to install **python3** from your preferred package manager.

Once that is done, you will also need **pyusb** for the script to be able to communicate with the keyboard.

## Usage
- Clone the repository:
```
git clone https://github.com/Epomaker/HE68Lite-Linux.git`
```

- Run the script from the main.py file:
```aiignore
python3 main.py (--flags)
```
*Latest preset is saved in `config.json`, if some flags are not specified the script will use the values from the config file.*

*If this is your first time running the script with a few flags missing, it will use default values instead (see he68lite.py)*

### Flags:

| Flag | Arguments | Description | Example |
| :--- | :--- | :--- | :--- |
| **`--color`** | `R G B` | Sets a custom, static color using RGB values (0-255). If used alongside an animation mode, it colors that animation. **Note:** This flag takes priority and will instantly override `--rainbow`. | `--color 255 0 128` |
| **`--brightness`** | `0-4` | Sets the brightness level of the LEDs. `0` is off/dimmest, and `4` is maximum brightness. Defaults to `4`. | `--brightness 2` |
| **`--speed`** | `0-4` | Sets the speed of the current animation. `0` is the slowest, and `4` is the fastest. | `--speed 4` |
| **`--mode`** | `name` or `1-13` | Sets the lighting effect. You can pass the exact text name (e.g., `ripple`) or its corresponding ID number (1 through 13). | `--mode 3` <br> `--mode starlight` |
| **`--rainbow`** | *None* | A toggle switch that forces the current animation to cycle through RGB colors automatically instead of using a static color. | `--mode wave --rainbow` |
| **`--actuation`** | `KEY MM` | Sets the magnetic actuation distance for a specific key. Distance can range from `0.1` to `4.0` millimeters. | `--actuation w 1.5` |
| **`--actuation-all`** | `MM` | Sets the magnetic actuation distance for all keys simultaneously. Distance can range from `0.1` to `4.0` millimeters. | `--actuation-all 2.0` |
| **`--list-keys`** | *None* | Prints a neatly formatted list of all valid key names that can be used with the `--actuation` flag. | `python3 main.py --list-keys` |
| **`-h`, `--help`** | *None* | Prints the help menu to the terminal, including the exact syntax and the 1-13 cheat sheet for all available modes. | `python3 main.py --help` |

#### Available modes: (with --mode flag)
1. `colorful_cross`
2. `wave`
3. `ripple`
4. `starlight`
5. `stream`
6. `shadow`
7. `mountain_wave`
8. `sine_wave`
9. `color_spring`
10. `flower_wave`
11. `kill_two_birds`
12. `circle_wave`
13. `snow_trace`

## Known issues
- The actuation/actuation-all flags are not working properly for a good portion of the keys (will remap the key ID dictionary soon enough)
