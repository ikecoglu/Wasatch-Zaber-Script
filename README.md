# Wasatch-Zayber-Script
Instructions to install a scanning script for Wasatch/Zayber

Wasatch Device: WP 785x

Zaber Platform: X-LSM025A


## MAC:
**Dependencies**

I recommend using conda with the added channels because we noticed that the version on pip and base conda caused problems with USB detection

	pip install zaber-motion
	pip install wasatch

 	pip install matplotlib.pyplot
   	pip install numpy
  
	conda config --add channels conda-forge
	conda config --add channels bioconda
 
	conda install seabreeze	
	conda install mkl
	conda install six
	conda install psutil
	conda install future
	conda install pygtail
 	conda install pyusb
	conda install requests
 	conda install pexpect
	conda install seabreeze
 	conda install pyudev

Dependencies listed were collected from the script and from Wasatch Github: https://github.com/WasatchPhotonics/Wasatch.PY/ 
 
## WINDOWS:
  TBD
