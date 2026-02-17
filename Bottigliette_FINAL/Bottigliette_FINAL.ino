// First participant's variable initialization
const int buttonPin1 = 7;
const int touchPinUP1 = 3;
const int touchPinDOWN1 = 2;

bool touchUP1 = false;
bool touchDOWN1 = false;
unsigned long startTrialTime;

bool buttonReleased1 = false;
unsigned long startTime1;
unsigned long graspingTime1ButtonReleased; // grasping time from button release 
unsigned long graspingTime1StartTrial; // grasping time from trial start
unsigned long totalTime1ButtonReleased;
unsigned long totalTime1StartTrial;

// Second participant's variable initialization
const int buttonPin2 = 8;
const int touchPinUP2 = 5;
const int touchPinDOWN2 = 4;

bool touchUP2 = false;
bool touchDOWN2 = false;
bool buttonReleased2 = false;
unsigned long startTime2;
unsigned long graspingTime2ButtonReleased;
unsigned long graspingTime2StartTrial; // grasping time from trial start
unsigned long totalTime2ButtonReleased;
unsigned long totalTime2StartTrial;

// Other variables initialization
unsigned long timeDifferenceButtonReleased;
unsigned long timeDifferenceStartTrial;
unsigned long timeWin = 0.25; //initialize time window: 250 ms
int n_outside = 0; // Counter for number of consecutive trials where timeDifference is outside time window
int n_within = 0; // Counter for number of consecutive trials where timeDifference is within time window
// Utily functions

  unsigned long GetTime(unsigned long startTime)
  {
    return millis() - startTime;
  }

 unsigned long incrementTimeWin()
 {
  timeWin = timeWin + 0.025;
  return timeWin;
 }
 unsigned long reduceTimeWin()
 {
  timeWin = timeWin - 0.025;
  return timeWin;
 }

  int isConsecutive(unsigned long timeDifference, int n_outside,int n_within, unsigned long timeWin)
  {
    if (timeDifference > timeWin && n_within == 1)
    {
      n_outside = 0;
      return n_outside;
    }
    if (timeDifference <= timeWin && n_outside ==1)
    {
      n_within = 0;
      return n_within;
    }

  }
 
 int changeTimeWin(unsigned long timeDifference, int n_outside, int n_within, unsigned long timeWin)
 {

  if (timeDifference <= timeWin) 
  {
    n_within = n_within + 1;
      if (n_within == 2)
    {
      reduceTimeWin();
      Serial.print('Time win reduced');
      n_within = 0;
      return n_within;
    }
    
    else 
    {
      return n_within;
    }

  }
  else 
  {
    digitalWrite(9,HIGH); //LED
    digitalWrite(10,HIGH);
    delay(500);
    digitalWrite(9,LOW);
    digitalWrite(10,LOW);
    

     n_outside = n_outside + 1;
     if (n_outside == 2)
     {
      incrementTimeWin();
      Serial.print('Time win incremented');
      n_outside = 0;
      return n_outside;
     }
     else 
     {
      return n_outside;
     }
  }
  
 }
 
 

void setup() {
 Serial.begin(9600);
 pinMode(buttonPin1,INPUT_PULLUP);
 pinMode(touchPinUP1,INPUT);
 pinMode(touchPinDOWN1,INPUT);
 pinMode(buttonPin2,INPUT_PULLUP);
 pinMode(touchPinUP2,INPUT);
 pinMode(touchPinDOWN2,INPUT);
 pinMode(10,OUTPUT); // pin attached to LEDs for feedback on grasping synchrony
 pinMode(9,OUTPUT);
}

void loop() {
  int buttonState1 = digitalRead(buttonPin1);
  int touchStateUP1 = digitalRead(touchPinUP1);
  int touchStateDOWN1 = digitalRead(touchPinDOWN1);
  int buttonState2 = digitalRead(buttonPin2);
  int touchStateUP2 = digitalRead(touchPinUP2);
  int touchStateDOWN2 = digitalRead(touchPinDOWN2);
  // Wait for start of the trial form serial
 if (Serial.available() > 0) {
  char c = Serial.read();

  if (c == '1') {
    startTrialTime = millis();
  }
}
}
 
  // ____________________________________________
  // ----------------FIRST BOTTLE----------------
  // ____________________________________________
  // Start record time when button is not pressed
  if (buttonState1 == LOW && (!touchUP1 && !touchDOWN1)) {
  startTime1 = millis(); // start timer from button release
  buttonReleased1 = true;
  }

  // First bottle, up part
  if (touchStateUP1 == HIGH && buttonReleased1 == true && touchUP1 == false && touchDOWN1 == false) {
  
    graspingTime1ButtonReleased = GetTime(startTime1);
    graspingTime1StartTrial = GetTime(startTrialTime);
    Serial.print("Grasping time UP1 from button release:");
    Serial.println(graspingTime1ButtonReleased);
    Serial.print("Grasping time UP1 from start trial:");
    Serial.println(graspingTime1StartTrial);
    touchUP1 = true;
    
  }

  if (buttonState1 == LOW && touchUP1 == true && buttonReleased1 == true) {
    totalTime1ButtonReleased = GetTime(startTime1);
    totalTime1StartTrial = GetTime(startTrialTime);
    Serial.print("Total time UP1 from button release:");
    Serial.println(totalTime1ButtonReleased);
    Serial.print("Total time UP1 from start trial:");
    Serial.println(totalTime1StartTrial);
    touchUP1 = false;
    buttonReleased1 = false;
    
  }
  // First bottle, down part

  if (touchStateDOWN1 == HIGH && buttonReleased1 == true && touchDOWN1 == false && touchUP1 == false) { // touchUP1==false to avoid double inputting from pressing the down part and then the top one
    graspingTime1ButtonReleased = GetTime(startTime1); 
    graspingTime1StartTrial = GetTime(startTrialTime);
    Serial.print("Grasping time DOWN1 from button release:");
    Serial.println(graspingTime1ButtonReleased);
    Serial.print("Grasping time DOWN1 from start trial:");
    Serial.println(graspingTime1StartTrial);
    touchDOWN1 = true;
  }

  if (buttonState1 == LOW && touchDOWN1 == true && buttonReleased1 == true) {
    totalTime1ButtonReleased = GetTime(startTime1);
    totalTime1StartTrial = GetTime(startTrialTime);
    Serial.print("Total time DOWN1 from button release:");
    Serial.println(totalTime1ButtonReleased);
    Serial.print("Total time DOWN1 from start trial:");
    Serial.println(totalTime1StartTrial);
    touchDOWN1 = false;
    buttonReleased1 = false;  
    
  }

  // ____________________________________________
  // -------------SECOND BOTTLE----------------
  // ____________________________________________
  // Start record time when button is not pressed
  if (buttonState2 == LOW && (!touchUP2 && !touchDOWN2)) {
  startTime2 = millis();
  Serial.println(startTime2);
  buttonReleased2 = true;
  }

  // Second bottle, up part
  if (touchStateUP2 == HIGH && buttonReleased2 == true && touchUP2 == false && touchDOWN2 == false) {
    graspingTime2ButtonReleased = GetTime(startTime2);
    graspingTime2StartTrial = GetTime(startTrialTime);
    Serial.print("Grasping time UP2 from button release:");
    Serial.println(graspingTime2ButtonReleased);
    Serial.print("Grasping time UP2 from start trial:");
    Serial.println(graspingTime2StartTrial);
    touchUP2 = true;
  }

  if (buttonState2 == LOW && touchUP2 == true && buttonReleased2 == true) {
    totalTime2ButtonReleased = GetTime(startTime2);
    graspingTime2StartTrial = GetTime(startTrialTime);
    Serial.print("Grasping time UP2 from button release:");
    Serial.println(graspingTime2ButtonReleased);
    Serial.print("Grasping time UP2 from start trial:");
    touchUP2 = false;
    buttonReleased2 = false;
    
  }
  // Second bottle, down part

  if (touchStateDOWN2 == HIGH && buttonReleased2 == true && touchDOWN2 == false && touchUP2 == false) {
    graspingTime2ButtonReleased = GetTime(startTime2);
    graspingTime2StartTrial = GetTime(startTrialTime);
    Serial.print("Grasping time DOWN2 from button release:");
    Serial.println(graspingTime2ButtonReleased);
    Serial.print("Grasping time DOWN2 from start trial:");
    Serial.println(graspingTime2StartTrial);
    touchDOWN2 = true;
  }

  if (buttonState2 == LOW && touchDOWN2 == true && buttonReleased2 == true) {
    totalTime2ButtonReleased = GetTime(startTime2);
    graspingTime2StartTrial = GetTime(startTrialTime);
    Serial.print("Total time DOWN2 from button release:");
    Serial.println(totalTime1ButtonReleased);
    Serial.print("Total time DOWN2 from start trial:");
    Serial.println(totalTime1StartTrial);
    touchDOWN2 = false;
    buttonReleased2 = false;  
    
  }
   // Calculate time difference between participants' grasping
  if ((graspingTime1ButtonReleased > 0 && graspingTime2ButtonReleased > 0) && (graspingTime1StartTrial > 0 && graspingTime2StartTrial > 0))
  {
    timeDifferenceButtonReleased = abs(graspingTime1ButtonReleased - graspingTime2ButtonReleased);
    timeDifferenceStartTrial = abs (graspingTime1StartTrial - graspingTime2StartTrial);
    Serial.print("time difference between grasps from button release:");
    Serial.println(timeDifferenceButtonReleased);
    Serial.print("time difference between grasps from start trial:");
    Serial.println(timeDifferenceStartTrial);
    isConsecutive(timeDifferenceStartTrial,n_outside,n_within,timeWin);
    changeTimeWin(timeDifferenceStartTrial,n_outside,n_within,timeWin);
    graspingTime1ButtonReleased = 0;
    graspingTime2ButtonReleased = 0;
    graspingTime1StartTrial = 0;
    graspingTime2StartTrial = 0;
    
  }
}
