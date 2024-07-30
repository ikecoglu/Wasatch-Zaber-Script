import csv
import sys
import time
from zaber_motion import Units
from zaber_motion.ascii import Connection
import wasatch
from wasatch.WasatchBus import WasatchBus
from wasatch.WasatchDevice import WasatchDevice
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog

# VARIABLE PARAMETERS for Zaber movement
step_number = 2 # grid with dimensions a x a
step_size = 10  # micrometers
velocity = 100  # micrometers/second

dark_spectrum = None

# Function to save spectrum data to CSV
def save_file(data, file_path):
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Wavelength', 'Intensity'])
        for i, value in enumerate(data):
            writer.writerow([i, value])

# Function to collect dark-subtracted spectrum and to plot it in real time
def collect_spectrum(correct_dark=True):
    global dark_spectrum
    spectrum = device.hardware.get_line().data.spectrum
    if correct_dark and dark_spectrum is not None:
        spectrum = [s - d for s, d in zip(spectrum, dark_spectrum)]
    plt.plot(spectrum)
    plt.show(block=False)
    plt.pause(0.1)
    plt.clf()
    return spectrum

# Function to collect dark spectrum for dark subtraction
def take_dark_scan():
    global dark_spectrum
    device.hardware.set_laser_enable(False)
    time.sleep(5)
    dark_spectrum = device.hardware.get_line().data.spectrum
    print("Dark scan collected")

# Function to move devices to origin coordinates before initiating scan
def move_to_position(device, position, vel):
    axis = device.get_axis(1)
    axis.move_absolute(position, unit=Units.LENGTH_MICROMETRES, velocity=vel, velocity_unit=Units.VELOCITY_MICROMETRES_PER_SECOND)

# Function to move device in one direction and save spectrum
def move_device(device, step_number, step_size, vel, base_file_path, save_counter):
    axis = device.get_axis(1)
    for x in range(step_number):
        axis.move_relative(step_size, unit=Units.LENGTH_MICROMETRES, velocity=vel, velocity_unit=Units.VELOCITY_MICROMETRES_PER_SECOND)
        spectrum = collect_spectrum()
        
        # Save the spectrum data to a unique CSV file
        save_counter[0] += 1
        file_path = f'{base_file_path}_step_{save_counter[0]}.csv'
        save_file(spectrum, file_path)
        print(f'Spectrum saved to {file_path}')

# Function to create the raster movement
def move_snake(device1, device2, step_number, step_size, vel, base_file_path):
    save_counter = [0]  # Using a list to keep the counter mutable across function calls
    axis = device2.get_axis(1)
    for x in range(step_number):
        move_device(device1, step_number, step_size * (-1) ** x, vel, base_file_path, save_counter)
        axis.move_relative(step_size, unit=Units.LENGTH_MICROMETRES, velocity=vel, velocity_unit=Units.VELOCITY_MICROMETRES_PER_SECOND)

# Tkinter setup to get the file path for saving CSV files
root = tk.Tk()
root.withdraw()  # Hide the root window
base_file_path = filedialog.asksaveasfilename(title="Save CSV File")
print(base_file_path)
root.destroy()

if not base_file_path:
    print("No file path provided")
    import sys
    sys.exit(1)

bus = WasatchBus()
if not bus.device_ids:
    print("No spectrometers found")
    sys.exit(1)

device_id = bus.device_ids[0]
print("Found %s" % device_id)

device = WasatchDevice(device_id)
if not device.connect():
    print("Connection failed")
    sys.exit(1)

print("Connected to %s %s with %d pixels from (%.2f, %.2f)" % (
    device.settings.eeprom.model,
    device.settings.eeprom.serial_number,
    device.settings.pixels(),
    device.settings.wavelengths[0],
    device.settings.wavelengths[-1]))

# VARIABLE PARAMETER for integration time
device.hardware.set_integration_time_ms(100)
print("Integration time set")

with Connection.open_serial_port("/dev/tty.usbserial-A10NFU4I") as connection:
    device_list = connection.detect_devices()
    print("Found {} devices".format(len(device_list)))
    
    if len(device_list) < 2:
        print("Not enough devices found")
        sys.exit(1)
    
    device1 = device_list[0]
    device2 = device_list[1]

    axis = device1.get_axis(1)
    if not axis.is_homed():
        axis.home()

    axis = device2.get_axis(1)
    if not axis.is_homed():
        axis.home()

    # VARIABLE PARAMETERS for origin coordinates and velocity
    move_to_position(device1, 2841.212, 1000)
    move_to_position(device2, 12972.574, 1000)

    take_dark_scan()

    # VARIABLE PARAMETER for laser power
    device.hardware.set_laser_enable(True)
    device.hardware.set_laser_power_mW(100)
    time.sleep(15)
    print("Laser initiated")

    move_snake(device1, device2, step_number, step_size, velocity, base_file_path)

device.hardware.set_laser_enable(False)
print("Laser off, scans saved :)")