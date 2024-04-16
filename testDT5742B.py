#/ \file    CLEAR_March/DT5742/clear/testDT5742B.py
#/ \brief   Implementation of the DT5730 control + data acquisition
#/ \author  Pietro Grutta (pietro.grutta@pd.infn.it)
from logger import *
from caendt5742b import *
from rootconverter import *
import queue
from os.path import exists


##############################################################
######## Setup ###############################################
##############################################################
# Event readout queue buffer
eventsReadout = queue.Queue()

# # Determine the usbLinkID of the digitizer
# dgt = CAENDT5742B(usbLinkID = 0, evtReadoutQueue = eventsReadout, eventCutoff=25)
# dgt.autoScan()
# exit()
logging.setLevel("DEBUG")
# # Instance the CAENDT5742B controller class
dgt = CAENDT5742B(usbLinkID = 0, evtReadoutQueue = eventsReadout, eventCutoff=25)
# Open the digitizer, plot waveform and close the digitizer
dgt.testClass(1)


## Instance the CAENDT5742B controller class
#dgt = CAENDT5742B(usbLinkID = 0, evtReadoutQueue = eventsReadout, eventCutoff=25)
## Open digitizer
#dgt.open()
## Setup digitizer
#dgt.setupSimple(windowSize_s = 50e-6, triggerThres_V = 1.5, channelDCOffset_V = 0.) 
#dgt.testClassWaveform(25)
#exit()
