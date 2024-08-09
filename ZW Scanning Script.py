import csv
import sys
import time
from datetime import datetime
from zaber_motion import Units
from zaber_motion.ascii import Connection
from wasatch.WasatchBus import WasatchBus
from wasatch.WasatchDevice import WasatchDevice
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox

# This script does not run if the Enlighten software is open

# VARIABLE PARAMETERS for Zaber movement
step_number     = 10 # grid with dimensions a x a
step_size       = 100  # micrometers
velocity        = 300  # micrometers/second

# VARIABLE PARAMETERS for Wasatch scans
integration_time    = 5000 # millisec
laser_power         = 450 # mW

# File Saving
save_seperately = True # if false, all readings will be saved into one file

# Function to save spectrum data to CSV
def save_file(data, file_path, multifile=False):
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)

        if (multifile):
            # Writing the header for multifile with multiple intensity columns
            writer.writerow(['Pixel'] + [i for i in range(len(data))])

            for i in range(len(data[0])):
                row = [i] + [d[i] for d in data]
                writer.writerow(row)
        else:
            writer.writerow(['Pixel', 'Intensity'])
            for i, value in enumerate(data):
                writer.writerow([i, value])

dark_spectrum = None
# Function to collect dark-subtracted spectrum and to plot it in real time
def collect_spectrum(correct_dark=True):
    global dark_spectrum
    spectrum = spectrometer.hardware.get_line().data.spectrum
    if correct_dark and dark_spectrum is not None:
        spectrum = [s - d for s, d in zip(spectrum, dark_spectrum)]
    plt.plot(spectrum)
    plt.show(block=False)
    plt.pause(0.001)
    plt.clf()
    return spectrum

# Function to collect dark spectrum for dark subtraction
def take_dark_scan():
    global dark_spectrum
    spectrometer.hardware.set_laser_enable(False)
    time.sleep(5)
    dark_spectrum = spectrometer.hardware.get_line().data.spectrum
    print("Dark scan collected")

# Function to move platform to origin coordinates before initiating scan
def move_to_position(platform, position, vel):
    axis = platform.get_axis(1)
    axis.move_absolute(position, unit=Units.LENGTH_MICROMETRES, velocity=vel, velocity_unit=Units.VELOCITY_MICROMETRES_PER_SECOND)

# Function to move device in one direction and save spectrum
def move_platform(platform, step_number, step_size, vel, base_file_path, save_counter, spectra):
    axis = platform.get_axis(1)
    for x in range(step_number):
        axis.move_relative(step_size, unit=Units.LENGTH_MICROMETRES, velocity=vel, velocity_unit=Units.VELOCITY_MICROMETRES_PER_SECOND)
        spectrum = collect_spectrum()
 
        if (save_seperately):
            save_counter[0] += 1
            # Save the spectrum data to a unique CSV file
            file_path = f'{base_file_path}_step_{save_counter[0]}.csv'
            save_file(spectrum, file_path)
            print(f'Spectrum saved to {file_path}')
        else:
            # add spectrum
            for i in range(len(spectrum)):
                spectra[i].append(spectrum[i])

# Function to create the raster movement
def move_snake(platform1, platform2, step_number, step_size, vel, base_file_path):
    save_counter = [0]  # Using a list to keep the counter mutable across function calls
    spectra = [[0]]

    plt.ion()
    plt.title("Spectrum Test")
    plt.xlabel("Pixels")
    plt.ylabel("Intensity")

    axis = platform2.get_axis(1)
    for x in range(step_number):
        move_platform(platform1, step_number, step_size * (-1) ** x, vel, base_file_path, save_counter, spectra)
        axis.move_relative(step_size, unit=Units.LENGTH_MICROMETRES, velocity=vel, velocity_unit=Units.VELOCITY_MICROMETRES_PER_SECOND)

    if (not save_seperately):
        save_file(spectra, f'{base_file_path}.csv', multifile=True)

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

spectrometer = WasatchDevice(device_id)
if not spectrometer.connect():
    print("Connection failed: 1")
    sys.exit(1)

if spectrometer.settings.eeprom.model == None:
    print("Connection failed: 2")
    sys.exit(1)

print("Connected to %s %s with %d pixels from (%.2f, %.2f)" % (
    spectrometer.settings.eeprom.model,
    spectrometer.settings.eeprom.serial_number,
    spectrometer.settings.pixels(),
    spectrometer.settings.wavelengths[0],
    spectrometer.settings.wavelengths[-1]))

spectrometer.hardware.set_integration_time_ms(integration_time)
print("Integration time set")

with Connection.open_serial_port("/dev/tty.usbserial-A10NFU4I") as connection:
    device_list = connection.detect_devices()
    print("Found {} devices".format(len(device_list)))
    
    if len(device_list) < 2:
        print("Not enough devices found")
        sys.exit(1)
    
    platform1 = device_list[0]
    platform2 = device_list[1]

    axis = platform1.get_axis(1)
    if not axis.is_homed():
        axis.home()

    axis = platform2.get_axis(1)
    if not axis.is_homed():
        axis.home()

    # VARIABLE PARAMETERS for origin coordinates and velocity
    move_to_position(platform1, 4018.65, 5000)
    move_to_position(platform2, 15289.72, 5000)
    
    take_dark_scan()

    spectrometer.hardware.set_laser_enable(True)
    spectrometer.hardware.set_laser_power_mW(laser_power)

    # time.sleep(15)
    print("Laser initiated")

    move_snake(platform1, platform2, step_number, step_size, velocity, base_file_path)

spectrometer.hardware.set_laser_enable(False)

root = tk.Tk()
root.withdraw()
messagebox.showinfo("Notification", f"Zaber-Wastach Script Finished!\n{datetime.now().strftime("%I:%M:%S %p")}")
root.destroy()

print(f"Laser off, scans saved :) -- {datetime.now().strftime("%I:%M:%S %p")}")