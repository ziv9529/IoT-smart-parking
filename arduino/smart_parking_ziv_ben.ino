// smart parking system

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

const int OCCUPIED_CM = 20;
const int DARK_LEVEL = 300;
const int TOTAL_SPOTS = 2;

const unsigned long SAMPLE_INTERVAL = 2000;
const unsigned long GATE_OPEN_TIME = 4000;

Servo gate;

long distance1 = 400;
long distance2 = 400;

int spot1 = 0;
int spot2 = 0;
int freeSpots = TOTAL_SPOTS;
int lightValue = 0;
int lampState = 0;

bool gateOpen = false;

unsigned long lastSampleTime = 0;
unsigned long gateOpenedTime = 0;

long readDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  unsigned long duration = pulseIn(echoPin, HIGH, 30000);

  if (duration == 0) {
    return 400;
  }

  return duration * 0.034 / 2;
}

void sendTelemetry() {
  Serial.print("{\"spot1\":");
  Serial.print(spot1);

  Serial.print(",\"spot2\":");
  Serial.print(spot2);

  Serial.print(",\"distance1\":");
  Serial.print(distance1);

  Serial.print(",\"distance2\":");
  Serial.print(distance2);

  Serial.print(",\"free\":");
  Serial.print(freeSpots);

  Serial.print(",\"light\":");
  Serial.print(lightValue);

  Serial.print(",\"lamp\":");
  Serial.print(lampState);

  Serial.print(",\"gate\":");
  Serial.print(gateOpen ? 1 : 0);

  Serial.println("}");
}

void updateSensors() {
  distance1 = readDistance(TRIG1, ECHO1);
  distance2 = readDistance(TRIG2, ECHO2);

  spot1 = distance1 < OCCUPIED_CM ? 1 : 0;
  spot2 = distance2 < OCCUPIED_CM ? 1 : 0;
  freeSpots = TOTAL_SPOTS - spot1 - spot2;

  digitalWrite(LED_SPOT1, spot1);
  digitalWrite(LED_SPOT2, spot2);

  lightValue = analogRead(LDR_PIN);
  lampState = lightValue < DARK_LEVEL ? 1 : 0;

  digitalWrite(LED_LAMP, lampState);
}

void openGate() {
  if (freeSpots == 0) {
    Serial.println("LOG:GATE_BLOCKED_PARKING_FULL");
    sendTelemetry();
    return;
  }

  gate.write(90);
  gateOpen = true;
  gateOpenedTime = millis();

  Serial.println("LOG:GATE_OPENED");
  sendTelemetry();
}

void closeGate() {
  gate.write(0);
  gateOpen = false;

  Serial.println("LOG:GATE_CLOSED");
  sendTelemetry();
}

void handleSerialCommand() {
  if (Serial.available() == 0) {
    return;
  }

  delay(20);

  String command = Serial.readString();
  command.trim();

  if (command == "OPEN_GATE") {
    openGate();
  }
  else if (command == "CLOSE_GATE") {
    closeGate();
  }
  else if (command.length() > 0) {
    Serial.print("LOG:UNKNOWN_COMMAND:");
    Serial.println(command);
  }
}

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(100);

  pinMode(TRIG1, OUTPUT);
  pinMode(ECHO1, INPUT);
  pinMode(TRIG2, OUTPUT);
  pinMode(ECHO2, INPUT);

  pinMode(LED_SPOT1, OUTPUT);
  pinMode(LED_SPOT2, OUTPUT);
  pinMode(LED_LAMP, OUTPUT);

  gate.attach(SERVO_PIN);
  gate.write(0);

  updateSensors();
  sendTelemetry();
}

void loop() {
  handleSerialCommand();

  if (gateOpen && millis() - gateOpenedTime >= GATE_OPEN_TIME) {
    closeGate();
  }

  if (millis() - lastSampleTime >= SAMPLE_INTERVAL) {
    lastSampleTime = millis();
    updateSensors();
    sendTelemetry();
  }
}