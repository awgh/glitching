/*
** Glitchcraft Controller
** - targets the Teensy, may have some Teensy-specific code
 */


#define T_CLK    2
#define T_DATA   3
#define GO       4
#define ARMED    5
#define ENABLE   6

int state = 0;


unsigned char hold_off[8];  // ticks to hold device in reset
unsigned char hold_on[8];   // ticks to wait for glitch?
unsigned char polarity = 0;

void setup()
{
  Serial.begin(9600);// Teensy USB is always 12Mbit/sec
  
  pinMode(T_CLK, OUTPUT); 
  pinMode(T_DATA, OUTPUT);
  pinMode(GO, OUTPUT);
  pinMode(ARMED, INPUT);
  pinMode(ENABLE, OUTPUT);

  digitalWrite(T_CLK, LOW);
  digitalWrite(T_DATA, LOW);
  digitalWrite(GO, LOW);
  digitalWrite(ENABLE, LOW);
}

void loop()
{
   switch(state) {
    case 0:
      state = 1;
      main_menu();
      break;
    default:
      break;
   }
   
  if (Serial.available()) {
    char c = Serial.read();
  
    switch(c){
      case '1':
        Serial.println("Toggled Polarity.");
        (polarity == 0) ? polarity = 1 : polarity = 0;
        break;
      case '2':
        Serial.println("Enter 16 Hex Digits for Hold Off (64 bits):");
        for(int i=0; i<8; i++)
        {
          int c = SerialReadHexByte();
          if( c < 0 ) 
          {
            Serial.println("Invalid Character!");
            break;
          }
          else hold_off[i] = c; 
        }
        break;
      case '3':
        Serial.println("Enter 16 Hex Digits for Hold On (64 bits):");
        for(int i=0; i<8; i++)
        {
          int c = SerialReadHexByte();
          if( c < 0 ) 
          {
            Serial.println("Invalid Character!");
            break;
          }
          else hold_on[i] = c; 
        }
        break;
      case '4':      
        // ConfigData: hold_off, hold_on, then polarity (MSB->LSB order)

        // To Program Config Data:
        // 1. enable pin high
        digitalWrite(ENABLE, HIGH);
        
        // 2. Clock in Config Data
        Serial.println("Writing Configuration Data...");
        for( int i=0; i<8; i++ )    // each byte
        {
          for( int j=0; j<8; j++ )  // each bit
          {
            digitalWrite( T_DATA, ((hold_off[i] << j) & 0x80) ? HIGH : LOW );
            digitalWrite( T_CLK, HIGH );            
            delay(1);
            digitalWrite( T_CLK, LOW );
          }
        }  
        delay(1);
        for( int i=0; i<8; i++ )    // each byte
        {
          for( int j=0; j<8; j++ )  // each bit
          {
            digitalWrite( T_DATA, ((hold_on[i] << j) & 0x80) ? HIGH : LOW );
            digitalWrite( T_CLK, HIGH );            
            delay(1);
            digitalWrite( T_CLK, LOW );          
          }
        }
        delay(1);  
        digitalWrite( T_DATA, polarity ? HIGH : LOW );
        digitalWrite( T_CLK, HIGH );            
        delay(1);
        digitalWrite( T_CLK, LOW );
        Serial.println("Configuration Data Written.");

        // 3. wait for armed to be high in loop
        while( digitalRead(ARMED) == LOW ) 
        {
          digitalWrite( T_CLK, HIGH );            
          delay(1);
          digitalWrite( T_CLK, LOW );
          Serial.print(".");          
        }
        Serial.println("");
        Serial.println("ARMED!!!");
        
        // 4. set go high to start glitch
        delay(1);
        digitalWrite( GO, HIGH );
        Serial.println("FIRING!!!");
        while( digitalRead(ARMED) == HIGH ) 
        {         
          delay(1000);
          Serial.println("Running..."); 
        }
        Serial.println("Completed!  Resetting...");        
        digitalWrite( GO, LOW );
        delay(1);
        digitalWrite(ENABLE, LOW);
        delay(1);
        digitalWrite( T_CLK, HIGH );  // have to clock once more after bringing enable low            
        delay(1);
        digitalWrite( T_CLK, LOW );

        break;
      default:
        Serial.println("");      
        break;
    }
    state = 0;
  }   
}

void main_menu()
{
  Serial.print("1. Polarity: ");
  if(polarity)
    Serial.println("Starts High");
  else Serial.println("Starts Low");
  
  Serial.print("2. Hold Off: ");
  for(int i=0; i<7; i++)
    Serial.print( printHexByte(hold_off[i]) );
  Serial.println( printHexByte(hold_off[7]) );
  
  Serial.print("3. Hold On: ");
  for(int i=0; i<7; i++)
    Serial.print( printHexByte(hold_on[i]) );
  Serial.println( printHexByte(hold_on[7]) );

  Serial.println("4. Launch Glitch");
  
  Serial.println("Choose an option: ");
}

String printHexByte(byte b) {
  String tmp = String(b, 16);
  if(tmp.length() < 2)
    tmp = "0" + tmp;
  return tmp;
}

byte WaitAndRead()
{
    while (Serial.available() == 0) {
        // do nothing
    }
    return (byte) Serial.read();
}

int SerialReadHexDigit()
{
    byte c = WaitAndRead();
    if (c >= '0' && c <= '9') {
        return c - '0';
    } else if (c >= 'a' && c <= 'f') {
        return c - 'a' + 10;
    } else if (c >= 'A' && c <= 'F') {
        return c - 'A' + 10;
    } else {
        return -1;   // invalid
    }
}

int SerialReadHexByte()
{
    int a = SerialReadHexDigit();
    int b = SerialReadHexDigit();
    if (a<0 || b<0) {
        return -1;  // an invalid hex character was encountered
    } else {
        return (a*16) + b;
    }
}

