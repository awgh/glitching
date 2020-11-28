#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3 as lite
import sys
import serial
import binascii
import threading
import time

import random

class Guesser():
  def __init__(self, *args):
    self.t0 = time.clock()
    self.con = None
    
    try:
        self.con = lite.connect('glitch.sqlite3')
        cur = self.con.cursor()    
        cur.execute('SELECT SQLITE_VERSION()')
        data = cur.fetchone()
        print "SQLite version: %s" % data                
        
    except lite.Error, e:
        print "Error %s:" % e.args[0]
        sys.exit(1)
        
    finally:
        if self.con:
            self.con.close()
  
  def testStarted(self):
    self.testStartedT = time.clock()
  
  def glitchStarted(self):
    self.glitchStartedT = time.clock()
    
  def testEnded(self, result):
    self.testEndedT = time.clock()
    self.result = result
    self.resultOK = (result == 0x00008000)
    
  def glitchEnded(self, holdoff, holdon, targetDelay):
    self.holdon = holdon
    self.holdoff = holdoff
    self.targetDelay = targetDelay
    self.glitchEndedT = time.clock()    
  
  def printReport(self):    
    #hoff = (self.holdoff * 5/1e9)  #hardcoded tick count math here
    #hon = (self.holdon * 5/1e9)  #hardcoded tick count math here
    #self.sqrtError = (self.testStartedT + 5.96788e-5) - (self.glitchStartedT + hoff)
    
    #print 'Glitch started : ' + str(self.glitchStartedT)
    #print 'Hold off in seconds : ' + str(hoff)
    #print 'Hold on in seconds : ' + str(hon)
    #print 'Target Delay in seconds : ' + str(self.targetDelay)
    #print '(testStart + cmdOverhead) : ' + str(self.testStartedT + 5.96788e-5)
    #print '(glitchStart+holdoff) : ' + str(self.glitchStartedT + hoff)    
    #print '(testStart + cmdOverhead) - (glitchStart+holdoff) : ' + str(self.sqrtError)    
    
    #self.error = self.sqrtError * self.sqrtError
    #print 'Error : ' + str(self.error)
    
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
      
  def guess(self):
    guesses = {}
    guesses['holdoff'] = int(self.holdoff)
    if self.result == 'REBOOT':
      # Reboot means we need a shorter glitch pulse
      guesses['holdon'] = int(self.holdon * 0.9)
    elif self.result == 'HUNG':
      # Hang means we need a shorter glitch pulse
      guesses['holdon'] = int(self.holdon * 0.9)
    else:
      guesses['holdon'] = int( (self.holdon * random.random()) + (self.holdon/2) )
    guesses['targetDelay'] = self.targetDelay
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
    print self.input          

  def isReady(self):
    self.glitchSerial.write('0') # write bogus char to show menu
    self.linefeed(6)
    return self.input.find('Choose an option') != -1
  
  def configure(self, polarity, holdoff, holdon, targetDelay):
    self.polarity = polarity
    self.holdoff = holdoff
    self.holdon = holdon
    self.targetDelay = targetDelay
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
      guesser.glitchEnded(self.holdoff, self.holdon, self.targetDelay)
    
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
    print self.input    

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
  glitch.configure(0, 0, 50000, 1) # known-bad value hardcoded, should be an argument  
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
  targetDelay = 0  # this is in seconds

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
      glitch.configure(0, 0, 11620, 0)  
    else:
      glitch.configure(0, guesses['holdoff'], guesses['holdon'], guesses['targetDelay'])  

    glitchThread = GlitchThread(glitch)
    targetThread = TargetThread(target)
    glitchThread.start()
    #time.sleep(targetDelay)
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

def fuzz():
  global guesser, glitch, target
  done = False
  firstTime = True
  targetDelay = 1  # this is in seconds

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
      glitch.configure(0, 0, 11620, 1)  
    else:
      glitch.configure(0, guesses['holdoff'], guesses['holdon'], guesses['targetDelay'])  

    glitchThread = GlitchThread(glitch)
    targetThread = TargetThread(target)
    glitchThread.start()
    time.sleep(targetDelay)
    targetThread.start()  
  
    glitchThread.join()
    targetThread.join()
  
    guesser.printReport()  
    firstTime = False
    
    if guesser.result != 'REBOOT':
      if guesser.result == 'HUNG':
        rebootOnPurpose()
      #else:
      #  done = True

if __name__ == "__main__":
  print 'started'
  #solveNonRebootingHoldoff()
  fuzz()