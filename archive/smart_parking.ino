// smart parking system
// reads 2 ultrasonic sensors + ldr + tmp36, drives leds and the gate servo,
// and prints one json line per cycle over serial

#include <Servo.h>

#define TRIG1 2
#define ECHO1 3
#define TRIG2 4
#define ECHO2 5
#define LED_SPOT1 6
#define LED_SPOT2 7
#define LED_LAMP 8
#define SERVO_PIN 9
#define LDR_PIN A0
#define TMP_PIN A1

const int OCCUPIED_CM = 20;   // a car closer than this means the spot is taken
const int DARK_LEVEL = 300;   // ldr reading below this means it is dark
const int TOTAL_SPOTS = 2;
const int SAMPLE_DELAY = 2000;

Servo gate;

void setup() {
  Serial.begin(9600);

  pinMode(TRIG1, OUTPUT);
  pinMode(ECHO1, INPUT);
  pinMode(TRIG2, OUTPUT);
  pinMode(ECHO2, INPUT);
  pinMode(LED_SPOT1, OUTPUT);
  pinMode(LED_SPOT2, OUTPUT);
  pinMode(LED_LAMP, OUTPUT);

  gate.attach(SERVO_PIN);
  gate.write(0);   // barrier starts closed
}

// sends a pulse and converts the echo time to cm
long readDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  return duration * 0.034 / 2;
}

float readTemperature() {
  int raw = analogRead(TMP_PIN);
  float volts = raw * 5.0 / 1024.0;
  return (volts - 0.5) * 100.0;   // tmp36: 500mv offset, 10mv per degree
}

void loop() {
  long dist1 = readDistance(TRIG1, ECHO1);
  long dist2 = readDistance(TRIG2, ECHO2);

  int spot1 = (dist1 < OCCUPIED_CM) ? 1 : 0;
  int spot2 = (dist2 < OCCUPIED_CM) ? 1 : 0;
  int freeSpots = TOTAL_SPOTS - spot1 - spot2;

  digitalWrite(LED_SPOT1, spot1);   // red led on = spot taken
  digitalWrite(LED_SPOT2, spot2);

  int light = analogRead(LDR_PIN);
  int lamp = (light < DARK_LEVEL) ? 1 : 0;
  digitalWrite(LED_LAMP, lamp);

  // the gate only opens while there is somewhere to park
  gate.write(freeSpots > 0 ? 90 : 0);

  float temp = readTemperature();

  Serial.print("{\"spot1\":");
  Serial.print(spot1);
  Serial.print(",\"spot2\":");
  Serial.print(spot2);
  Serial.print(",\"free\":");
  Serial.print(freeSpots);
  Serial.print(",\"light\":");
  Serial.print(light);
  Serial.print(",\"lamp\":");
  Serial.print(lamp);
  Serial.print(",\"temp\":");
  Serial.print(temp, 1);
  Serial.println("}");

  delay(SAMPLE_DELAY);
}
