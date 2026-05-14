#include <Servo.h>

Servo s[5];
int v[5];

void setup() {
  Serial.begin(115200);

  s[0].attach(60); // thumb
  s[1].attach(63); // index
  s[2].attach(62); // middle
  s[3].attach(61); // ring
  s[4].attach(64); // pinky
}

void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');

    int i = 0;
    char* ptr = strtok((char*)data.c_str(), ",");

    while (ptr && i < 5) {
      v[i++] = constrain(atoi(ptr), 0, 180);
      ptr = strtok(NULL, ",");
    }

    if (i == 5) {
      for (int j = 0; j < 5; j++) {
        s[j].write(v[j]);
      }
    }
  }
}