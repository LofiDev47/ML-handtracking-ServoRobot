#include <Servo.h>

Servo s[6];
int v[6];

void setup() {
  Serial.begin(115200);

  s[0].attach(60); // thumb
  s[1].attach(61); // index
  s[2].attach(62); // middle
  s[3].attach(63); // ring
  s[4].attach(64); // pinky
  s[5].attach(65); // wrist
}

void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');

    int i = 0;
    char* ptr = strtok((char*)data.c_str(), ",");

    while (ptr && i < 6) {
      v[i++] = constrain(atoi(ptr), 0, 180);
      ptr = strtok(NULL, ",");
    }

    if (i == 6) {
      for (int j = 0; j < 6; j++) {
        s[j].write(v[j]);
      }
    }
  }
}
