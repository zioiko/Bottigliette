// First participant's variable initialization
const int buttonPin1 = 7;
const int touchPinUP1 = 3;
const int touchPinDOWN1 = 2;

bool touchUP1 = false;
bool touchDOWN1 = false;
bool buttonReleased1 = false;
unsigned long startTime1;
unsigned long graspingTime1;
unsigned long totalTime1;

// Second participant's variable initialization
const int buttonPin2 = 8;
const int touchPinUP2 = 5;
const int touchPinDOWN2 = 4;

bool touchUP2 = false;
bool touchDOWN2 = false;
bool buttonReleased2 = false;
unsigned long startTime2;
unsigned long graspingTime2;
unsigned long totalTime2;

// Other variables initialization
unsigned long timeDifference;
unsigned long timeWin = 0.25; //initialize time window: 250 ms
int n_outside = 0; // Counter for number of consecutive trials where timeDifference is outside time window
int n_within = 0; // Counter for number of consecutive trials where timeDifference is within time window
bool b1 = false; //condition for button1 released
bool b2 = false; //condition for button2 released
bool isPressed1 = false; // condition for button 1 press
bool isPressed2 = false; // condition for button 2 press
bool isNotPressed1 = false;
bool isNotPressed2 = false;
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
    delay(500);

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

  // ____________________________________________
  // ----------------FIRST BOTTLE----------------
  // ____________________________________________
  // Start record time when button is not pressed
  if (buttonState1 == LOW && (!touchUP1 && !touchDOWN1)) {
  startTime1 = millis();
  buttonReleased1 = true;
  b1 = true;
  delay(10);
  }

  if (b1 && buttonState1 == HIGH) { //Start soggetto 1
    Serial.println("Button 1 released");
    b1 = false;
  }

  // First bottle, up part
  if (touchStateUP1 == HIGH && buttonReleased1 == true && touchUP1 == false) {
    graspingTime1 = GetTime1(startTime1);
    Serial.print("Grasping time UP1:");
    Serial.println(graspingTime1);
    touchUP1 = true;
  }

  if (buttonState1 == LOW && touchUP1 == true && buttonReleased1 == true) {
    totalTime1 = GetTime1(startTime1);
    Serial.print("Total time UP1:");
    Serial.println(totalTime1);
    touchUP1 = false;
    buttonReleased1 = false;
    
  }
  // First bottle, down part

  if (touchStateDOWN1 == HIGH && buttonReleased1 == true && touchDOWN1 == false) {
    graspingTime1 = GetTime1(startTime1);
    Serial.print("Grasping time DOWN1:");
    Serial.println(graspingTime1);
    touchDOWN1 = true;
  }

  if (buttonState1 == LOW && touchDOWN1 == true && buttonReleased1 == true) {
    totalTime1 = GetTime1(startTime1);
    Serial.print("Total time DOWN1:");
    Serial.println(totalTime1);
    touchDOWN1 = false;
    buttonReleased1 = false;  
    
  }
  

  // ____________________________________________
  // -------------SECOND BOTTLE----------------
  // ____________________________________________
  // Start record time when button is not pressed
  if (buttonState2 == LOW && (!touchUP2 && !touchDOWN2)) {
  startTime2 = millis();
  //Serial.println(startTime2);
  buttonReleased2 = true;
  b2 = true;
  delay(10);
  }

  if (b2 && buttonState2 == HIGH) { //Start soggetto 2
    Serial.println("Button 2 released");
    b2 = false;
  }

  // Second bottle, up part
  if (touchStateUP2 == HIGH && buttonReleased2 == true && touchUP2 == false) {
    graspingTime2 = GetTime2(startTime2);
    Serial.print("Grasping time UP2:");
    Serial.println(graspingTime2);
    touchUP2 = true;
  }

  if (buttonState2 == LOW && touchUP2 == true && buttonReleased2 == true) {
    totalTime2 = GetTime2(startTime2);
    Serial.print("Total time UP2:");
    Serial.println(totalTime2);
    touchUP2 = false;
    buttonReleased2 = false;
    
    
  }
  // Second bottle, down part

  if (touchStateDOWN2 == HIGH && buttonReleased2 == true && touchDOWN2 == false) {
    graspingTime2 = GetTime2(startTime2);
    Serial.print("Grasping time DOWN2:");
    Serial.println(graspingTime2);
    touchDOWN2 = true;
  }

  if (buttonState2 == LOW && touchDOWN2 == true && buttonReleased2 == true) {
    totalTime2 = GetTime2(startTime2);
    Serial.print("Total time DOWN2:");
    Serial.println(totalTime2);
    touchDOWN2 = false;
    buttonReleased2 = false;  
    
    
  }
  
   // Calculate time difference between participants' grasping
  if (graspingTime1 > 0 && graspingTime2 > 0)
  {
    timeDifference = abs(graspingTime1 - graspingTime2);
    Serial.print("time difference between grasps:");
    Serial.println(timeDifference);
    isConsecutive(timeDifference,n_outside,n_within,timeWin);
    changeTimeWin(timeDifference,n_outside,n_within,timeWin);
    graspingTime1 = 0;
    graspingTime2 = 0;
  }

  // Send info on grasping state
 if (buttonState1 == LOW && isPressed1 == false ) 
 {
    Serial.println("Button 1 pressed");
    isPressed1 = true;
    isNotPressed1=false;
 }
  if (buttonState1 == HIGH && isNotPressed1 == false) {
  Serial.println("Button 1 not pressed");
  isNotPressed1 = true;
  isPressed1 = false;
 }
  if (buttonState2 == LOW && isPressed2 == false ) 
 {
    Serial.println("Button 2 pressed");
    isPressed2 = true;
    isNotPressed2=false;
 }
  if (buttonState2 == HIGH && isNotPressed2 == false) {
  Serial.println("Button 2 not pressed");
  isNotPressed2 = true;
  isPressed2 = false;
 }
}
