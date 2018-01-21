#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>
RF24 radio(9, 10);
unsigned short index = 0;
unsigned char packageEnd = '\n';
unsigned short code;
char strBuffer[20];
byte strIndex = 0;

unsigned long started_waiting_at;               // Set up a timeout period, get the current microseconds
boolean timeout = false;
boolean isEnded = false;

void setup() {
  Serial.begin(500000);
  Serial.setTimeout(50);
  
  radio.begin();
  delay(1000);
  radio.powerUp();
  radio.setChannel(75);
  radio.setRetries(15,15);
  radio.setDataRate(RF24_250KBPS);     // (RF24_250KBPS, RF24_1MBPS, RF24_2MBPS)
  radio.setPALevel(RF24_PA_MAX);       // (RF24_PA_MIN=-18dBm, RF24_PA_LOW=-12dBm, RF24_PA_HIGH=-6dBm, RF24_PA_MAX=0dBm)
  radio.setAutoAck(1);
  radio.openWritingPipe(0xAABBCCDD11LL);
  // radio.openWritingPipe(0xF0F0F0F0AALL);
  radio.startListening();
  Serial.print("Loaded\n");
}

void loop() {
  if (Serial.available() > 0) {
    if (!readSerial()) {
      Serial.print("FAIL\n");
    } else {
      Serial.print("OK\n");
    }

    timeout = false;
    index = 0;
    radio.startListening();
  }
}

boolean readSerial() {
  byte portSignal[1000];
  timeout = true;
  started_waiting_at = micros();
  
  
  while (timeout == true && (micros() - started_waiting_at < 200000)) {

    if (Serial.available() > 0) {
      started_waiting_at = micros();
      
      code = Serial.read();
      portSignal[index] = code;
      index++;
      if (code == 10) {
        timeout = false;
        break;
      }
    }
  }
  
  if (timeout) {
    Serial.print("TIMEOUT\n");
  } else {

    // If recive IR signal (it starts with i)
    if (portSignal[0] == 105) {
      return irSignal(portSignal);
    }
  }
  
  return true;
}

boolean irSignal(byte *signal) {
  byte b;
  int count = 0;
  radio.stopListening();

  // Add pipes
  
  for (int i = 3; i < index; i++) {
    b = signal[i];
    
    if (b > 47 && b < 58) {
      strBuffer[strIndex] = b;
      strIndex++;
    } else if (b == 32) {
      count++;
      if (!sendSignal(atoi(strBuffer))) {
        return false;
      }
      clearBuffer();
    } else if (b == 10) {
      if (!radio.write(&packageEnd, sizeof(packageEnd))) {
        return false;
      }
    }
  }

  return true;
}

boolean sendSignal(int code) {
  if (!radio.write(&code, sizeof(code))) {
    return false;
  }
  
  return true;
}
void clearBuffer() {
  memset(strBuffer, 0, sizeof(strBuffer));
  strIndex = 0;
}