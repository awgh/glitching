import serial
import binascii
import threading
import time

class Guesser():
  def __init__(self, *args):
    self.t0 = time.clock()
  
  def testStarted(self):
    self.testStartedT = time.clock()
  
  def glitchStarted(self):
    self.glitchStartedT = time.clock()
    
  def testEnded(self, result):
    self.testEndedT = time.clock()
    self.result = result
    self.resultOK = (result == 0x00008000)
    
  def glitchEnded(self, holdoff, holdon):
    self.holdon = holdon
    self.holdoff = holdoff
    self.glitchEndedT = time.clock()
  
  def printReport(self):
    self.t1 = self.testStartedT - self.t0
    print 'Test Started  : ' + str(self.t1)
    print 'Glitch Started: ' + str(self.glitchStartedT - self.t1)
    print 'Test Ended    : ' + str(self.testEndedT - self.t1)
    print 'Glitch Ended  : ' + str(self.glitchEndedT - self.t1)
    if self.resultOK:
      print 'Result OK'
    elif self.result == 'REBOOT':
      print 'REBOOT'
    elif self.result == 'HUNG':
      print 'HUNG'
    else:
      print 'RESULT CORRUPT! '+str(self.result)

    
    print 'Hold Off: ' + str(self.holdoff)
    print 'Hold On : ' + str(self.holdon)     
      
    #print 'Glitch Duration Overall: ' + str(self.glitchEndedT - self.glitchStartedT)
    #print 'Glitch Duration Overhead: ' + str(self.glitchEndedT - self.glitchStartedT - (self.holdoff * (1/200000000)))
    
  def guess(self):
    guesses = {}
    guesses['holdoff'] = int(self.holdoff)
    if self.result == 'REBOOT':
      guesses['holdon'] = int(self.holdon * 0.9)
    elif self.result == 'HUNG':
      guesses['holdon'] = int(self.holdon * 0.9)
    else:
      guesses['holdon'] = int(self.holdon)
    return guesses

class Glitcher():
  #glitchPort = '/dev/tty.usbmodem121081'
  glitchPort = 'COM4'
  input = ''
  
  # Glitch config values
  #polarity = 0
  #holdon = 0xFA
  #holdoff = 0xFE
  # tempvars
  
  def __init__(self, *args):
    try:
      self.glitchSerial = serial.Serial(self.glitchPort, 9600, timeout=1)      
    except Exception, msg:
      print msg
      exit()
      
  def __del__(self):
    self.glitchSerial.close()
  
  def linefeed(self, numlines):
    self.input = ''
    for i in range(0, numlines):
      self.input += self.glitchSerial.readline()
    #print self.input          

  def isReady(self):
    self.glitchSerial.write('0') # write bogus char to show menu
    self.linefeed(6)
    return self.input.find('Choose an option') != -1
  
  def configure(self, polarity, holdoff, holdon):
    self.polarity = polarity
    self.holdoff = holdoff
    self.holdon = holdon
    # set polarity
    setlow = (self.input.find('Starts Low') != -1)
    if (setlow and polarity != 0) or ((not setlow) and polarity == 0): 
      self.glitchSerial.write('1')  
      self.linefeed(6)
    
    # set hold_off
    self.glitchSerial.write('2')
    self.linefeed(1)
    self.glitchSerial.write("{:0>16x}".format(holdoff))    
    self.linefeed(6)
    
    # set hold_on
    self.glitchSerial.write('3')
    self.linefeed(1)
    self.glitchSerial.write("{:0>16x}".format(holdon))
    self.linefeed(6)    
  
  def glitch(self, updateGuesser=True):
    # start glitch    
    self.glitchSerial.write('4')
    if updateGuesser:
      guesser.glitchStarted()
    self.linefeed(1)
    while self.input.find('Completed') == -1:
      self.linefeed(1)
    if updateGuesser:    
      guesser.glitchEnded(self.holdoff, self.holdon)
    
class Target():
  targetPort = 'COM8'
  input = ''
  def __init__(self, *args):
    try:
      self.targetSerial = serial.Serial(self.targetPort, 1843200, timeout=1)      
    except Exception, msg:
      print msg
      exit()
      
  def __del__(self):
    self.targetSerial.close()
    
  def linefeed(self, numlines):
    self.input = ''
    for i in range(0, numlines):
      self.input += self.targetSerial.readline()
    #print self.input    

  def isReady(self):
    # Connect to tests in the target
    self.targetSerial.write(' ') # write a space to show the menu
    self.linefeed(6)
    return self.input.find('0 - AES256') != -1

  def runTest(self, test2run):
    # Configure the test
    if test2run == 0:
      self.targetSerial.write('0')       # for AES256
      print self.targetSerial.readline()
      self.targetSerial.write('100000\n')  # for loop count
      print self.targetSerial.readline()
      self.targetSerial.write( binascii.unhexlify('00112233445566778899AABBCCDDEEFF') )
      #Plaintext 00112233445566778899AABBCCDDEEFF
      #Ciphertext D83414223D20A0C928B136C884D07EA2
      #Result 0x00000000
      for i in range(0,6):
        print self.targetSerial.readline()
    elif test2run == 1:
      self.targetSerial.write('1')       # for loop test
      print self.targetSerial.readline()
      self.targetSerial.write('100000\n')  # for loop count
      print self.targetSerial.readline()
    elif test2run == 6:
      self.targetSerial.write('6')       # for branch test      
      self.linefeed(1)
      guesser.testStarted()      
      self.targetSerial.write('4294967295\n')  # for loop count
      self.linefeed(1)

      hangCounter = 0
      while self.input.find('Result') == -1:
        # check for reboot
        if self.input.find('SS=') != -1:
          guesser.testEnded('REBOOT')
          self.linefeed(6)          
          return
        else:
          hangCounter += 1 # timeout set to 1 sec, so this is number of secs hung
          if(hangCounter > 5):
            guesser.testEnded('HUNG')
            return
        self.linefeed(1)
      guesser.testEnded(int(self.input.split()[1], base=16))      

    
class TargetThread(threading.Thread):
  def __init__(self, target):
    self.target = target
    threading.Thread.__init__(self)
  def run(self):    
    self.target.runTest(6)

class GlitchThread(threading.Thread):
  def __init__(self, glitch):
    self.glitch = glitch
    threading.Thread.__init__(self)
  def run(self):    
    self.glitch.glitch()

glitch = Glitcher()
target = Target()
guesser = Guesser()

def rebootOnPurpose():
  global guesser, glitch, target
      
  if not glitch.isReady():
    print 'Glitcher in bad state.'
    exit()   

  old_hoff = glitch.holdoff
  old_hon = glitch.holdon
  glitch.configure(0, 0, 50000) # known-bad value hardcoded, should be an argument  
  glitch.glitch(updateGuesser=False)
  glitch.holdoff = old_hoff
  glitch.holdon = old_hon
  time.sleep(5)

  target.linefeed(6)
  if target.input.find('SS=') != -1:
    print 'Target Rebooted Successfully'
  else:
    print 'TARGET REBOOT FAILED!'
    exit()

  
    
def solveNonRebootingHoldoff():
  global guesser, glitch, target
  done = False
  firstTime = True

  while not done:
    if not firstTime:
      guesses = guesser.guess()
      
    if not glitch.isReady():
      print 'Glitcher in bad state.'
      exit()   
    if not target.isReady():
      print 'Target in bad state.'
      exit()
  
    if firstTime:
      glitch.configure(0, 0xFA7, 11620)  
    else:
      glitch.configure(0, guesses['holdoff'], guesses['holdon'])  

    glitchThread = GlitchThread(glitch)
    targetThread = TargetThread(target)
    glitchThread.start()
    time.sleep(1)
    targetThread.start()  
  
    glitchThread.join()
    targetThread.join()
  
    guesser.printReport()  
    firstTime = False
    
    if guesser.result != 'REBOOT':
      if guesser.result == 'HUNG':
        rebootOnPurpose()
        
      else:
        done = True
  

if __name__ == "__main__":

  print 'started'
  solveNonRebootingHoldoff()
  
  
  #glitch = Glitcher()
  #if not glitch.isReady():
    #print 'Glitcher in bad state.'
    #exit()
    
  ## 0.000000005 seconds = 5ns = 1 tick @ 200 Mhz
  
  #hoff = 0.00125228282729 / 0.000000005
  #print 'div = ' + str(hoff)
  #glitch.configure(0, 0xFF, 0xFFFFFFF)  
  
  #target = Target()
  #if not target.isReady():
    #print 'Target in bad state.'
    #exit()
  
  
  #glitch.start()
  #time.sleep(2)
  #target.start()  
  ##time.sleep(0.01)
  
  #glitch.join()
  #target.join()

  #guesser.printReport()  

  #del glitch
  #del target
  
## start of inductive step
  #guesses = guesser.guess()
  #guesser = Guesser()
  #glitch = Glitcher()
  #if not glitch.isReady():
    #print 'Glitcher in bad state.'
    #exit()
  #target = Target()    
  #if not target.isReady():
    #print 'Target in bad state.'
    #exit()
  
  #glitch.configure(0, guesses['holdoff'], guesses['holdon'])  
  #glitch.start()
  #time.sleep(2)
  #target.start()  

  #glitch.join()
  #target.join()

  #guesser.printReport()  
  