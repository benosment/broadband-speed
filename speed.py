#! /usr/bin/env python3

import subprocess
import re
import os
from io import StringIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.generator import Generator
import smtplib

BANDWIDTH_THRESHOLD = 20

def collect_data():
    data = {}
    command = 'speedtest-cli --simple'
    try:
        output = subprocess.check_output(command.split())
    except subprocess.CalledProcessError as e:
        print("%s call failed" % command)
        print("Output generated before error:")
        print(e.output)
        print("Return code:")
        print(e.returncode)
        raise

    output = output.decode('utf-8')
    ping_pattern = re.compile(r'Ping: (?P<ping>.*) .*')
    download_pattern = re.compile(r'Download: (?P<download>.*) .*')
    upload_pattern = re.compile(r'Upload: (?P<upload>.*) .*')

    for line in output.splitlines():
        match = re.match(ping_pattern, line)
        if match:
            data['ping'] = float(match.group('ping'))
        match = re.match(download_pattern, line)
        if match:
            data['download'] = float(match.group('download'))
        match = re.match(upload_pattern, line)
        if match:
            data['upload'] = float(match.group('upload'))

    return data


def send_email(data):
    try:
        gmail_user = os.environ.get('MAIL_USERNAME')
        gmail_password = os.environ.get('MAIL_PASSWORD')
    except:
        print('unable to import mail username/password')
        raise
    subject = 'Warning - Bandwidth speeds are low'
    body = 'Detected: Ping %s ms<br><br>Download %s Mbit/s<br><br> Upload %s Mbit/s' % (data['ping'],
                                                                           data['download'],
                                                                           data['upload'])

    from_address = ['Bandwidth Checker', gmail_user]
    recipient = ['Master', gmail_user]

    # 'alternative' MIME type - HTML and plaintext bundled in one email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = '%s' % Header(subject, 'utf-8')
    msg['From'] = '"%s" <%s>' % (Header(from_address[0], 'utf-8'),
                                 from_address[1])
    msg['To'] = '"%s" <%s>' % (Header(recipient[0], 'utf-8'), recipient[1])

    htmlpart = MIMEText(body, 'html', 'UTF-8')
    msg.attach(htmlpart)
    str_io = StringIO()
    g = Generator(str_io, False)
    g.flatten(msg)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, gmail_user, str_io.getvalue())
        server.close()
    except smtplib.SMTPException:
        print('Failed to send mail')


if __name__ == '__main__':
    data = collect_data()
    if data['download'] < BANDWIDTH_THRESHOLD:
        send_email(data)
