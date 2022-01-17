# midi2vjoy

## 1. Introduction

midi2vjoy evolution is based on midi2vjoy by c0redumb from 2017 https://github.com/c0redumb/midi2vjoy 
As per the original python code from c0redumb, the midi2vjoy python code is licensed under the GNU General Public License 2.0.

This software provides a way to use MIDI controllers to provide data for **vJoy joysticks on Windows**, by mapping MIDI inputs to virtual joystick controls.
These virtual joystick devices created using vJoy can then be mapped to controls in games and simulators as if they were real game controllers.

The largest change from the original midi2vjoy by c0redumb is the decoupling of MIDI status bytes from MIDI control type classification, as this did not work on most MIDI controllers I tested. For this reason, a modified configuration file format is used, with manual classification of the desired control type. The current options are 'B' for Button, 'A' for Axis and 'R' for rotary encoders treated as two directional buttons.
The midi2vjoy-evolution fork currently supports any midi inputs but relies on the user to select the correct control type.

Note: if you're not familiar with command-line interfaces and writing configuration files, you may have difficulties using this software.

## 2. How to use the software

### 2.1. Setup

1. Download and install **vJoy** from https://github.com/shauleiz/vJoy/releases
2. Use the vJoyConf tool ("vJoy" ->"Configure vJoy") to define the virtual joysticks, [see details in 2.2](#22-configure-vjoy).
3. Install python 3.6 or later
4. Install pygame for midi support e.g. by executing the command line `pip install pygame`
4. Run `python midi2vjoy.py -t` to figure out the MIDI control outputs to include in your configuration file. [see details in 2.3](#23-test-midi-device).
5. Write/edit the mapping configuration file, [see details in 2.4](#24-edit-mapping-configuration-file).
6. Run `midi2vjoy.py -m <midi device id> -c <path to configuration file>`, where midi is the midi device and conf is the configuration file. If your vJoy installation is portable or otherwise nonstandard, you can specify the path to the vjoyinterface.dll file using the `--dll` option. This may be necessary when the vJoy installer freezes at the end of installation and doesn't create the correct windows registry entries for DLL autodiscovery.

### 2.2. Configure vJoy

Start the Windows application "Configure vJoy" (joyconf.exe) and add a virtual joystick device. Assign a number of buttons sufficient for your use. For simple press buttons, one joystick button is sufficient. For each rotary encoder, two buttons are needed.
There is a limited number of joystick axes supported by vJoy, so for each additional 8 axes you will need to create a new virtual joystick. After making changes to the virtual joystick device, you are likely to have to reboot windows for the changes to be reflected.

### 2.3. Test MIDI device

To test the MIDI device, just run `python midi2vjoy.py -t`. First the program will print out a list of available MIDI input devices for you to choose. You will need to select the MIDI you want to use. If you only have one MIDI device connected, the device ID is likely to be `1`.

When the device is opened, you can turn knobs, slide sliders, rotate encoders and press buttons on the MIDI controller. The MIDI codes that are sent by the MIDI device will be displayed on the screen. Just write down the first number representing the "MIDI status byte" (usually 176 for axis and 144 for buttons), and the second number "MIDI data1 byte" representing the specific button/slider etc. The third number is the actual MIDI control readout that depends on the type of the control – you probably don't need to care about this last number.

### 2.4. Edit mapping configuration file

The mapping configuration file is a simple text file with each line representing how midi2vjoy should interpret MIDI inputs into vJoy outputs.
Using the Test MIDI device instructions above, make note of all the MIDI controls you want to use and start writing them down into a text file. You can name it "mappings.conf" for example. All lines starts with "#" are comments and will be ignored by the parser.

For each axis/button/slider etc, make a new line in the text file. Structure the lines as such:
<control type>		<MIDI status number>		<MIDI data1 number>		<vJoy number>		<Joystick axis/button mapping>

As an example:
```
# Type		Status		Data1		vJoy	Mapping
A			176			6			1		X
```
will assign MIDI control 176:6 to vJoystick number 1, interpret it as an Axis and assign it to joystick axis 'X'. 

Respectively:
```
# Type		Status		Data1		vJoy	Mapping
B			154			2			1		2
```
will assign MIDI control 154:2 to vJoystick number 1, interpret it as a Button and assign it to joystick button 2.

The special case for configuration lines is the case of the Rotary encoder that can spin freely in two directions and has no stops or position information. These require a two-button mapping, one for each direction.
```
# Type		Status		Data1		vJoy	Mapping
R			177			2			1		8,9
```
will assign MIDI control 177:2 to vJoystick number 1, interpret it as a Rotary encoder and assign the up direction to button 8, and the down direction to button 9

### 2.5 Running midi2vjoy-evolution

Once you have the configuration file, your typical command to run midi2joy will be 

`python midi2vjoy.py --midi 1 --conf mapping.conf`.

In case midi2vjoy complains about pygame, make sure your Python installation is working correctly.
In case midi2vjoy complains about the vJoy interface, please pass the absolute path to the vjoyinterface.dll file using `--dll <path-to-DLL>`.
For debugging your configuration file and the controls, use --verbose
