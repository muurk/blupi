#!/usr/bin/env python3

__doc__ = "blupi"

import argparse
import logging
import time
import os
import subprocess as sp
from os import devnull
from collections import deque
from math import sqrt

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
required_params = parser.add_argument_group("Required Arguments")
optional_params = parser.add_argument_group("Optional Arguments")
optional_params.add_argument('--freqmin', help="Minimum Frequency", type=int, default=854000000)
optional_params.add_argument('--freqmax', help="Maximum Frequency", type=int, default=860000000)
optional_params.add_argument('--sensitivity', help="Sensitivity", type=int, default=50)
optional_params.add_argument('--sysdamping', help="Sysdamping", type=int, default=10)
optional_params.add_argument('--freqdamping', help="Freqdamping", type=int, default=100)
optional_params.add_argument("--powerfftw_path", help="Path to rtl_power_fftw binary", type=str,
							 default="/usr/local/bin/rtl_power_fftw")
optional_params.add_argument("--baseline_path", help="Baseline Data", type=str,
							 default="baseline_data.dat")
optional_params.add_argument("--ppm_offset", help="PPM Offset", type=int, default=56)
optional_params.add_argument("--bline_int_t", help="bline_int_t", type=int, default=600)
optional_params.add_argument("--debug", help="Verbose Messaging", action='store_true', default=False)

args = parser.parse_args()

if args.debug is True:
	logger.setLevel(logging.DEBUG)

# Global variables until we have a config file
freqmin = args.freqmin
freqmax = args.freqmax
sensitivity = args.sensitivity
sysdamping = args.sysdamping
freqdamping = args.freqdamping
powerfftw_path = args.powerfftw_path
baseline_path = args.baseline_path
totalbins = 960 * 3 # DO NOT CHANGE
ppm_offset = args.ppm_offset
bline_int_t = args.bline_int_t

# Global that we'll keep
dvnll = open(devnull, 'wb')

# Functions
def average(p): return sum(p) / float(len(p))

def variance(p): return map(lambda x: (x - average(p))**2, p)

def std_dev(p): return sqrt(average(variance(p)))

def alert(p):

	# Still developing...need to provide true alert functionality (GPIO, audio, etc)
	freq = round(p[0] /1000000, 4)
	logger.debug("At " + time.strftime("%H:%M:%S") + ", a " + str(round(p[1], 1)) + " dB/Hz signal was detected at " + str(freq) + " MHz.")

def bline_build(fmin, fmax, bins, b_time, offset, bpath):
	t = "-t " + str(b_time)
	array = []
	spect = "-f " + str(fmin) + ":" + str(fmax)
	b_bins = "-b %i" % (int(bins/3))

	base_gen = sp.Popen([powerfftw_path, spect, t, offset, b_bins], stdout=sp.PIPE, stderr=dvnll, shell=False)

	for line in iter(base_gen.stdout.readline, b""):

		with open(baseline_path, 'a') as baselinefile: baselinefile.write(str(line))

# Start your engines...
if __name__ == '__main__':
	# Import settings file here...

	# Parameter formatting
	spect = "-f " + str(freqmin) + ":" + str(freqmax)

	fftb = totalbins / 3 # NEED TO DEVELOP

	fftbins = "-b %i" % int(fftb)
	ppm = "-p " + str(ppm_offset)
	otherargs = "-c"
	rolling = []
	rolling_avg = deque([])
	sweep = deque([])
	i = 0
	stddev = 100
	baseline_file = "-B " + str(baseline_path)

	# Ready, set, GO!
	try:
		logger.debug("Starting up")
		
		# Check for baseline file
		if not os.path.isfile(baseline_path):
			logger.debug(f"{baseline_path}: Baseline file not found. Generating a new one.")
			# Generate said baseline file
			bline_build(freqmin, freqmax, fftb, bline_int_t, ppm, baseline_path)
			logger.debug(f"{baseline_path}: Baseline file generation completed.")

		rpf = sp.Popen([powerfftw_path, spect, otherargs, ppm, fftbins, baseline_file], stdout=sp.PIPE, stderr=dvnll, shell=False)

		# Let's see what's going on with rtl_power_fftw
		for line in iter(rpf.stdout.readline, b""):

			# Ignore garbage output
			if not ('#' in line or not line.strip()):

				floats = map(float, line.split())

				# Create 2D array if it isn't already defined
				if len(rolling) < totalbins: rolling.append(deque([]))

				rolling[i].append(floats[1])
				sweep.append(floats[1])

				# Let's start filtering...
				if len(rolling[i]) >= freqdamping:
					rolling[i].popleft()
					alarmthresh = average(rolling[i]) + stddev / sensitivity * 25000

					#if i == 0: print floats[1], alarmthresh - floats[1]

					# There be coppers!
					if floats[1] > alarmthresh:

						alert(floats)

				# Maintain sweep length at the total number of samples
				if len(sweep) > totalbins: sweep.popleft()

				# Increment or reset indexer (i)
				if i < totalbins - 1: i = i + 1
				else: 
					i = 0

					# Maintain rolling_avg
					rolling_avg.append(average(sweep))

					if len(rolling_avg) > sysdamping: 
						rolling_avg.popleft()
						stddev = std_dev(rolling_avg)

	except (KeyboardInterrupt, SystemExit): # Press ctrl-c

		rpf.kill()
		logger.debug("\n", "Buh-bye")
