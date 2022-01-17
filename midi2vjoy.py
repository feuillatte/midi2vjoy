#  midi2vjoy.py
#  
#  Copyright 2017  <c0redumb>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import sys, os, time, traceback
import ctypes
from optparse import OptionParser
import pygame.midi
import winreg

# Constants
# Axis mapping
axis = {'X': 0x30, 'Y': 0x31, 'Z': 0x32, 'RX': 0x33, 'RY': 0x34, 'RZ': 0x35,
		'SL0': 0x36, 'SL1': 0x37, 'WHL': 0x38, 'POV': 0x39}
		
# Globals
options = None

def midi_test():
	n = pygame.midi.get_count()

	# List all the devices and make a choice
	print('Input MIDI devices:')
	for i in range(n):
		info = pygame.midi.get_device_info(i)
		if info[2]:
			print(i, info[1].decode())
	d = int(input('Select MIDI device to test: '))
	
	# Open the device for testing
	try:
		print('Opening MIDI device:', d)
		m = pygame.midi.Input(d)
		print('Device opened for testing. Use ctrl-c to quit.')
		while True:
			while m.poll():
				print(m.read(1))
			time.sleep(0.1)
	except:
		m.close()
		
def read_conf(conf_file):
	'''Read the configuration file'''
	table = {}
	vjoy_ids = []
	MAPPING_TYPE_POS = 0
	MIDI_TYPE_POS = 1
	MIDI_DATA1_POS = 2
	VJOY_ID_POS = 3
	VJOY_MAP_POS = 4
	with open(conf_file, 'r') as file:
		for line in file:
			# Skip empty lines and lines staring with '#'
			if len(line.strip()) == 0 or line[0] == '#':
				continue
			# Get the conf values from the line
			confvalues = line.split()
			
			# Get the Mapping type 
			maptype = confvalues[MAPPING_TYPE_POS]

			# Get the MIDI event identifiers
			midikey = (int(confvalues[MIDI_TYPE_POS]), int(confvalues[MIDI_DATA1_POS]))

			# If we treat the line as a button conf, use an integer to refer to the vjoy button
			if maptype == 'B':
				vjoykey = (int(confvalues[VJOY_ID_POS]), int(confvalues[VJOY_MAP_POS]))
			elif maptype == 'A': # If an axis, use a string to refer to the vjoy axis
				vjoykey = (int(confvalues[VJOY_ID_POS]), confvalues[VJOY_MAP_POS])
			elif maptype == 'R': # If a 360 rotary encoder, map each direction as a button 
				vjoykey = (int(confvalues[VJOY_ID_POS]), confvalues[VJOY_MAP_POS])
			else:
				print("Unrecognized button/axis type identifier '"+maptype+"' in conf file")

				# Store the midi to vjoy mapping in the mapping table
			table[midikey] = (maptype, vjoykey)

			vjoy_id = int(confvalues[VJOY_ID_POS])
			
			# If this line contains a previously unregistered Virtual joystick ID, add it to the list
			if not vjoy_id in vjoy_ids:
				vjoy_ids.append(vjoy_id)
	return (table, vjoy_ids)
		
def joystick_run():
	# Process the configuration file
	if options.conf == None:
		print('Must specify a configuration file')
		return
	try:
		if options.verbose:
			print('Opening configuration file:', options.conf)
		(table, vjoy_ids) = read_conf(options.conf)
		if options.verbose:
			print(table)
			print(vjoy_ids)
	except:
		print('Error processing the configuration file:', options.conf)
		return
		
	# Getting the MIDI device ready
	if options.midi == None:
		print('Must specify a MIDI interface to use')
		return
	try:
		if options.verbose:
			print('Opening MIDI device:', options.midi)
		midi = pygame.midi.Input(options.midi)
	except:
		print('Error opting MIDI device:', options.midi)
		return
		
	# Load vJoysticks
	try:
		# Load the vJoy library
		#print(installpath[0])
		dll_file = "C:\\Program Files\\vJoy\\x64\\vJoyInterface.dll"
		vjoy = ctypes.WinDLL(dll_file)
		if options.verbose:
			print("vJoy DLL Version: "+str(vjoy.GetvJoyVersion()))
			
	except:
		print('Error initializing the vJoy DLL')
		return
	try:	
		# Getting ready
		for vid in vjoy_ids:
			if options.verbose:
				print('Acquiring vJoystick:', vid)
			assert(vjoy.AcquireVJD(vid) == 1)
			assert(vjoy.GetVJDStatus(vid) == 0)
			vjoy.ResetVJD(vid)
	except:
		print('Error initializing virtual joysticks. Make sure vJoy is configured correctly')
		return
	
	try:
		print('midi2vjoy Ready. Use ctrl-c to quit.')
		while True:
			while midi.poll():
				input = midi.read(1)
				#print(input)
				midikey = tuple(input[0][0][0:2])
				datareading = input[0][0][2]
				# Check that the input is defined in table, otherwise skip
				if options.verbose:
					print(midikey, datareading)
				if not midikey in table:
					continue
				maptype = table[midikey][0]
				output = table[midikey][1]
				joy_id = output[0]
				joy_mapping = output[1]
				if maptype == "A":
					# A slider input
					# Check that the output axis is valid
					# Note: We did not check if that axis is defined in vJoy
					if not joy_mapping in axis:
						continue
					datareading = (datareading + 1) << 8
					vjoy.SetAxis(datareading, output[0], axis[joy_mapping])
				elif maptype == "B":
					# A button input
					vjoy.SetBtn(datareading, output[0], int(joy_mapping))
				elif maptype == "R":
					# Rotary encoder input
					directionbuttons = joy_mapping.split(',')
					if datareading == 1:
						joy_mapping = directionbuttons[0]
						vjoy.SetBtn(127,output[0], int(joy_mapping))
						time.sleep(0.02)
						vjoy.SetBtn(0,joy_id, int(joy_mapping))
					elif datareading == 127:
						joy_mapping = directionbuttons[1]
						vjoy.SetBtn(127, joy_id, int(joy_mapping))
						time.sleep(0.02)
						vjoy.SetBtn(0,joy_id, int(joy_mapping))
				elif midikey[0] == 128:
					# A button off input
					vjoy.SetBtn(datareading, joy_id, int(joy_mapping))
					
				if options.verbose:
					print(midikey, '->', output, datareading)

			time.sleep(0.05)
	except:
		traceback.print_exc()
		pass
		
	# Relinquish vJoysticks
	for vid in vjoy_ids:
		if options.verbose:
			print('Relinquishing vJoystick:', vid)
		vjoy.RelinquishVJD(vid)
	
	# Close MIDI device
	if options.verbose:
		print('Closing MIDI device')
	midi.close()
		
def main():
	# parse arguments
	parser = OptionParser()
	parser.add_option("-t", "--test", dest="runtest", action="store_true",
					  help="To test the midi inputs")
	parser.add_option("-m", "--midi", dest="midi", action="store", type="int",
					  help="File holding the list of file to be checked")
	parser.add_option("-c", "--conf", dest="conf", action="store",
					  help="Configuration file for the translation")
	parser.add_option("-v", "--verbose",
						  action="store_true", dest="verbose")
	parser.add_option("-q", "--quiet",
						  action="store_false", dest="verbose")
	global options
	(options, args) = parser.parse_args()
	
	pygame.midi.init()
	
	if options.runtest:
		midi_test()
	else:
		joystick_run()
	
	pygame.midi.quit()

if __name__ == '__main__':
	main()
