#include <Servo.h>
#include <avr/interrupt.h>

Servo s[5];
int v[5];

void setup() {
  Serial.begin(115200);

  s[0].attach(64); // thumb
  s[1].attach(63); // index
  s[2].attach(62); // middle
  s[3].attach(61); // ring
  s[4].attach(60); // pinky

  // Enable pin change interrupts on A10-A15 (PK2-PK7)
  PCICR |= (1 << PCIE2);  // Enable PCINT2 for Port K
  PCMSK2 |= (1 << PCINT18) | (1 << PCINT19) | (1 << PCINT20) | (1 << PCINT21) | (1 << PCINT22) | (1 << PCINT23);  // Enable PCINT for PK2-PK7
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

  // No refresh needed for hardware Servo
}

ISR(PCINT2_vect) {
  // Handle pin change interrupt on Port K (A10-A15)
  // Add interrupt handling code here
}