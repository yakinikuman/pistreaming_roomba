# Pi Video Streaming and Roomba Control

Combines a Raspberry Pi with Pi Camera and a Roomba.

Drive your Roomba around with any web browser, while streaming video

A mashup of https://github.com/waveform80/pistreaming and https://github.com/AtsushiSakai/PyRoombaAdapter.

## Hardware and Project Description
See more in-depth writeup, with pictures, at https://yakinikuman.github.io/pistreaming_roomba.


## Software Prereqs

The software has been tested on a Raspberry Pi B+ running Raspbian Buster (headless, but that shouldn't matter).

First make sure you've got a functioning Pi camera module (test it with
`raspistill` to be certain). Then make sure you've got the following packages
installed:

    $ sudo apt-get install ffmpeg git python3-picamera

PyRoombaAdapter:

    $ pip3 install pyroombaadapter ws4py


## Usage

Clone pistreaming_roomba project to Pi.  Run the Python server script which should print out a load of stuff
to the console as it starts up:

    $ cd pistreaming_roomba
    $ python3 server.py
    Serial port is open, presumably to a roomba...
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

Forward/Back - increase/decrease Roomba's forward speed

Left/Right - increase/decrease Roomba's spin rate

Halt - set Roomba's speed and spin rate to 0

Dock - put Roomba in docking mode

Power - triggers remote Roomba power on. This requires a Roomba hardware modification, see https://yakinikuman.github.io/pistreaming_roomba.  Note that this isn't needed if you manually power on Roomba.

