const int buttonPin = 4;
const int touchPinUP = 3;
const int touchPinDOWN = 5;
bool touchUP = false;
bool touchDOWN = false;
bool buttonReleased = false;
float startTime;
float graspingTime;
float totalTime;

void setup() {
 Serial.begin(9600);
 pinMode(buttonPin,INPUT);
 pinMode(touchPinUP,INPUT);
 pinMode(touchPinDOWN,INPUT);

}

void loop() {
  int buttonState = digitalRead(buttonPin);
  int touchStateUP = digitalRead(touchPinUP);
  int touchStateDOWN = digitalRead(touchPinDOWN);

  // Start record time when button is not pressed
  if (buttonState == HIGH && (!touchUP && !touchDOWN)) {
  startTime = millis();
  Serial.print("Start time: ");
  Serial.println(startTime);
  buttonReleased = true;
  }

  // First bottle, up part
  if (touchStateUP == HIGH && buttonReleased == true && touchUP == false) {
    graspingTime = millis() - startTime;
    Serial.print("Grasping timeUP: ");
    Serial.println(graspingTime);
    touchUP = true;
  }

  if (buttonState == HIGH && touchUP == true && buttonReleased == true) {
    totalTime = millis() - startTime;
    Serial.print("Total time UP: ");
    Serial.println(totalTime);
    touchUP = false;
    buttonReleased = false;
    
  }
  // First bottle, down part

  if (touchStateDOWN == HIGH && buttonReleased == true && touchDOWN == false) {
    graspingTime = millis() - startTime;
    Serial.print("Grasping time DOWN: ");
    Serial.println(graspingTime);
    touchDOWN = true;
  }

  if (buttonState == HIGH && touchDOWN == true && buttonReleased == true) {
    totalTime = millis() - startTime;
    Serial.print("Total time DOWN: ");
    Serial.println(totalTime);
    touchDOWN = false;
    buttonReleased = false;  
    
  }
}
