
from pyroombaadapter import PyRoombaAdapter
import time
import RPi.GPIO as GPIO

SERIAL_PORT = "/dev/ttyUSB0"

def get_response(adapter, packet_id, expected_bytes, signed=False):
    adapter.serial_con.write(bytes([adapter.CMD["Sensors"],packet_id]))
    time.sleep(0.3)
    response_bytes = adapter.serial_con.in_waiting
    if response_bytes == expected_bytes:
        response_raw = adapter.serial_con.read(expected_bytes)
        response = int.from_bytes(response_raw,byteorder='big',signed=signed)
        return response
    else:
        print('Error ... expected %d bytes but received %d\n' % (expected_bytes,response_bytes))
        quit()

# The Open Interface isn't active until Roomba powers on ... so need alternate method of powering on.
# This GPIO is connected to the power button switch, and we can turn it on by setting it high for a short period and then releasing.
power_on_pin = 18 # Pi GPIO
power_on_duration_sec = 0.1

### Command line args
import argparse
parser = argparse.ArgumentParser(description='Send simple commands to roomba')
parser.add_argument('command', help='Command to issue.  "Clean", "Stop", "Dock", "Off", "On", "Battery"')
args = parser.parse_args()
cmd = args.command.lower()

### Turn on roomba if "on" cmd
if cmd == "on":
    print("Powering on Roomba...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(power_on_pin, GPIO.OUT)
    GPIO.output(power_on_pin, GPIO.HIGH)
    time.sleep(power_on_duration_sec)
    GPIO.output(power_on_pin, GPIO.LOW)
    print("Roomba should be powered on")
    exit()

### Establish connection
adapter = PyRoombaAdapter(SERIAL_PORT)

print ("Command: %s" % cmd)

if cmd == "clean":
    adapter.start_cleaning()
elif cmd == "off":
    #can't be started again without physical button push
    adapter.turn_off_power()
elif cmd == "stop":
    adapter.change_mode_to_passive()
elif cmd == "bclean":
    #functions same as "clean"
    adapter.send_buttons_cmd(clean=True)
elif cmd == "dock":
    adapter.start_seek_dock()   
elif cmd == "battery":
    # Current battery charge percent
    battery_current_mah = get_response(adapter,25,2)
    battery_max_mah = get_response(adapter,26,2)
    print('Charge: %0.1f%% of max %g mAh\n' % (100.0*battery_current_mah/battery_max_mah, battery_max_mah))

    # Open Interface spec: sensor 22 returns 2 bytes containing batt voltage in mV
    response_mv = get_response(adapter,22,2)
    print('Batt voltage: %g V\n' % (response_mv/1000))

    # Current flow
    response_ma = get_response(adapter,23,2,signed=True)
    print('Batt current: %g mA\n' % (response_ma))

    # Charging State
    response_enum = get_response(adapter,21,1)
    response_code = {0: "Not charging",
	             1: "Reconditioning Charging",
		     2: "Full Charging",
		     3: "Trickle Charging",
		     4: "Waiting",
		     5: "Charging Fault Condition"}
    print('Charging state: %s\n' % response_code[response_enum])
else:
    print('Unknown command!\n')

