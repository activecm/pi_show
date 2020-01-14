#!/usr/bin/env python3
"""Show text or graphics on a display connected to a Raspberry Pi.
This current version only supports the PiOled (ssd1306 chip on the I2C bus),
with a fallback to using xwindows apps xmessage and feh to display text and
images, respectively."""

# Based on ssd1306_bro_stats, original authors: Tony DiCola & James DeVito
# Copyright (c) 2017 Adafruit Industries
# References:
# https://learn.adafruit.com/adafruit-pioled-128x32-mini-oled-for-raspberry-pi/usage
# https://learn.adafruit.com/pages/15678/elements/3024322/download

# Copyright 2019 
# pi_show author: William Stearns <william.l.stearns@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# This example is for use on (Linux) computers that are using CPython with
# Adafruit Blinka to support CircuitPython libraries. CircuitPython does
# not support PIL/pillow (python imaging library)!

#xmessage: debian/ubuntu package: x11-utils , rpm package: xorg-x11-apps, mac ports package: xmessage
#feh: (all) package: feh


import os
import sys
import time
import subprocess


try:
	from board import SCL, SDA
except ImportError:
	sys.stderr.write('Unable to load board module; have you run "sudo pip3 install Adafruit-Blinka" ?\n')
	#sys.exit(1)

try:
	import busio
except ImportError:
	sys.stderr.write('Unable to load busio module; have you run "sudo pip3 install Adafruit-Blinka" ?\n')
	#sys.exit(1)

try:
	from PIL import Image, ImageDraw, ImageFont
except ImportError:
	sys.stderr.write('Unable to load PIL module; have you run "sudo apt-get install python3-pil" ?\n')
	#sys.exit(1)

#Move into board detect function
try:
	import adafruit_ssd1306
except ImportError:
	sys.stderr.write('Unable to load adafruit_ssd1306 module; have you run "sudo pip3 install adafruit-circuitpython-ssd1306" ?\n')
	#sys.exit(1)



def warn(warn_message):
	"""On a non-fatal error, notify user."""

	sys.stderr.write(warn_message + '\n')


def debug(debug_message):
	"""On a non-fatal error, notify user."""

	if cl_args['debug']:
		sys.stderr.write(debug_message + '\n')



def fail(fail_message):
	"""On a fatal error, notify user and exit."""

	sys.stderr.write(fail_message + ' Exiting.\n')
	sys.exit(1)



def cmd_output(cmd_to_run):
	"""Get the stdout from a command run from bash."""

	return subprocess.check_output(cmd_to_run, shell=True).decode("utf-8")


def load_drawing_h(ld_width, ld_height):
	"""Initializes the display and Returns the handles needed to access the display.  Only called once at the beginning."""

	disp_h = None
	image_h = None
	draw_h = None

	if 'busio' in sys.modules and 'board' in sys.modules and 'adafruit_ssd1306' in sys.modules:
		# Create the I2C interface.
		i2c = busio.I2C(SCL, SDA)

		# Create the SSD1306 OLED class.
		# The first two parameters are the pixel width and pixel height.  Change these
		# to the right size for your display!
		disp_h = adafruit_ssd1306.SSD1306_I2C(ld_width, ld_height, i2c)

		# Clear display.
		disp_h.fill(0)
		disp_h.show()

	if 'PIL' in sys.modules:
		# Create blank image for drawing.
		# Make sure to create image with mode '1' for 1-bit color.
		image_h = Image.new('1', (ld_width, ld_height))

		# Get drawing object to draw on image.
		draw_h = ImageDraw.Draw(image_h)

		# Draw a black filled box to clear the image.
		draw_h.rectangle((0, 0, ld_width, ld_height), outline=0, fill=0)

	return disp_h, image_h, draw_h



def load_font_h(font_file):
	"""Load a specific font and return the handle.  If no font is specified (None), try to load DejaVuSans
	and if that fails, load the default font."""

	font_h = None

	if 'PIL' in sys.modules:
		if font_file and os.path.exists(font_file):
			# Some other nice fonts to try: http://www.dafont.com/bitmap.php
			#Example: '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
			font_h = ImageFont.truetype(font_file, 9)
		else:
			if os.path.exists('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
				#Seriously nicer font than the default for this small display.
				font_h = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)
			else:
				# Load default font.
				font_h = ImageFont.load_default()

	return font_h



def send_text(display_module_name, disp_h, image_h, draw_h, font_h, text_l, max_lines, max_chars, pad_pixels, display_time):
	"""Pushes the line(s) of text in the text_l list to the handles provided.
	At most max_lines of text, and at most max_chars per line, are shown."""

	if display_module_name == 'xwindows' and xmessage_installed:
		xmessage_proc = subprocess.Popen(['xmessage', "\n".join(text_l)])
		time.sleep(display_time)
		xmessage_proc.terminate()
	else:
		# Draw a black filled box to clear the image.
		draw_h.rectangle((0, 0, disp_h.width, disp_h.height), outline=0, fill=0)

		for line_count in range(0, min(max_lines, len(text_l))):
			draw_h.text((0, pad_pixels + 8 * line_count), text_l[line_count][0:max_chars], font=font_h, fill=255)

		disp_h.image(image_h)
		disp_h.show()

		try:
			time.sleep(display_time)
		except KeyboardInterrupt:
			sys.exit(0)



def send_image(display_module_name, disp_h, image_file, display_time):
	"""Draws the image on the screen.  image_file must be a full path to the file."""

	if os.path.exists(image_file):
		if display_module_name == 'xwindows' and feh_installed:
			feh_proc = subprocess.Popen(['feh', image_file])
			time.sleep(display_time)
			feh_proc.terminate()
		else:
			image_h = Image.open(image_file).convert('1')
			try:
				disp_h.image(image_h)
			except ValueError:
				#Could be that the supplied image has not been converted correctly, so we'll force a conversion
				warn(image_file + ' is not in ' + str(disp_h.width) + 'x' + str(disp_h.height) + 'x1 format, converting.')
				image_h = Image.open(image_file).resize((disp_h.width, disp_h.height), Image.ANTIALIAS).convert('1')
				disp_h.image(image_h)
			disp_h.show()

			try:
				time.sleep(display_time)
			except KeyboardInterrupt:
				sys.exit(0)
	else:
		warn(image_file + " unreadable, skipping.")


def sorted_dir_list(requested_start_object):
	"""Returns a sorted list of files (and only files) in a directory, with the directory name prepended.  Not recursive.
	If the requested object is a file, return that."""

	justfile_list = []

	if os.path.isfile(requested_start_object):
		justfile_list.append(requested_start_object)
	elif os.path.isdir(requested_start_object):
		for one_obj in os.listdir(requested_start_object):
			if os.path.isfile(requested_start_object + '/' + one_obj):
				justfile_list.append(requested_start_object + '/' + one_obj)

	justfile_list.sort()

	return justfile_list


def locate_display():
	"""Detect the display and return its modules name and dimensions."""
	#FIXME - add param for forced display

	detected_display = None
	x_pixels = 0
	y_pixels = 0


	#i2c appears to be enabled, check for i2c displays
	if os.path.exists('/dev/i2c-1') and os.path.exists('/usr/sbin/i2cdetect') and cmd_output('i2cdetect -y 1 60 60 | grep "^30:.*3c"'):
		detected_display = 'ssd1306'
		x_pixels = 128
		y_pixels = 32			#Are there other boards with id 0x3c with 64 pixels?
		#else:
		#	fail('ssd1306 not detected on i2c bus.  Is the PiOled plugged in on the pins closest to the corner on the 40 pin interface?')

	elif 'DISPLAY' in os.environ and (feh_installed or xmessage_installed):
		detected_display = 'xwindows'
		x_pixels = 1024
		y_pixels = 768

	else:
		#FIXME - add reformatted text for what the user needs to do to enable some display
		fail("/dev/i2c-1 does not exist.  If you are using an I2C display, please run raspi-config, go to Interfacing options or Advanced, enable I2C, reboot, and rerun this script.")
		#fail("/usr/sbin/i2cdetect does not exist.  Please install i2c-tools with 'sudo apt-get install i2c-tools' .")

	return detected_display, x_pixels, y_pixels



pi_show_version = '0.3.5'
default_show_dir = '/var/toshow/'
default_delay = '8'

xmessage_installed = os.path.exists('/opt/X11/bin/xmessage') or os.path.exists('/bin/xmessage') or os.path.exists('/usr/bin/xmessage')
feh_installed = os.path.exists('/usr/bin/feh') or os.path.exists('/bin/feh') or os.path.exists('/opt/local/bin/feh')



if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description='pi_show version ' + str(pi_show_version))
	parser.add_argument('-w', '--wait', help='Time to show a screen before moving to the next (default: ' + str(default_delay) + ' ).', required=False, default=default_delay)
	parser.add_argument('-d', '--directory', help='Directory that holds text files/images to be shown (default: ' + str(default_show_dir) + ' ).', required=False, default=default_show_dir)
	parser.add_argument('-o', '--once', help='Show each requested object once, then exit (default: continuous loop)', required=False, default=False, action='store_true')
	parser.add_argument('-s', '--stdin', help='Show text handed on stdin (lines are only read a single time)', required=False, default=False, action='store_true')
	parser.add_argument('-f', '--font', help='Full path to truetype font file (default: DejaVuSans)', required=False, default=None)
	parser.add_argument('--debug', help='Show additional debugging information on stderr', required=False, default=False, action='store_true')
	cl_args = vars(parser.parse_args())

	nap_time = int(cl_args['wait'])

	show_dir = str(cl_args['directory'])

	(display_module, x_size, y_size) = locate_display()

	(disp, image, draw) = load_drawing_h(x_size, y_size)

	if cl_args['font'] and not os.path.exists(cl_args['font']):
		fail('No such font file')

	font = load_font_h(cl_args['font'])

	padding = -2
	#top = padding
	#bottom = disp.height - padding
	# Move left to right keeping track of the current x position for drawing shapes.

	while True:
		if cl_args['stdin']:
			#debug('Reading from stdin')
			lines = sys.stdin.readlines()
			lines = [x.strip() for x in lines]
			#debug('About to show: ' + '__'.join(lines))
			send_text(display_module, disp, image, draw, font, lines, y_size//8, x_size//6, padding, nap_time)

		for full_file in sorted_dir_list(show_dir):
			if os.path.exists(full_file):						#File may have been deleted since the directory listing was taken, ignore if so.
				if full_file.lower().endswith(('.txt')):
					with open(full_file) as f:
						lines = f.readlines()
					lines = [x.strip() for x in lines]
					send_text(display_module, disp, image, draw, font, lines, y_size//8, x_size//6, padding, nap_time)
				else:
					send_image(display_module, disp, full_file, nap_time)

		if cl_args['once']:
			sys.exit(0)
