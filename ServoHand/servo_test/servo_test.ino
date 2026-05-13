// Arduino Mega Servo Port Monitor
// Monitor all servo ports and output to terminal

#include <Servo.h>

Servo s[5];
int v[5];

void setup() {
  Serial.begin(115200);

  s[0].attach(64); // thumb
  s[1].attach(63); // index
  s[2].attach(62); // middle
  s[3].attach(61); // ring
  s[4].attach(60); // pinky

  s[0].write(0);
  s[1].write(0);
  s[2].write(0);
  s[3].write(0);
  s[4].write(0);
}

void loop() {

}
