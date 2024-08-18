import sys
import time
import pandas as pd
from datetime import datetime
from zaber_motion import Units
from zaber_motion.ascii import Connection
from wasatch.WasatchBus import WasatchBus
from wasatch.WasatchDevice import WasatchDevice
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox
from pynput import keyboard

# OPERATION INFO
    # Script does not run if the Enlighten software is open
    # Script starts in the top right and snake scans to the bottom left
    # Dark is collected and live subtracted from all readings

# VARIABLE PARAMETERS for Zaber movement
step_number     = 2 # grid with dimensions a x a
step_size       = 25  # micrometers
velocity        = 300  # micrometers/second
origin          = (4018.65, 15289.72) # origin co-ordinates (x, y)

# VARIABLE PARAMETERS for Wasatch scans
integration_time    = 5000 # millisec
laser_power         = 450 # mW

# Files
try:
    wavenumbers = pd.read_csv('/Users/milo/Documents/CREST/Wasatch-Zayber-Script/wavenumbers1.csv') # path to wavenumbers
except FileNotFoundError as e:
    print(f'{e}\nProvide valid file path to wavenumbers.csv file\n')
    sys.exit(1)

#region Function Definitions

# Function to listen for keyboard input to stop the process
def listen_for_stop(key):
    global stop_flag
    if key == keyboard.Key.backspace or key == keyboard.Key.delete:
        print("Keyboard Interruption")
        stop_flag = True

# Function to save spectrum data to CSV
def save_file(data, file_path):
    data_df = pd.DataFrame()
    if (wavenumbers is not None):
        data_df['Wavenumber'] = wavenumbers.iloc[:, 0]
    data_df['Intensity'] = data
    data_df.to_csv(file_path)

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
        save_counter[0] += 1
        # Save the spectrum data to a unique CSV file
        file_path = f'{base_file_path}_step_{save_counter[0]}.csv'
        save_file(spectrum, file_path)
        print(f'Spectrum saved to {file_path}')

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
        if stop_flag:
                return
        axis.move_relative(step_size, unit=Units.LENGTH_MICROMETRES, velocity=vel, velocity_unit=Units.VELOCITY_MICROMETRES_PER_SECOND)

    save_file(spectra, f'{base_file_path}.csv')

#endregion

#region Device Connection

bus = WasatchBus()
if not bus.device_ids:
    print("No spectrometers found")
    sys.exit(1)

device_id = bus.device_ids[0]
print("Found %s" % device_id)

spectrometer = WasatchDevice(device_id)
if not spectrometer.connect():
    print("Connection failed: spectrometer.connect() call failed. \n-Ensure that ENLGIHTEN software is closed")
    sys.exit(1)

if spectrometer.settings.eeprom.model == None:
    print("Connection failed: blank connection")
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

#endregion

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

# abort script flag thread started
print('Press delete/backspace to stop the script')
stop_flag = False
listener = keyboard.Listener(on_press=listen_for_stop)
listener.start()

# move to origin co-ordinates
move_to_position(platform1, origin[0], 5000)
move_to_position(platform2, origin[1], 5000)
    
take_dark_scan()

spectrometer.hardware.set_laser_enable(True)
spectrometer.hardware.set_laser_power_mW(laser_power)

# time.sleep(15)
print("Laser initiated")

# Begin scans
move_snake(platform1, platform2, step_number, step_size, velocity, base_file_path)

spectrometer.hardware.set_laser_enable(False)
listener.join()
plt.close()

if (not stop_flag):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Notification", f"Zaber-Wastach Script Finished!\n{datetime.now().strftime("%I:%M:%S %p")}")
    root.destroy()

print(f"Laser off, scans saved :) -- {datetime.now().strftime("%I:%M:%S %p")}")

'''
Further Script Development
-------------------------
*Quality of Life*
- Should average multiple darks and/or despike the dark in case of cosmic spike during dark collection
- Solve the connection error that requires you to re-run the script multiple times
- Can’t get laser to start (junk readings)
    - time.sleep() doesn't seem to be enough and wasatch's sdk get_laser_temperature() seems broken
    -  maybe take random readings before starting and wait till spectra reaches certain threshold
- Fix matplot regenerating the window for each reading
- Check if file with same name is already present
- If disconnected during runtime, retry connection
- Check spectrometer temp before running (should be ~ -15 Celsius)
'''