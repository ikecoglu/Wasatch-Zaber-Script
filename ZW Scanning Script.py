import sys
import os
import time
import pandas as pd
import numpy as np
from datetime import datetime
from zaber_motion import Units
from zaber_motion.ascii import Connection
from wasatch.WasatchBus import WasatchBus
from wasatch.WasatchDevice import WasatchDevice
from scipy.ndimage import median_filter
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox

'''
OPERATION INFO ------------------------
    # Wait for spectrometer to reach -15 celsius
    # Script does not run if the Enlighten software is open
    # May fail to connect multiple times in a row. You must persevere over the machine
    # Script starts in the top right and snake scans to the bottom left
    # Dark is collected and live subtracted from all readings
    # Output file is one column for pixels, wavenumbers, and intensity
----------------------------------------
'''

# VARIABLE PARAMETERS for Zaber movement
step_number     = 10 # grid with dimensions a x a
step_size       = 60 # micrometers
velocity        = 300 # micrometers/second
origin          = (4722.02, 12454.70) # origin co-ordinates (x, y)

# VARIABLE PARAMETERS for Wasatch device
integration_time    = 5000 # millisec
laser_power         = 450 # mW

# OTHER PARAMETER
wavenum_path = '/Users/milo/Documents/CREST/Wasatch-Zayber-Script/wavenumbers.csv' # Update this path to match your wavenumber file path
despike_dark = False # set to true to despike the dark

# load wavenumbers
try:
    wavenumbers = pd.read_csv(wavenum_path)
except FileNotFoundError as e:
    print(f'{e}\nProvide valid file path to wavenumbers.csv file\n')
    sys.exit(1)

#region Function Definitions

# Function to save spectrum data to CSV
def save_file(data, file_path):
    data_df = pd.DataFrame()
    data_df.index.name = 'Pixels'
    if (wavenumbers is not None):
        data_df['Wavenumber'] = wavenumbers['Wavenumber']
    data_df['Intensity'] = data
    data_df.to_csv(file_path)

dark_spectrum = None
# Function to collect dark-subtracted spectrum and to plot it in real time
def collect_spectrum(figure, ax, line, correct_dark=True):
    global dark_spectrum
    spectrum = spectrometer.hardware.get_line().data.spectrum
    if correct_dark and dark_spectrum is not None:
        spectrum = [s - d for s, d in zip(spectrum, dark_spectrum)]

    line.set_ydata(spectrum)
    ax.set_ylim(0, max(spectrum) + 100)
    figure.canvas.draw()
    figure.canvas.flush_events()
    time.sleep(0.001)

    return spectrum

# Function to despike spectrum (used for dark reading)
def despike_spectrum(spectrum, threshold=5):
    filtered = median_filter(spectrum, size=3)
    spikes = np.abs(spectrum - filtered) > threshold
    spectrum[spikes] = filtered[spikes]
    return spectrum

# Function to collect dark spectrum for dark subtraction
def take_dark_scan(despike=False):
    global dark_spectrum
    spectrometer.hardware.set_laser_enable(False)
    time.sleep(5)
    dark_spectrum = spectrometer.hardware.get_line().data.spectrum
    if despike == True:
        despike_dark = despike_spectrum(np.array(dark_spectrum))
        dark_spectrum = despike_dark.tolist()
    print("Dark scan collected")

# Function to move platform to origin coordinates before initiating scan
def move_to_position(platform, position, vel):
    axis = platform.get_axis(1)
    axis.move_absolute(position, unit=Units.LENGTH_MICROMETRES, velocity=vel, velocity_unit=Units.VELOCITY_MICROMETRES_PER_SECOND)

# Function to move device in one direction and save spectrum
def move_platform(platform, step_number, step_size, vel, base_file_path, save_counter, figure, ax, line):
    axis = platform.get_axis(1)
    for x in range(step_number):
        axis.move_relative(step_size, unit=Units.LENGTH_MICROMETRES, velocity=vel, velocity_unit=Units.VELOCITY_MICROMETRES_PER_SECOND)
        spectrum = collect_spectrum(figure, ax, line)
        save_counter[0] += 1
        # Save the spectrum data to a unique CSV file
        file_path = f'{base_file_path}_step_{save_counter[0]}.csv'
        save_file(spectrum, file_path)
        print(f'Spectrum saved to {file_path}')

# Function to create the raster movement
def move_snake(platform1, platform2, step_number, step_size, vel, base_file_path):
    save_counter = [0]  # Using a list to keep the counter mutable across function calls

    plt.ion()
    figure, ax = plt.subplots(figsize=(10, 8))
    line, = ax.plot(wavenumbers['Wavenumber'], dark_spectrum)
    plt.title(f"Spectrum")
    plt.xlabel("Wavenumbers")
    plt.ylabel("Intensity")

    axis = platform2.get_axis(1)
    for x in range(step_number):
        move_platform(platform1, step_number, step_size * (-1) ** x, vel, base_file_path, save_counter, figure, ax, line)
        axis.move_relative(step_size, unit=Units.LENGTH_MICROMETRES, velocity=vel, velocity_unit=Units.VELOCITY_MICROMETRES_PER_SECOND)

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
    print("Connection failed: spectrometer.connect() call failed. \n- Ensure that ENLGIHTEN software is closed")
    sys.exit(1)

# sometimes it will connect, but all info is blank. this checks for that
if spectrometer.settings.eeprom.model == None:
    print("Connection failed: blank connection")
    sys.exit(1)

# display device ingo
print("Connected to %s %s with %d pixels from (%.2f, %.2f)" % (
    spectrometer.settings.eeprom.model,
    spectrometer.settings.eeprom.serial_number,
    spectrometer.settings.pixels(),
    spectrometer.settings.wavelengths[0], # these wavelength values are incorrect for some reason
    spectrometer.settings.wavelengths[-1]))

spectrometer.hardware.set_integration_time_ms(integration_time)
spectrometer.hardware.set_laser_power_mW(laser_power)
print("Power and Integration time set")

#endregion

# Tkinter setup to get the file path for saving CSV files
root = tk.Tk()
root.withdraw()  # Hide the root window
base_file_path = filedialog.asksaveasfilename(title="Save CSV File")
print(base_file_path)
root.destroy()

# check if file path was provided
if not base_file_path:
    print("No file path provided")
    import sys
    sys.exit(1)

# check if file name already exists and prompt user
if os.path.exists(base_file_path + '_step_1.csv'): # this is poorly hardcoded
    print("File path already exists")
    while(True):
        user_input = input("This path will override other files. Do you want to continue? (yes/no): ").strip().lower()
        if user_input == "yes" or user_input == 'y':
            break
        elif user_input == "no" or user_input == 'n':
            print("Process aborted")
            sys.exit(1)
        else:
            print("Invalid input. Please enter 'yes' or 'no'")

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

    # move to origin co-ordinates
    move_to_position(platform1, origin[0], 6000)
    move_to_position(platform2, origin[1], 6000)
        
    take_dark_scan()

    spectrometer.hardware.set_laser_enable(True)

    print("Laser initiated")

    # Begin scans
    move_snake(platform1, platform2, step_number, step_size, velocity, base_file_path)

spectrometer.hardware.set_laser_enable(False)

# Script end pop-up
root = tk.Tk()
root.withdraw()
messagebox.showinfo("Notification", f"Zaber-Wasatch Script Finished!\n{datetime.now().strftime("%I:%M:%S %p")}")
root.destroy()

print(f"Laser off, scans saved :) -- {datetime.now().strftime("%I:%M:%S %p")}")

'''
Further Script Development
-------------------------
*Bugs*
- Solve the connection error that requires you to re-run the script multiple times
- segmentation fault occasionally (save_file problem when same name?)
- Can't close zaber software while script is running. it will disable zaber connection
- matplot icon on messagebox?
- Wasatch connection giving wrong wavenumber range (~795-1059)

*Quality of Life*
- Ending the script
    - must be done properly or the laser stays on
    - Should listen for a key to end the script
    - Closing the matplot window should end the script
- False Laser Start (junk readings)
    - time.sleep() doesn't seem to be enough and wasatch's sdk get_laser_temperature() seems broken
    - maybe take random readings before starting and wait till spectra reaches certain threshold. 
        Could risk burning sample? maybe scan the material next to it
- Reset zaber position to zero at end of script
- get matplot to regenerate when alt-tabbing (need to refresh more often? or on select?)
- fix hard-coded file name check with 'step_1'
- Reogranize zaber connection code
- If disconnected during runtime, retry connection
- Spectrometer check and info
    - Check spectrometer temp before running (should be ~ -15 Celsius)
    - Check that laser key is turned
'''