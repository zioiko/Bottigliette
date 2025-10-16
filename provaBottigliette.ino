const int buttonPin = 4;
const int touchPin = 3;
float startTime;
bool touch = false;

unsigned long startTime = 0;
unsigned long reactionTime = 0;

void setup() {
 Serial.begin(9600);
 pinMode(buttonPin,INPUT_PULLUP);
 pinMode(touchPin,INPUT);

}

void loop() {
  int buttonState = digitalRead(buttonPin);
  int touchState = digitalRead(touchPin);

  if (buttonState == LOW) {
  startTime = 0;
  }
  else {
    startTime=millis();
    touch = true
  }

  if (touchState == HIGH && touch == true) {
    graspingTime = millis() - startTime;
    Serial.print("Grasping time: ");
    Serial.println(graspingTime);
  }

  if (buttonState == LOW && touch == true) {
    totalTime = millis() - startTime;
    Serial.print("Total time: ");
    Serial.println(totalTime);
    touch = false;
  }
}
