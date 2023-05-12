#/ \file    CLEAR_March/DT5730/clear/testDT5730.py
#/ \brief   Implementation of the DT5730 control + data acquisition
#/ \author  Pietro Grutta (pietro.grutta@pd.infn.it)
from logger import *
from caendt5730 import *
from rootconverter import *
import queue
from os.path import exists


##############################################################
######## Setup ###############################################
##############################################################
# Event readout queue buffer
eventsReadout = queue.Queue()

# Instance the CAENDT5730 controller class
dgt = CAENDT5730(usbLinkID = 2, evtReadoutQueue = eventsReadout, eventCutoff=25)
# Open the digitizer, plot waveform and close the digitizer
dgt.testClass(25)
exit()



## Instance the CAENDT5730 controller class
#dgt = CAENDT5730(usbLinkID = 0, evtReadoutQueue = eventsReadout, eventCutoff=25)
## Open digitizer
#dgt.open()
## Setup digitizer
#dgt.setupSimple(windowSize_s = 50e-6, triggerThres_V = 1.5, channelDCOffset_V = 0.) 
#dgt.testClassWaveform(25)
#exit()
