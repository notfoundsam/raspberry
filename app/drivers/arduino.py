from __future__ import print_function
import serial
import time, random
import array
import os, sys
import threading, Queue
import requests
from app import so

class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Also, the decorated class cannot be
    inherited from. Other than that, there are no restrictions that apply
    to the decorated class.

    To get the singleton instance, use the `Instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def Instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)

@Singleton
class Arduino():
    ser = None
    queue = None
    starter = None

    def startQueue(self):
        self.queue = ArduinoQueue(self.ser)
        self.queue.start()
    
    def activateQueueStarter(self):
        self.starter = ArduinoQueueStarter()
        self.starter.start()

    def send(self, btn, sid):
        self.queue.putItem(ArduinoQueueItem(self.ser, btn, sid, 1))

    def status(self, radio):
        self.queue.putItem(ArduinoQueueRadio(self.ser, radio, 5))

    def connect(self, env = ''):
        if self.ser is None:
            print('Connect to /dev/ttyUSB0', file=sys.stderr)

            if env == 'dev':
                self.ser = SerialDev()
            else:
                self.ser = serial.Serial()
                
            self.ser.baudrate = 500000
            self.ser.port = '/dev/ttyUSB0'
            self.ser.timeout = 10
            self.ser.open()

            # Only after write sketch into Arduino
            time.sleep(2)
            self.ser.flushInput()
            self.ser.flushOutput()
            # print(repr(self.ser.readline()), file=sys.stderr)
            self.activateQueueStarter()

class ArduinoQueue(threading.Thread):

    def __init__(self, ser):
        threading.Thread.__init__(self)
        self.ser = ser
        self.workQueue = Queue.PriorityQueue()

    def run(self):
        while True:
            if not self.workQueue.empty():
                # print('get new item', file=sys.stderr)
                queue_item = self.workQueue.get()
                queue_item.run()
                # print('run over', file=sys.stderr)
            else:
                time.sleep(0.05)

    def putItem(self, item):
        self.workQueue.put(item)

class ArduinoQueueStarter(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        time.sleep(2)
        r = requests.get('http://127.0.0.1:5000/')
        print('Send first request', file=sys.stderr)

class ArduinoQueueItem():

    def __init__(self, ser, btn, sid, priority):
        self.signal = ''
        self.buffer = 32
        self.ser = ser
        self.btn = btn
        self.sid = sid
        self.priority = priority
        self.radio = btn.radio

        # print("--------------", file=sys.stderr)
        # print(self.btn.radio.pipe, file=sys.stderr)

    def __cmp__(self, other):
        return cmp(self.priority, other.priority)

    def encodeBits(self, data):
        counter = 0
        zero = None
        encode = ''
        
        for digit in data:
            if digit == '0':
                if zero == None:
                    zero = True

                if counter > 0 and zero == False:
                    encode += str(counter) + 'b'
                    counter = 1
                    zero = True
                else:
                    counter += 1

            elif digit == '1':
                if zero == None:
                    zero = False

                if counter > 0 and zero == True:
                    encode += str(counter) + 'a'
                    counter = 1
                    zero = False
                else:
                    counter += 1

        if counter > 0:
            if zero == True:
                encode += str(counter) + 'a'
            if zero == False:
                encode += str(counter) + 'b'


        return encode

    def prepareIrSignal(self):
        pre_data = []
        data = []
        pre_data.append('%si' % self.btn.radio.pipe)

        zero = []
        one = []
        compressed = ''

        for value in self.btn.signal.split(' '):
            x = int(value)
            if x > 65000:
                data.append('65000')
                if compressed != '':
                    data.append("[%s]" % encodeBits(compressed))
                    compressed = ''
            else:
                if x < 1800:
                    code = '0'
                    if x < 1000:
                        zero.append(x)
                    elif 1000 <= x:
                        one.append(x)
                        code = '1'
                    compressed += code
                else:
                    if compressed != '':
                        data.append("[%s]" % encodeBits(compressed))
                        compressed = ''
                    data.append(value)

        if compressed != '':
            data.append("[%s]" % encodeBits(compressed))

        data.append('\n')

        pre_data.append(str(sum(zero)/len(zero)))
        pre_data.append(str(sum(one)/len(one)))

        self.signal = ' '.join(pre_data + data)
        print(self.signal, file=sys.stderr)

    def prepareCommand(self):
        self.signal = '%sc %s\n' % (self.btn.radio.pipe, self.btn.signal)

    def run(self):
        self.ser.flushInput()
        self.ser.flushOutput()

        if self.btn.type == 'ir':
            self.prepareIrSignal()
        elif self.btn.type == 'cmd':
            self.prepareCommand()

        partial_signal = [self.signal[i:i+self.buffer] for i in range(0, len(self.signal), self.buffer)]
        
        response = ""

        for part in partial_signal:
            b_arr = bytearray(part.encode())
            self.ser.write(b_arr)
            self.ser.flush()

            response = self.ser.readline()
            response = response.rstrip()

            if response != 'next':
                break;

            response = ""
        
        if response == "":
            response = ser.readline()

        data = response.split(':')

        if 1 < len(data):
            if data[1] == 'FAIL':
                so.emit('json', {'response': {'result': 'error', 'message': data[0]}}, namespace='/remotes', room=self.sid)
            elif data[1] == 'OK':
                so.emit('json', {'response': {'result': 'error', 'message': data[0]}}, namespace='/remotes', room=self.sid)
        else:
            so.emit('json', {'response': {'result': 'error', 'message': 'Unknown error'}}, namespace='/remotes', room=self.sid)

class ArduinoQueueRadio():

    def __init__(self, ser, radio, priority):
        self.signal = ''
        self.buffer = 32
        self.ser = ser
        self.radio = radio
        self.priority = priority

    def __cmp__(self, other):
        return cmp(self.priority, other.priority)
    
    def run(self):
        self.ser.flushInput()
        self.ser.flushOutput()

        self.signal = 'c%s %s\n' % (self.radio.pipe, 'status')

        partial_signal = [self.signal[i:i+self.buffer] for i in range(0, len(self.signal), self.buffer)]
        
        response = ""

        for part in partial_signal:
            b_arr = bytearray(part.encode())
            self.ser.write(b_arr)
            self.ser.flush()

            response = self.ser.readline()
            response = response.rstrip()

            if response != 'next':
                break;

            response = ""
        
        if response == "":
            response = ser.readline()

        data = response.split(':')
        print(repr(response), file=sys.stderr)

        if 1 < len(data):
            if data[1] == 'FAIL':
                so.emit('json', {'response': {'result': 'error', 'message': data[0]}}, namespace='/radios')
            elif data[1] == 'OK':
                self.getStatus(data[0])
        else:
            so.emit('json', {'response': {'result': 'error', 'message': 'Unknown error'}}, namespace='/radios')

    def getStatus(self, data):
        sensors_data = dict(s.split(' ') for s in data.split(','))
        sensors = {}

        if self.radio.dht == 1:
            if 'hum' in sensors_data:
                sensors['hum'] = sensors_data['hum']
  
            if 'temp' in sensors_data:
                sensors['temp'] = sensors_data['temp']

        if self.radio.battery == 1:
            if 'bat' in sensors_data:
                sensors['bat'] = sensors_data['bat']

        so.emit('json', {'response': {'result': 'success', 'callback': 'radio_sensor_refresh', 'id': self.radio.id, 'sensors': sensors}}, namespace='/radios')

class SerialDev():
    transfer = False

    def open(self):
        print('SERIAL DEV: Connect to /dev/ttyUSB0', file=sys.stderr)

    def flushInput(self):
        print('SERIAL DEV: flushInput', file=sys.stderr)

    def flushOutput(self):
        print('SERIAL DEV: flushOutput', file=sys.stderr)

    def flush(self):
        print('SERIAL DEV: flush', file=sys.stderr)

    def write(self, data):
        print('SERIAL DEV: Recieved bytearray', file=sys.stderr)
        if data.endswith("\n"):
            self.transfer = False
        else:
            self.transfer = True
        print(data, file=sys.stderr)


    def readline(self):
        if self.transfer == False:
            temp = random.uniform(18, 26)
            hum = random.uniform(35, 65)
            bat = random.uniform(0.1, 1)
            return "temp %.2f,hum %.2f,bat %.2f:OK\n" % (temp, hum, bat)
        else:
            return "next\n"
