#!/usr/bin/env python

import sys
import io
import os
import shutil
from subprocess import Popen, PIPE
from string import Template
from struct import Struct
from threading import Thread
from time import sleep, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from wsgiref.simple_server import make_server

import picamera
from ws4py.websocket import WebSocket
from ws4py.server.wsgirefserver import (
    WSGIServer,
    WebSocketWSGIHandler,
    WebSocketWSGIRequestHandler,
)
from ws4py.server.wsgiutils import WebSocketWSGIApplication

from pyroombaadapter import PyRoombaAdapter
import RPi.GPIO as GPIO
import numpy as np

###########################################
# PISTREAMING CONFIGURATION
WIDTH = 640
HEIGHT = 480
FRAMERATE = 24
HTTP_PORT = 8082
WS_PORT = 8084
COLOR = u'#444'
BGCOLOR = u'#333'
JSMPEG_MAGIC = b'jsmp'
JSMPEG_HEADER = Struct('>4sHH')
VFLIP = True
HFLIP = True

# ROOMBA CONFIGURATION
SERIAL_PORT = "/dev/ttyUSB0"
# The Open Interface isn't active until Roomba powers on ... so need alternate method of powering on.
# This GPIO is connected to the power button switch, and we can turn it on by setting it high for a short period and then releasing.
POWER_ON_PIN = 18 # Pi GPIO
POWER_ON_DURATION_SEC = 0.1
SPEED_INC_MS = 0.1
RATE_INC_DEGS = 5.0
MAX_SPEED_MS = 0.5
MIN_SPEED_MS = -0.5
MAX_RATE_DEGS = 50.0
MIN_RATE_DEGS = -50.0
###########################################

class PyRoomba(PyRoombaAdapter):
    def __init__(self,serial_port):
        self.roomba_speed = 0.0
        self.roomba_rate = 0.0
        self.cmd = ""
        super(PyRoomba, self).__init__(serial_port)

    def move_roomba(self):
        self.change_mode_to_full()
        if self.roomba_speed > MAX_SPEED_MS:
            self.roomba_speed = MAX_SPEED_MS
        if self.roomba_speed < MIN_SPEED_MS:
            self.roomba_speed = MIN_SPEED_MS
        if self.roomba_rate > MAX_RATE_DEGS:
            self.roomba_rate = MAX_RATE_DEGS
        if self.roomba_rate < MIN_RATE_DEGS:
            self.roomba_rate = MIN_RATE_DEGS
        print('Moving with speed %f m/s and rate %f deg/s' % (self.roomba_speed,self.roomba_rate))
        self.move(self.roomba_speed,np.deg2rad(self.roomba_rate))
   
    def command(self,cmd):
        self.cmd = cmd # for status string
        if cmd == "forward":
            self.roomba_speed = self.roomba_speed + SPEED_INC_MS
            self.move_roomba()

        if cmd == "back":
            self.roomba_speed = self.roomba_speed - SPEED_INC_MS
            self.move_roomba()

        if cmd == "left":
            self.roomba_rate = self.roomba_rate + RATE_INC_DEGS
            self.move_roomba()

        if cmd == "right":
            self.roomba_rate = self.roomba_rate - RATE_INC_DEGS
            self.move_roomba()

        if cmd == "halt":
            self.roomba_speed = 0.0
            self.roomba_rate = 0.0
            self.move_roomba()

        if cmd == "dock":
            self.start_seek_dock()
 
        if cmd == "power":
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(POWER_ON_PIN, GPIO.OUT)
            GPIO.output(POWER_ON_PIN, GPIO.HIGH)
            sleep(POWER_ON_DURATION_SEC)
            GPIO.output(POWER_ON_PIN, GPIO.LOW)

    def get_speed(self):
        return self.roomba_speed

    def get_rate(self):
        return self.roomba_rate
  
    def get_status_string(self):
        # return a string to be printed on camera overlay
        if self.cmd in ("halt","power","dock"):
            s = " %s " % self.cmd.capitalize()
        else:
            s = " %s (%g m/s, %g deg/s) " % (self.cmd.capitalize(), self.roomba_speed, self.roomba_rate)
        return s


def StreamingHttpHandlerFactory(camera,roomba):
    # A class factory, so we can pass the camera and roomba arguments to the HttpHandler
    # https://stackoverflow.com/questions/21631799/how-can-i-pass-parameters-to-a-requesthandler
    class StreamingHttpHandler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            if self.path == '/':
                self.send_response(301)
                self.send_header('Location', '/index.html')
                self.end_headers()
                return
            elif self.path == '/jsmpg.js':
                content_type = 'application/javascript'
                content = self.server.jsmpg_content
            elif self.path == '/index.html':
                content_type = 'text/html; charset=utf-8'
                tpl = Template(self.server.index_template)
                content = tpl.safe_substitute(dict(
                    WS_PORT=WS_PORT, WIDTH=WIDTH, HEIGHT=HEIGHT, COLOR=COLOR,
                    BGCOLOR=BGCOLOR))
            else:
                self.send_error(404, 'File not found')
                return
            content = content.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', len(content))
            self.send_header('Last-Modified', self.date_time_string(time()))
            self.end_headers()
            if self.command == 'GET':
                self.wfile.write(content)

        def do_POST(self):
            print("Got a POST")
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            self.send_response(204)
            self.end_headers()
            print(body)

            if "forward" in str(body):
                roomba.command("forward");
                camera.annotate_text = roomba.get_status_string()
                
            if "back" in str(body):
                roomba.command("back");
                camera.annotate_text = roomba.get_status_string()
                
            if "left" in str(body):
                roomba.command("left");
                camera.annotate_text = roomba.get_status_string()
                
            if "right" in str(body):
                roomba.command("right");
                camera.annotate_text = roomba.get_status_string()

            if "halt" in str(body):
                roomba.command("halt");
                camera.annotate_text = roomba.get_status_string()
                
            if "dock" in str(body):
                roomba.command("dock");
                camera.annotate_text = roomba.get_status_string()
                
            if "power" in str(body):
                roomba.command("power");
                camera.annotate_text = roomba.get_status_string()

    
    return StreamingHttpHandler

class StreamingHttpServer(HTTPServer):
    def __init__(self, camera, roomba):
        super(StreamingHttpServer, self).__init__(
                ('', HTTP_PORT), StreamingHttpHandlerFactory(camera,roomba))
        with io.open('index.html', 'r') as f:
            self.index_template = f.read()
        with io.open('jsmpg.js', 'r') as f:
            self.jsmpg_content = f.read()

        camera.annotate_foreground = picamera.Color('black')
        camera.annotate_background = picamera.Color('white')
        camera.annotate_text_size = 32
        camera.annotate_text = "Welcome to Roomba Cam" 

class StreamingWebSocket(WebSocket):
    def opened(self):
        self.send(JSMPEG_HEADER.pack(JSMPEG_MAGIC, WIDTH, HEIGHT), binary=True)


class BroadcastOutput(object):
    def __init__(self, camera):
        print('Spawning background conversion process')
        self.converter = Popen([
            'ffmpeg',
            '-f', 'rawvideo',
            '-pix_fmt', 'yuv420p',
            '-s', '%dx%d' % camera.resolution,
            '-r', str(float(camera.framerate)),
            '-i', '-',
            '-f', 'mpeg1video',
            '-b', '800k',
            '-r', str(float(camera.framerate)),
            '-'],
            stdin=PIPE, stdout=PIPE, stderr=io.open(os.devnull, 'wb'),
            shell=False, close_fds=True)

    def write(self, b):
        self.converter.stdin.write(b)

    def flush(self):
        print('Waiting for background conversion process to exit')
        self.converter.stdin.close()
        self.converter.wait()


class BroadcastThread(Thread):
    def __init__(self, converter, websocket_server):
        super(BroadcastThread, self).__init__()
        self.converter = converter
        self.websocket_server = websocket_server

    def run(self):
        try:
            while True:
                buf = self.converter.stdout.read1(32768)
                if buf:
                    self.websocket_server.manager.broadcast(buf, binary=True)
                elif self.converter.poll() is not None:
                    break
        finally:
            self.converter.stdout.close()


def main():
    ### Establish connection to Roomba
    roomba = PyRoomba(SERIAL_PORT)

    print('Initializing camera')
    with picamera.PiCamera() as camera:
        camera.resolution = (WIDTH, HEIGHT)
        camera.framerate = FRAMERATE
        camera.vflip = VFLIP # flips image rightside up, as needed
        camera.hflip = HFLIP # flips image left-right, as needed
        sleep(1) # camera warm-up time
        print('Initializing websockets server on port %d' % WS_PORT)
        WebSocketWSGIHandler.http_version = '1.1'
        websocket_server = make_server(
            '', WS_PORT,
            server_class=WSGIServer,
            handler_class=WebSocketWSGIRequestHandler,
            app=WebSocketWSGIApplication(handler_cls=StreamingWebSocket))
        websocket_server.initialize_websockets_manager()
        websocket_thread = Thread(target=websocket_server.serve_forever)
        print('Initializing HTTP server on port %d' % HTTP_PORT)
        http_server = StreamingHttpServer(camera,roomba)
        http_thread = Thread(target=http_server.serve_forever)
        print('Initializing broadcast thread')
        output = BroadcastOutput(camera)
        broadcast_thread = BroadcastThread(output.converter, websocket_server)
        print('Starting recording')
        camera.start_recording(output, 'yuv')
        try:
            print('Starting websockets thread')
            websocket_thread.start()
            print('Starting HTTP server thread')
            http_thread.start()
            print('Starting broadcast thread')
            broadcast_thread.start()
            while True:
                camera.wait_recording(1)
        except KeyboardInterrupt:
            pass
        finally:
            print('Stopping recording')
            camera.stop_recording()
            print('Waiting for broadcast thread to finish')
            broadcast_thread.join()
            print('Shutting down HTTP server')
            http_server.shutdown()
            print('Shutting down websockets server')
            websocket_server.shutdown()
            print('Waiting for HTTP server thread to finish')
            http_thread.join()
            print('Waiting for websockets thread to finish')
            websocket_thread.join()


if __name__ == '__main__':
    main()
