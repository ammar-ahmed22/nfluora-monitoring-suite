int voutPin = A0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  int voutValue = analogRead(voutPin);
  Serial.println(voutValue);
  delay(10);
}
