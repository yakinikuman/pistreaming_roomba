# Pi Video Streaming and Roomba Control

Combines a Raspberry Pi with Pi Camera and a Roomba.

Drive your Roomba around with any web browser, while streaming video

A mashup of https://github.com/waveform80/pistreaming and https://github.com/AtsushiSakai/PyRoombaAdapter.

## Hardware
Raspberry Pi with a female USB-A port (eg. not a Zero or Zero W)

Raspberry Pi Camera

Roomba which supports the iRobot Open Interface

USB-TTL dongle

7-pin mini-din plug

5V voltage regulator

Micro USB male connector

JST-PH female-male pair (or similar)

Some spare wire (28 - 24 AWG or so)

Solder and soldering iron


More in-depth tutorial coming soon...


## Software Prereqs

The software has been testing on a Raspberry Pi B+ running Raspbian Buster (headless, but that shouldn't matter).

First make sure you've got a functioning Pi camera module (test it with
`raspistill` to be certain). Then make sure you've got the following packages
installed:

    $ sudo apt-get install ffmpeg git python3-picamera

PyRoombaAdapter:

    $ pip3 install pyroombaadapter ws4py


## Usage

Run the Python server script which should print out a load of stuff
to the console as it starts up:

    $ cd pistreaming_roomba
    $ python3 server.py
    Initializing websockets server on port 8084
    Initializing HTTP server on port 8082
    Initializing camera
    Initializing broadcast thread
    Spawning background conversion process
    Starting websockets thread
    Starting HTTP server thread
    Starting broadcast thread

Now fire up your favourite web-browser and visit the address
`http://pi-address:8082/` - it should fairly quickly start displaying the feed
from the camera. 

Use the buttons below the video feed to control the Roomba.

Power - power on Roomba (if you manually press the Roomba's power button, you don't need this)

Forward/Back - increase/decrease Roomba's forward speed

Left/Right - increase/decrease Roomba's spin rate

Halt - set Roomba's speed and spin rate to 0

Dock - put Roomba in docking mode

