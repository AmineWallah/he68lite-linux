import usb.core
import usb.util

# Vendor and product IDs for the Epomaker HE68 lite
VENDOR_ID = 0x3151
PRODUCT_ID = 0x5029

def set_keyboard_color(r, g, b):
    # Figuring out our keyboard
    device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if device is None:
        raise ValueError('Keyboard not found')

    # Detaching driver from interface 2 (presumably for RGB control)
    interface = 2
    if device.is_kernel_driver_active(interface):
        device.detach_kernel_driver(interface)

    # Building our payload (PRESUMABLY: [start of frame, command class, target zone, animation mode, brightness/speed?, R, G, B, Checksum]
    payload = [0x07, 0x08, 0x03, 0x04, 0x07, r, g, b]

    ## Calculating checksum then appending it to the payload
    total_sum = sum(payload)
    checksum = 0xFF - (total_sum & 0xFF)
    payload.append(checksum)

    # Padding the payload to reach the 64 byte length requirement
    payload += [0x00] * (64 - len(payload))

    # Sending the control transfer using exact parameters grabbed from Wireshark
    try:
        device.ctrl_transfer(
            bmRequestType=0x21,
            bRequest=0x09, # SET_REPORT
            wValue=0x0300,
            wIndex=0x0002, # Our interface number
            data_or_wLength = payload
        )
        print(f"Keyboard color set to {r}, {g}, {b}")
    except usb.core.USBError as e:
        print(f"Error setting keyboard color: {e}")
    finally:
        # Reattaching the driver to interface 2
        usb.util.dispose_resources(device)
        try:
            device.attach_kernel_driver(interface)
        except Exception as e:
            print(f"Error reattaching driver: {e}")


def main():
    set_keyboard_color(16, 212, 242)

if __name__ == "__main__":
    main()