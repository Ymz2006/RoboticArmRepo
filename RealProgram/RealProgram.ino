
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// called this way, it uses the default address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x41); // 1,2,3
Adafruit_PWMServoDriver pwm0 = Adafruit_PWMServoDriver(0x40); // 4,5,6

#define SERVOMIN  90 // This is the 'minimum' pulse length count (out of 4096)
#define SERVOMAX  465 // This is the 'maximum' pulse length count (out of 4096)

#define SERVOMINGB  95 // This is the 'minimum' pulse length count (out of 4096)
#define SERVOMAXGB  480 // This is the 'maximum' pulse length count (out of 4096)

#define USMIN  600 // This is the rounded 'minimum' microsecond length based on the minimum pulse of 150
#define USMAX  2400 // This is the rounded 'maximum' microsecond length based on the maximum pulse of 600
#define SERVO_FREQ 50 // Analog servos run at ~50 Hz updates

const int BUFFER_SIZE = 100;
char buffer[100];

int t1= 37+360, t2 = 99,t3 = 90,t4 = 90,t5 = 90,t6;
int deg1 = 0, deg2 = 0, deg3 = 0, deg4 = 0, deg5 = 0;

// our servo # counter
uint8_t servonum = 0;

void setup() {

  Serial.begin(9600);

  pwm.begin(); pwm0.begin();
  pwm.setOscillatorFrequency(27000000); pwm0.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(SERVO_FREQ); pwm0.setPWMFreq(SERVO_FREQ);

  delay(10);
}

void setServoPulse(uint8_t n, double pulse) {
  double pulselength;
  
  pulselength = 1000000;   // 1,000,000 us per second
  pulselength /= SERVO_FREQ;   // Analog servos run at ~60 Hz updates
  pulselength /= 4096;  // 12 bits of resolution
  pulse *= 1000000;  // convert input seconds to us
  pulse /= pulselength;
}



int DegToPulse(int deg){
  return map(deg,0,180,SERVOMIN,SERVOMAX);
}
int DegToPulseGB(int deg){
  return map(deg,0,900,SERVOMINGB,SERVOMAXGB);
}


void flash(){
  digitalWrite(LED_BUILTIN, HIGH);  // turn the LED on (HIGH is the voltage level)
  delay(1000);                      // wait for a second
  digitalWrite(LED_BUILTIN, LOW);   // turn the LED off by making the voltage LOW
  delay(1000);    

}

void loop() {

  if (Serial.available() > 0) {
    // read the incoming bytes:
    int rlen = Serial.readBytesUntil('\n', buffer, BUFFER_SIZE);
    String str(buffer);

    for(int i =0; i < rlen;i+=4){
      int n = str.substring(i,i+1).toInt();
      int val = str.substring(i+1,i+4).toInt();

      if(n == 6){
        pwm0.setPWM(6, 0, DegToPulse(val));
        Serial.println(n);
        Serial.println(val);
        
      }
      if(n == 5){
        pwm0.setPWM(5, 0, DegToPulse(val));
        Serial.println(n);
        Serial.println(val);
      }
      if(n == 4){
        pwm0.setPWM(4, 0, DegToPulse(val));
        Serial.println(n);
        Serial.println(val);
      }
      if(n == 3){
        pwm.setPWM(3, 0, DegToPulse(val));
        Serial.println(n);
        Serial.println(val);
        
      }
      if(n == 2){
        pwm.setPWM(2, 0, DegToPulseGB(val));
        Serial.println(n);
        Serial.println(val);
      }
      if(n == 1){
        pwm.setPWM(1, 0, DegToPulseGB(val));
        Serial.println(n);
        Serial.println(val);
      }

    }
    

  }
}
