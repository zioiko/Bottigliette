// ===================== PIN DEFINITIONS =====================
// First participant
const int buttonPin1 = 7;
const int touchPinUP1 = 3;
const int touchPinDOWN1 = 2;

// Second participant
const int buttonPin2 = 8;
const int touchPinUP2 = 5;
const int touchPinDOWN2 = 4;

// Feedback LED
const int ledPin = 11;

// ===================== STATE VARIABLES =====================
// First participant
bool touchUP1 = false;
bool touchDOWN1 = false;
unsigned long startTime1 = 0;
unsigned long graspingTime1 = 0;

// Second participant
bool touchUP2 = false;
bool touchDOWN2 = false;
unsigned long startTime2 = 0;
unsigned long graspingTime2 = 0;

// Button edge detection
bool lastButtonState1 = HIGH;
bool lastButtonState2 = HIGH;

// Time window logic
unsigned long timeDifference = 0;
unsigned long timeWin = 250;   // 250 ms
int n_outside = 0;
int n_within = 0;

// ===================== TIME WINDOW FUNCTIONS =====================
void incrementTimeWin() {
  timeWin += 25;   // +25 ms
}

void reduceTimeWin() {
  if (timeWin > 25) {
    timeWin -= 25;
  }
}

// ===================== SETUP =====================
void setup() {
  Serial.begin(9600);

  pinMode(buttonPin1, INPUT_PULLUP);
  pinMode(buttonPin2, INPUT_PULLUP);

  pinMode(touchPinUP1, INPUT);
  pinMode(touchPinDOWN1, INPUT);
  pinMode(touchPinUP2, INPUT);
  pinMode(touchPinDOWN2, INPUT);

  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);
}

// ===================== LOOP =====================
void loop() {

  // -------- READ INPUTS --------
  int buttonState1 = digitalRead(buttonPin1);
  int buttonState2 = digitalRead(buttonPin2);

  int touchStateUP1 = digitalRead(touchPinUP1);
  int touchStateDOWN1 = digitalRead(touchPinDOWN1);
  int touchStateUP2 = digitalRead(touchPinUP2);
  int touchStateDOWN2 = digitalRead(touchPinDOWN2);

  // -------- BUTTON EDGE DETECTION --------
  bool buttonPressed1 = (lastButtonState1 == HIGH && buttonState1 == LOW);
  bool buttonPressed2 = (lastButtonState2 == HIGH && buttonState2 == LOW);

  lastButtonState1 = buttonState1;
  lastButtonState2 = buttonState2;

  // ================= FIRST PARTICIPANT =================
  if (buttonPressed1) {
    startTime1 = millis();
    touchUP1 = false;
    touchDOWN1 = false;
    Serial.println("START PARTICIPANT 1");
  }

  if (touchStateUP1 == HIGH && !touchUP1) {
    graspingTime1 = millis() - startTime1;
    touchUP1 = true;
    Serial.print("Grasping UP1: ");
    Serial.println(graspingTime1);
  }

  if (touchStateDOWN1 == HIGH && !touchDOWN1) {
    graspingTime1 = millis() - startTime1;
    touchDOWN1 = true;
    Serial.print("Grasping DOWN1: ");
    Serial.println(graspingTime1);
  }

  // ================= SECOND PARTICIPANT =================
  if (buttonPressed2) {
    startTime2 = millis();
    touchUP2 = false;
    touchDOWN2 = false;
    Serial.println("START PARTICIPANT 2");
  }

  if (touchStateUP2 == HIGH && !touchUP2) {
    graspingTime2 = millis() - startTime2;
    touchUP2 = true;
    Serial.print("Grasping UP2: ");
    Serial.println(graspingTime2);
  }

  if (touchStateDOWN2 == HIGH && !touchDOWN2) {
    graspingTime2 = millis() - startTime2;
    touchDOWN2 = true;
    Serial.print("Grasping DOWN2: ");
    Serial.println(graspingTime2);
  }

  // ================= TIME COMPARISON =================
  if (graspingTime1 > 0 && graspingTime2 > 0) {

    timeDifference = abs(graspingTime1 - graspingTime2);

    Serial.print("Time difference: ");
    Serial.println(timeDifference);

    if (timeDifference <= timeWin) {
      n_within++;
      n_outside = 0;

      if (n_within == 2) {
        reduceTimeWin();
        n_within = 0;
        Serial.println("Time window REDUCED");
      }

    } else {
      n_outside++;
      n_within = 0;

      digitalWrite(ledPin, HIGH);
      delay(500);
      digitalWrite(ledPin, LOW);

      if (n_outside == 2) {
        incrementTimeWin();
        n_outside = 0;
        Serial.println("Time window INCREASED");
      }
    }

    graspingTime1 = 0;
    graspingTime2 = 0;
  }
}

