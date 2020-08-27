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
from the camera. You should be able to visit the URL from multiple browsers
simultaneously (although obviously you'll saturate the Pi's bandwidth sooner or
later).

If you find the video stutters or the latency is particularly bad (more than a
second), please check you have a decent network connection between the Pi and
the clients. I've found ethernet works perfectly (even with things like
powerline boxes in between) but a poor wifi connection doesn't provide enough
bandwidth, and dropped packets are not handled terribly well.

To shut down the server press Ctrl+C - you may find it'll take a while
to shut down unless you close the client web browsers (Chrome in particular
tends to keep connections open which will prevent the server from shutting down
until the socket closes).

