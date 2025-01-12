import serial
import time

arduino = serial.Serial(port='COM3',  baudrate=9600, timeout=.1)


def write_read(x):
    arduino.write(x.encode('utf-8'))

while 1:
    x = input()
    write_read(x);




