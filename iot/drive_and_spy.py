
import time
import asyncio
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from sphero_sdk import SpheroRvrAsync
from sphero_sdk import SerialAsyncDal
from sphero_sdk import RvrStreamingServices
from sphero_sdk import RvrLedGroups
from sphero_sdk import Colors
from helper_keyboard_input import KeyboardHelper


# Define the MQTT topic and broker details
BROKER_HOSTNAME = "localhost"
LED_BLINK_TOPIC = "spheroRVR/led/blink"
LED_GREEN_TOPIC = "spheroRVR/led/green"
topic = "spheroRVR/speed"
hostname = BROKER_HOSTNAME
port = 1883

client = mqtt.Client("rover")

global blink_enabled
blink_enabled = 0
global green_enabled
green_enabled = 0


class ExitException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def speed_handler(speed_data):
    # Read the speed data from the Sphero RVR
    # print('speed data response: ', speed_data)
    speed = speed_data['Speed']['Speed']

    # Publish the speed data to the Mosquitto broker
    # client.publish(topic, speed)
    publish.single(topic, speed, hostname=hostname,
                   port=port, client_id="rover_speed_pub")
    print("published speed data: {}".format(speed))


# initialize global variables
key_helper = KeyboardHelper()
current_key_code = -1
driving_keys = [119, 97, 115, 100, 32]
speed = 0
heading = 0
flags = 0

loop = asyncio.get_event_loop()
rvr = SpheroRvrAsync(
    dal=SerialAsyncDal(
        loop
    )
)


def keycode_callback(keycode):
    global current_key_code
    current_key_code = keycode
    print("Key code updated: ", str(current_key_code))


async def blink_leds():
    for i in range(0, 6):
        # headlight leds on
        await rvr.set_all_leds(
            led_group=RvrLedGroups.headlight_left.value,
            led_brightness_values=[255, 124, 0]
        )
        await rvr.set_all_leds(
            led_group=RvrLedGroups.headlight_right.value,
            led_brightness_values=[255, 124, 0]
        )

        await asyncio.sleep(0.2)

        # headlight leds off
        await rvr.set_all_leds(
            led_group=RvrLedGroups.headlight_right.value,
            led_brightness_values=[0, 0, 0]
        )
        await rvr.set_all_leds(
            led_group=RvrLedGroups.headlight_left.value,
            led_brightness_values=[0, 0, 0]
        )

        await asyncio.sleep(0.2)


async def control_loop():
    """
    Runs the main control loop for this demo.  Uses the KeyboardHelper class to read a keypress from the terminal.
    W - Go forward.  Press multiple times to increase speed.
    A - Decrease heading by -10 degrees with each key press.
    S - Go reverse. Press multiple times to increase speed.
    D - Increase heading by +10 degrees with each key press.
    Spacebar - Reset speed and flags to 0. RVR will coast to a stop
    """
    global current_key_code
    global speed
    global heading
    global flags

    try:
        print("waking rvr")
        await rvr.wake()
        print("rvr connected")

        # Give RVR time to wake up
        await asyncio.sleep(2)

        # lights off
        await rvr.set_all_leds(
            led_group=RvrLedGroups.all_lights.value,
            led_brightness_values=[color for _ in range(
                10) for color in Colors.off.value]
        )

        # lights blinking
        print("blink LEDS")
        await blink_leds()

        # set up sensor callback
        await rvr.sensor_control.add_sensor_data_handler(
            service=RvrStreamingServices.speed,
            handler=speed_handler
        )

        await rvr.sensor_control.start(interval=250)

        await rvr.reset_yaw()

        # lights green
        await rvr.set_all_leds(
            led_group=RvrLedGroups.headlight_left.value,
            led_brightness_values=[0, 255, 0]
        )
        await rvr.set_all_leds(
            led_group=RvrLedGroups.headlight_right.value,
            led_brightness_values=[0, 255, 0]
        )

        # key board loop
        while True:

            global blink_enabled
            if blink_enabled:
                # blink LEDS
                print("blink leds command activated!")
                await blink_leds()
                blink_enabled = 0
                print("blink leds command done!")

            global green_enabled
            if green_enabled:
                # green LEDS
                print("green leds command activated!")

                await rvr.set_all_leds(
                    led_group=RvrLedGroups.headlight_left.value,
                    led_brightness_values=[0, 255, 0]
                )
                await rvr.set_all_leds(
                    led_group=RvrLedGroups.headlight_right.value,
                    led_brightness_values=[0, 255, 0]
                )

                green_enabled = 0

                print("green leds command done!")

            if current_key_code == 119:  # W
                # if previously going reverse, reset speed back to 64
                if flags == 1:
                    speed = 64
                else:
                    # else increase speed
                    speed += 64
                # go forward
                flags = 0
            elif current_key_code == 97:  # A
                heading -= 10
            elif current_key_code == 115:  # S
                # if previously going forward, reset speed back to 64
                if flags == 0:
                    speed = 64
                else:
                    # else increase speed
                    speed += 64
                # go reverse
                flags = 1
            elif current_key_code == 100:  # D
                heading += 10
            elif current_key_code == 32:  # SPACE
                # reset speed and flags, but don't modify heading.
                speed = 0
                flags = 0

            # check the speed value, and wrap as necessary.
            if speed > 255:
                speed = 255
            elif speed < -255:
                speed = -255

            # check the heading value, and wrap as necessary.
            if heading > 359:
                heading = heading - 359
            elif heading < 0:
                heading = 359 + heading

            # reset the key code every loop
            current_key_code = -1

            # issue the driving command
            await rvr.drive_with_heading(speed, heading, flags)

            # sleep the infinite loop for a 10th of a second to avoid flooding the serial port.
            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        print('\nProgram terminated with keyboard interrupt.')

        await rvr.sensor_control.clear()

        # Delay to allow RVR issue command before closing
        await asyncio.sleep(0.5)

        # rvr.close()
        raise ExitException("exitting")
        # return


def run_loop():
    global loop
    global key_helper

    key_helper.set_callback(keycode_callback)
    loop.run_until_complete(
        asyncio.gather(
            control_loop()
        )
    )


# mqtt stuff
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")

        global Connected  # Use global variable
        Connected = True  # Signal connection

    else:
        print("Connection failed")


def on_message(client, userdata, message):
    print("mqtt message received! -> " + str(message.payload))

    # if blink message
    if message.topic == LED_BLINK_TOPIC:
        print("blinking leds")
        global blink_enabled
        blink_enabled = 1

    elif message.topic == LED_GREEN_TOPIC:
        print("setting green leds")
        global green_enabled
        green_enabled = 1


def main():
    """ This program drives the rover and streams data to mqtt
    """

    # Set up the MQTT client
    client = mqtt.Client("rover_sub")
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the MQTT broker
    client.connect(BROKER_HOSTNAME, 1883)
    client.loop_start()  # start the loop

    # subscribe to topics
    client.subscribe(LED_BLINK_TOPIC)
    client.subscribe(LED_GREEN_TOPIC)

    loop.run_in_executor(None, key_helper.get_key_continuous)

    try:
        print("starting control loop")
        run_loop()

    except ExitException as e:
        print("exit")
        key_helper.end_get_key_continuous()

    finally:
        loop.run_until_complete(
            asyncio.gather(
                rvr.close()
            )
        )

        # stop mqtt
        client.disconnect()
        client.loop_stop()

        print("any key to exit")
        exit()


if __name__ == '__main__':
    print("starting main")
    print("---------------")
    print("Runs the main control loop for this demo.  Uses the KeyboardHelper class to read a keypress from the terminal.")
    print("W - Go forward.  Press multiple times to increase speed.")
    print("A - Decrease heading by -10 degrees with each key press.")
    print("S - Go reverse. Press multiple times to increase speed.")
    print("D - Increase heading by +10 degrees with each key press.")
    print("Spacebar - Reset speed and flags to 0. RVR will coast to a stop")
    print("")

    main()
