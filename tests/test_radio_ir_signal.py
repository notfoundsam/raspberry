import serial
import time
import array

ir_signal = "8851 4435 565 1644 591 512 568 565 566 540 567 1642 568 565 567 1644 592 539 540 565 592 1623 592 1647 594 511 589 1650 562 1646 593 1643 594 513 595 511 590 516 565 569 592 510 595 1615 570 564 592 514 593 513 566 565 541 567 591 515 592 513 567 565 541 565 592 515 565 565 541 565 591 517 564 541 590 515 591 541 591 1619 568 564 538 568 566 539 591 513 592 543 561 545 589 516 593 512 565 567 565 539 566 1644 565 567 593 1618 593 1643 594 515 590 514 565 1675 589 514 593"
# ir_signal = "332 432 437 431 437 432 438 432 434 433 436 25180 3480 1730 433 1300 436 431 436 432 436 434 436 1302 432 435 434 433 411 458 435 433 435 1301 436 433 436 1300 436 1302 434 436 432 1302 434 1300 416 1323 435 1299 436 1302 434 437 431 434 435 1304 433 433 434 431 438 432 436 432 437 432 436 432 438 431 437 433 434 432 439 428 437 434 411 1326 409 456 438 433 435 431 436 433 437 3043 431 434 432 436 434 432 434 433 437 433 434 433 436 431 437 433 438 430 436 431 437 434 435 431 434 435 436 432 435 431 438 433 434 433 437 432 436 432 434 433 438 431 436 434 435 433 434 433 437 434 434 432 436 433 435 433 436 433 436 431 435 434 435 438 434 436 436 433 432 1304 434 432 436 432 409 458 439 430 438 434 433 432 434 437 431 433 436 436 435 431 434 441 429 434 434 439 431 435 430 435 436 433 435 432 433 434 436 438 432 431 436 433 435 436 434 432 436 1297 440 430 439 1297 438 431 437 432 435 431 436 432 438 432 438 431 443 428 431 437 435 438 427 435 438 431 434 432 438 431 435 436 407 457 436 433 439 431 435 431 466 403 412 458 434 432 435 437 433 436 434 430 434 440 431 434 438 432 433 435 434 431 434 435 434 437 430 437 431 436 435 435 434 437 430 435 440 427 434 436 435 430 438 436 431 434 435 431 437 432 435 433 437 432 434 434 433 436 436 429 437 441 429 435 438 431 433 1302 434 432 412 1327 434 1297 436 1303 439 431 434 34727 3478 1731 436 1304 434 437 429 433 414 464 427 1303 436 430 412 460 408 456 412 460 408 1328 436 431 445 1290 411 1328 411 455 437 1301 440 1296 434 1302 435 1300 438 1302 436 432 435 431 435 1302 434 437 434 434 434 431 435 436 434 432 437 431 437 433 433 436 435 436 430 436 435 433 435 433 435 430 436 436 435 430 438 434 438 429 436 432 436 1299 436 432 437 434 433 1301 438 434 431 437 435 1301 432 432 436 437 434 1299 435 436 432 1302 437 433 436 1299 436 435 436 429 438 429 437 433 410 459 438 436 428 436 439 426 439 430 436 434 434 435 431 436 434 434 433 437 434 1302 434 1302 436 430 438 435 434 431 438 431 434 435 434 430 444 429 434 436 430 433 439 432 433 435 435 431 439 430 436 430 439 436 433 431 439 431 435 432 434 436 434 1298 439 1298 438 434 436 432 434 435 435 431 440 426 439 432 436 431 436 431 439 429 438 431 444 1294 435 1300 435 436 434 432 439 430 435 434 438 431 434 432 439 430 439 427 440 430 439 427 440 431 439 432 433 435 435 430 439 429 439 429 439 431 442 1293 439 1297 438 430 444 425 439 430 439 431 434 1304 432 1308 429 432 442 427 439 428 441 431 434 437 431 433 436 430 439 436 430 432 440 428 440 427 439 431 440 431 435 431 439 432 434 433 435 435 434 1298 439 1300 439 1297 436 1302 436 430 440 1299 434 1298 439"
# ir_signal = "332 432 437 431 437 432 438 432 434 433 436"
radio_pipe = 'AABBCCDD33'

success = 0
fail = 0
error = 0

ser = serial.Serial()
ser.baudrate = 500000
ser.port = '/dev/ttyUSB0'
ser.timeout = 5
ser.open()

# Only after writing sketch into Arduino
# print(repr(ser.readline()))
time.sleep(2)
ser.flushInput()
ser.flushOutput()

pre_test_data = []
test_data = []
pre_test_data.append('%si' % radio_pipe)

zero = []
one = []
compressed = ''

for value in ir_signal.split(' '):
    x = int(value)
    if x > 65000:
        test_data.append('65000')
        if compressed != '':
            test_data.append("[%s]" % compressed)
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
                test_data.append("[%s]" % compressed)
                compressed = ''
            test_data.append(value)

if compressed != '':
    test_data.append("[%s]" % compressed)

test_data.append('\n')


pre_test_data.append(str(sum(zero)/len(zero)))
pre_test_data.append(str(sum(one)/len(one)))
signal = ' '.join(pre_test_data + test_data)

print("-----signal------")
print(signal)

n = 32
partial_signal = [signal[i:i+n] for i in range(0, len(signal), n)]

try:
    while True:
        ser.flushInput()
        ser.flushOutput()
        print "-----------------"

        response_in = ""

        for part in partial_signal:
            b_arr = bytearray(part)
            print(b_arr)
            ser.write(b_arr)
            ser.flush()

            response_in = ser.readline()
            # print(repr(response_in))

            if response_in.rstrip() != 'next':
                break;
            response_in = ""
        
        if response_in == "":
            response_in = ser.readline()
        
        print("-----------")
        print(repr(response_in))
        
        response = response_in.rstrip()

        data = response.split(':')

        if 1 < len(data):
            if data[1] == 'FAIL':
                fail += 1
                time.sleep(5)
            elif data[1] == 'OK':
                success += 1
        else:
            error += 1
            print(repr(response_in))

        print "Success: %d Fail: %d Error: %d" % (success, fail, error)
        if data[0]:
                print(data[0])

        time.sleep(0.5)

except KeyboardInterrupt:
    ser.flushInput()
    ser.flushOutput()
    ser.close()
    print("QUIT")
