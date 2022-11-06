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
        self.test() # must send the AT command before everything
        self.sim_init()

    def sim_init(self):
        logging.info("Init SIM900A ...")
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
        logging.info("Init SIM900A done")

    
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
        rcv = self.ser.read(self.ser.in_waiting).decode("utf-8")
        return rcv == "OK"

    def factory_reset(self):
        for i in range(5):
            self.ser.write(b'AT&F\r')
            time.sleep(0.4)
            self.ser.flushOutput()

    def get_sim_status(self):
        self.ser.write(b'AT+CSMINS?\r')
        time.sleep(self.TIME_PER_BYTES * 20)
        rcv = self.ser.read(self.ser.in_waiting).decode("utf-8") 
        response = re.search(r"(\+CSMINS:.*)", rcv)
        if response:
            msg = response.group()
            logging.info(msg)
            return msg


    def get_provider_name(self):
        self.ser.write(b'AT+CSPN?\r')
        time.sleep(self.TIME_PER_BYTES * 20)
        rcv = self.ser.read(self.ser.in_waiting).decode("utf-8")
        response = re.search(r"(\+CSPN:.*)", rcv)
        if response:
            msg = response.group()
            logging.info(msg)
            return msg

    def send_sms(self, msg: str, phone: str):
        cmd = b'AT+CMGS=' + f'"{phone}"'.encode('utf-8') + b'\r'
        self.ser.write(cmd)
        time.sleep(1)
        self.ser.write(str.encode(msg + chr(26)))


    def read_all_sms(self):
        # logging.info('Read all sms: AT+CMGL="ALL"')
        self.ser.write(b'AT+CMGL="ALL"\r')
        time.sleep(1)
        try:
            rcv = self.ser.read(self.ser.in_waiting).decode("utf-8").replace('\r', '')
            sms = re.findall(r'(\+CMGL: \d.*\n.*)', rcv)
            return [SMS(s) for s in sms]
        except Exception as e:
            logging.error(e)
            self.sim_init()
            return []

    def delete_all_read_sms(self):
        self.ser.write(b'AT+CMGDA="DEL READ"\r')
        # logging.info('Delete all read sms: AT+CMGDA="DEL READ"')
        time.sleep(1)
        self.ser.flushOutput()

    def __del__(self):
        if isinstance(self.ser, serial.Serial):
            print("Close serial port")
            self.ser.close()

    
