#include <Arduino.h>
#include <Servo.h>

// Standard servo - moves to specific positions (0-180 degrees)

const int SERVO_PIN = 60;

Servo myServo;

void setup() {
	myServo.attach(SERVO_PIN);
	// give the servo a moment
	delay(500);
}

void loop() {
	// Sweep from 0 to 180 and back
	for (int pos = 0; pos <= 180; pos += 10) {
		myServo.write(pos);
		delay(5);
	}
	for (int pos = 180; pos >= 0; pos -= 10) {
		myServo.write(pos);
		delay(5);
	}
}

