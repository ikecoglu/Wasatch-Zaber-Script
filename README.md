# Wasatch-Zayber-Script
Instructions to install a scanning script for Wasatch/Zayber.

Operation:
- Script does not run if the Enlighten software is open
- Script starts in the top right and snake scans to the bottom left
- Dark is collected and live subtracted from all readings

*Intended Devices*
Wasatch Device: WP 785x
Zaber Platform: X-LSM025A


## MAC:
Using [Homebrew]([url](https://brew.sh/)) run 'brew install libusb'

## Dependencies
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

Dependencies listed were collected from the script and from Wasatch Github: https://github.com/WasatchPhotonics/Wasatch.PY/ 