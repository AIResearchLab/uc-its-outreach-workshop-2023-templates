import os
import time
import smtplib
import ssl

class EmailHelper(object):
    def __init__(self) -> None:
        # get env variables
        # Set up your Gmail account details
        self.sender_email = 'engrehsanamiri@gmail.com'
        self.receiver_email = 'engrehsanamiri@gmail.com'
        self.password = 'jlaezogdlhjnllwu'
        self.subject = 'email subject'
        self.body = "email body"

    def send_email(self):
        # Set up the email message
        msg = f'Subject: {self.subject}\n\n{self.body}'

        print(msg)
        return

        # Create a secure SSL context
        context = ssl.create_default_context()

        try:
            # Log in to your Gmail account and create a secure connection
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
                server.login(self.sender_email, self.password)

                # Send the email message
                server.sendmail(self.sender_email, self.receiver_email, msg)

            print('Email sent successfully.')
        except Exception as e:
            print('Error sending email: %s', e)


class IngringementHelper(EmailHelper):
    def __init__(self, speed_limit: float) -> None:
        super().__init__()

        self.speed_limit = speed_limit
        self.ingringement_max_speed = 0.0
        self.infringement_start = 0.0
        self.infringement_duration = 0.0
        self.infringement_started = False
        self.infringement_complete = False

    def start_tracking_infringement(self):
        self.infringement_started = True
        self.infringement_start = time.time()

    def track_infringement(self, current_speed: float):
        if current_speed > self.speed_limit and not self.infringement_started:
            print("SPEEDING DETECTED!")
            self.start_tracking_infringement()

        if current_speed < self.speed_limit:
            self.infringement_started = False
            self.infringement_complete = True

        if self.infringement_started and not self.infringement_complete:
            self.infringement_duration = time.time() - self.infringement_start
            self.ingringement_max_speed = max(self.ingringement_max_speed, current_speed)

    def speeding_event_finished(self):
        return self.infringement_complete

    def send_infringement_notice(self, notice_text: str):
        print("SENDING EMAIL INFRINGMENT NOTICE!")
        self.body = notice_text
        self.body += f"\n\nNotice details:\n\nMaximum Speed (m/s): {self.ingringement_max_speed}\nDuration (s):{self.infringement_duration}\n"
        self.send_email()
