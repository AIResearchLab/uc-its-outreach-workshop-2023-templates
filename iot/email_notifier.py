import smtplib
import ssl
import paho.mqtt.client as mqtt
import time


# GLOBALS
BROKER_HOSTNAME = "localhost"
BROKER_HOSTNAME = "robotics14.lan.robolab"
BROKER_HOSTNAME = "192.168.1.114"
SPEED_TOPIC = "spheroRVR/speed"
LED_BLINK_TOPIC = "spheroRVR/led/blink"
LED_GREEN_TOPIC = "spheroRVR/led/green"
MAXIMUM_SPEED_LIMIT = 0.4


def send_email():
    # Set up your Gmail account details
    sender_email = 'engrehsanamiri@gmail.com'
    receiver_email = 'engrehsanamiri@gmail.com'
    password = 'jlaezogdlhjnllwu'
    subject = 'Test email'
    body = 'This is a test email sent from Python.'
    msg = f'Subject: {subject}\n\n{body}'

    # Set up the email message
    message = """\
    Subject: Test email from Python

    This is a test email sent from Python."""

    # Create a secure SSL context
    context = ssl.create_default_context()

    try:
        # Log in to your Gmail account and create a secure connection
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(sender_email, password)

            # Send the email message
            server.sendmail(sender_email, receiver_email, msg)

        print('Email sent successfully.')
    except Exception as e:
        print('Error sending email: %s', e)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")

        global Connected  # Use global variable
        Connected = True  # Signal connection

    else:
        print(rc)
        print("Connection failed")


def on_message(client, userdata, message):
    print("speed message received! -> " + str(float(message.payload)))

    speed = float(message.payload)

    # check for speeding
    if speed > MAXIMUM_SPEED_LIMIT:
        print("SPEEDING DETECTED!")
        print("SENDING EMAIL INFRINGMENT NOTICE!")
        # send_email()


def main():
    """ This program listens to rover messages and notifies of traffic infringements using mqtt and email
    """

    # Set up the MQTT client
    client = mqtt.Client("remote")
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the MQTT broker
    client.connect(BROKER_HOSTNAME, 1883)
    client.loop_start()  # start the loop

    # subscribe to a message on a topic
    topic = SPEED_TOPIC
    client.subscribe(topic)

    try:
        while True:
            print("listening...")
            time.sleep(1)
            client.publish(LED_BLINK_TOPIC, "1")
            time.sleep(8)
            client.publish(LED_GREEN_TOPIC, "1")
            time.sleep(8)

    except KeyboardInterrupt:
        print("exiting")
        client.disconnect()
        client.loop_stop()


if __name__ == '__main__':
    main()
