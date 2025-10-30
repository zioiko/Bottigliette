// First participant's variable initialization
const int buttonPin1 = 4;
const int touchPinUP1 = 3;
const int touchPinDOWN1 = 5;

bool touchUP1 = false;
bool touchDOWN1 = false;
bool buttonReleased1 = false;
unsigned long startTime1;
unsigned long graspingTime1;
unsigned long totalTime1;

// Second participant's variable initialization
const int buttonPin2 = 7;
const int touchPinUP2 = 6;
const int touchPinDOWN2 = 8;

bool touchUP2 = false;
bool touchDOWN2 = false;
bool buttonReleased2 = false;
unsigned long startTime2;
unsigned long graspingTime2;
unsigned long totalTime2;

// Other variables initialization
unsigned long timeDifference;
unsigned long timeWin = 0.25; //initialize time window: 250 ms
int n_otuside = 0; // Counter for number of consecutive trials where timeDifference is outside time window
int n_within = 0; // Counter for number of consecutive trials where timeDifference is within time window
// Utily functions

  unsigned long GetTime1(unsigned long startTime1)
  {
    return millis() - startTime1;
  }

 unsigned long GetTime2(unsigned long startTime2)
 {
   return millis() - startTime2;
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

 int isConsecutive(unsigned long timeDifference, int n_outside, int n_within, unsigned long timeWin)
 {
  if (timeDifference <= timeWin) 
  {
    n_within = n_within + 1;
      if (n_within == 2)
    {
      reduceTimeWin();
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
     n_outside = n_outside + 1;
     if (n_outside == 2)
     {
      incrementTimeWin();
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
 pinMode(buttonPin1,INPUT);
 pinMode(touchPinUP1,INPUT);
 pinMode(touchPinDOWN1,INPUT);
 pinMode(buttonPin2,INPUT);
 pinMode(touchPinUP2,INPUT);
 pinMode(touchPinDOWN2,INPUT);

}

void loop() {
  int buttonState1 = digitalRead(buttonPin1);
  int touchStateUP1 = digitalRead(touchPinUP1);
  int touchStateDOWN1 = digitalRead(touchPinDOWN1);
  int buttonState2 = digitalRead(buttonPin1);
  int touchStateUP2 = digitalRead(touchPinUP1);
  int touchStateDOWN2 = digitalRead(touchPinDOWN1);
  // ____________________________________________
  // ----------------FIRST BOTTLE----------------
  // ____________________________________________
  // Start record time when button is not pressed
  if (buttonState1 == HIGH && (!touchUP1 && !touchDOWN1)) {
  startTime1 = millis();
  Serial.print("Start time: ");
  Serial.println(startTime1);
  buttonReleased1 = true;
  }

  // First bottle, up part
  if (touchStateUP1 == HIGH && buttonReleased1 == true && touchUP1 == false) {
    graspingTime1 = GetTime1(startTime1);
    Serial.print("Grasping timeUP: ");
    Serial.println(graspingTime1);
    touchUP1 = true;
  }

  if (buttonState1 == HIGH && touchUP1 == true && buttonReleased1 == true) {
    totalTime1 = GetTime1(startTime1);
    Serial.print("Total time UP: ");
    Serial.println(totalTime1);
    touchUP1 = false;
    buttonReleased1 = false;
    
  }
  // First bottle, down part

  if (touchStateDOWN1 == HIGH && buttonReleased1 == true && touchDOWN1 == false) {
    graspingTime1 = GetTime1(startTime1);
    Serial.print("Grasping time DOWN: ");
    Serial.println(graspingTime1);
    touchDOWN1 = true;
  }

  if (buttonState1 == HIGH && touchDOWN1 == true && buttonReleased1 == true) {
    totalTime1 = GetTime1(startTime1);
    Serial.print("Total time DOWN: ");
    Serial.println(totalTime1);
    touchDOWN1 = false;
    buttonReleased1 = false;  
    
  }

  // ____________________________________________
  // -------------SECOND BOTTLE----------------
  // ____________________________________________
  // Start record time when button is not pressed
  if (buttonState2 == HIGH && (!touchUP2 && !touchDOWN2)) {
  startTime2 = millis();
  Serial.print("Start time: ");
  Serial.println(startTime2);
  buttonReleased2 = true;
  }

  // Second bottle, up part
  if (touchStateUP2 == HIGH && buttonReleased2 == true && touchUP2 == false) {
    graspingTime2 = GetTime2(startTime2);
    Serial.print("Grasping timeUP: ");
    Serial.println(graspingTime2);
    touchUP2 = true;
  }

  if (buttonState2 == HIGH && touchUP2 == true && buttonReleased2 == true) {
    totalTime2 = GetTime2(startTime2);
    Serial.print("Total time UP: ");
    Serial.println(totalTime2);
    touchUP2 = false;
    buttonReleased2 = false;
    
  }
  // Second bottle, down part

  if (touchStateDOWN2 == HIGH && buttonReleased2 == true && touchDOWN2 == false) {
    graspingTime2 = GetTime2(startTime2);
    Serial.print("Grasping time DOWN: ");
    Serial.println(graspingTime2);
    touchDOWN2 = true;
  }

  if (buttonState2 == HIGH && touchDOWN2 == true && buttonReleased2 == true) {
    totalTime2 = GetTime2(startTime2);
    Serial.print("Total time DOWN: ");
    Serial.println(totalTime2);
    touchDOWN2 = false;
    buttonReleased2 = false;  
    
  }
   // Calculate time difference between participants' grasping
  if (graspingTime1 > 0 && graspingTime2 > 0)
  {
    timeDifference = abs(graspingTime1 - graspingTime2);
    Serial.print("time difference between grasps :");
    Serial.println(timeDifference);
    isConsecutive(timeDifference,n_outside,n_within,timeWin);
    graspingTime1 = 0;
    graspingTime2 = 0;
  }
}
