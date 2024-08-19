# Wasatch-Zayber-Script
Instructions to install a scanning python script for Wasatch/Zayber.

Operation:
- Script does not run if the Enlighten software is open
- May fail to connect multiple times in a row. You must persevere over the machine
- Script starts in the top right and snake scans to the bottom left
- Dark is collected and live subtracted from all readings
- Output file is one column wavenumbers and another for intensity


*Intended Devices*

Wasatch Device: WP 785x

Zaber Platform: X-LSM025A


## MAC:
Using [Homebrew](https://brew.sh/), run `brew install libusb` to solve a backend error

## Dependencies
Run the following command in terminal, using the dependencies.txt file from this repo
(make sure the path to the .txt file is correct)

	pip install -r dependencies.txt

or, install each dependency one by one

	pip install zaber-motion
	pip install wasatch
 	pip install matplotlib
   	pip install numpy
	pip install seabreeze
	pip install mkl
	pip install six
	pip install psutil
	pip install future
	pip install pygtail
 	pip install pyusb
	pip install requests
 	pip install pexpect
	pip install seabreeze
 	pip install pyudev
  	pip install pandas
   	pip install datetime
    pip install pynput
	pip install scipy

Dependencies listed were collected from the script and from Wasatch Github: https://github.com/WasatchPhotonics/Wasatch.PY/ 