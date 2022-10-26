import serial
import logging
import time
import re
from .sms import SMS

class SIM900A:
    TIME_PER_BYTES = 0.04

    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        # connect to serial
        logging.info(f"Connect to serial port {port}, baudrate = {baudrate}")
        self.ser = serial.Serial(port, baudrate)
        if not self.ser.is_open:
            logging.error("The serial port should be open. Check the port and baudrate.")
        # test AT command
        self.sim_init()

    def sim_init(self):
        logging.info("Init SIM900A ...")
        # reset config
        self.ser.write(b'ATZ\r')
        time.sleep(5)
        # no echo
        self.ser.write(b'ATE0\r')
        time.sleep(0.2)
        # sms in text mode
        self.ser.write(b'AT+CMGF=1\r')
        time.sleep(0.2)
        # notify the received sms result codes
        self.ser.write(b'AT+CNMI=1,1,0,0,0\r')
        time.sleep(0.2)
        # store sms in sim card
        self.ser.write(b'AT+CPMS="SM","SM","SM"\r')
        time.sleep(0.2)
        # save settings
        self.ser.write(b'AT+CSAS\r')
        time.sleep(0.2)
        self.ser.flushOutput()

    
    def send_message(self, phone_number: str, msg: str):
        logging.info(f"sending the message to {phone_number}: {msg} ")
        self.ser.write(str.encode(f'AT+CMGS="{phone_number}"') + b'\r')
        time.sleep(0.5)
        self.ser.write(str.encode(msg + chr(26)))
        self.ser.flushOutput()
        logging.info("message sent")

    def test(self):
        self.ser.write(b'AT\r')
        time.sleep(self.TIME_PER_BYTES * 6)
        rcv = self.ser.read(self.ser.in_waiting).replace(b'\r\n', b'').decode("utf-8")
        print("debug test", rcv)
        return rcv == "OK"


    def get_sim_status(self):
        self.ser.write(b'AT+CSMINS?\r')
        time.sleep(self.TIME_PER_BYTES * 20)
        rcv = self.ser.read(self.ser.in_waiting).decode("utf-8") 
        response = re.search(r"(\+CSMINS:.*)", rcv)
        if response:
            return response.group()


    def get_provider_name(self):
        self.ser.write(b'AT+CSPN?\r')
        time.sleep(self.TIME_PER_BYTES * 20)
        rcv = self.ser.read(self.ser.in_waiting).decode("utf-8")
        response = re.search(r"(\+CSPN:.*)", rcv)
        if response:
            return response.group()

    def read_all_sms(self):
        self.ser.write(b'AT+CMGL="ALL"\r')
        time.sleep(1)
        try:
            rcv = self.ser.read(self.ser.in_waiting).decode("utf-8").replace('\r', '')
            sms = re.findall(r'(\+CMGL: \d.*\n.*)', rcv)
            return [SMS(s) for s in sms]
        except Exception as e:
            logging.error(e)
            logging.error("Reset SIM900A")
            self.ser.write(b'ATZ\r')
            time.sleep(5)
            self.sim_init()
            return []

    def delete_all_read_sms(self):
        self.ser.write(b'AT+CMGDA="DEL READ"\r')
        time.sleep(1)
        self.ser.flushOutput()

    def __del__(self):
        if isinstance(self.ser, serial.Serial):
            logging.info("Close serial port")
            self.ser.close()

    
