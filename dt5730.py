#/ \file    CLEAR_March/DT5730/clear/dt5730.py
#/ \brief   Implementation of the DT5730 control + data acquisition
#/ \author  Pietro Grutta (pietro.grutta@pd.infn.it)
from logger import *
from caendt5730 import *
from rootconverter import *
import matplotlib.pyplot as plt
import time
import queue
import signal
import threading
from collections import deque
from os.path import exists
import pickle
from datetime import datetime


##############################################################
######## globals #############################################
##############################################################
# Counter of the ROOT file number
runID = 0
# Counter for the cumulative number of events in this session
eventID = 0
## ROOT
# Filename of the ROOT files
daqStartTime = datetime.now()
rFilename = daqStartTime.strftime("%d%H%M%S_") + "DT5730_run"
rPath = "/home/pietro/work/CLEAR_March/DT5730/data/"
# List of ROOT processed data files
rProcessedSession = []
## Status of the data saving thread
rootDumpStatus = True
# FIFO object to display the last 500 in a plot (not the best solution, but it's 5:00 and I'm tired)
traceAvgQSize = 500
traceAvgQ_FIFO = deque(maxlen = traceAvgQSize)


##############################################################
######## runCache ############################################
##############################################################
# Check cache about the list of already processed FERS datafiles (to ROOT)
def checkCache(cache_fname = "/home/pietro/work/CLEAR_March/cache_dt5730.dat"):
    runID = 0
    eventID = 0
    if exists(cache_fname):
        # Gather data from the file
        with open(cache_fname, 'rb') as infile:
            # Read back payload from file
            payload = pickle.load(infile)
            runID = payload[0] + 1
            eventID = payload[1] + 1
            logging.info(f"runList: Read from file runList.dat : OK")
    else:
        logging.warning(f"No cache present.")
    return (runID, eventID)

# Save cache file
def dumpCache(cache_fname = "/home/pietro/work/CLEAR_March/cache_dt5730.dat"):
    # Get run filename without extentions from the path like.
    # For example: _extractFilename(/home/pietro/work/CLEAR_March/FERS/Janus_3.0.3/bin/MsgLog.txt) -> MsgLog.txt
    def _extractFilename(path: str):
        idx = path.rfind('/')
        if idx > 0 :
            return path[idx+1:] 
        else:
            return path
    #   
    # Save runList of the processed ROOT files on file
    with open(cache_fname, 'wb') as outfile:
        # Read back payload from file
        payload = [runID, eventID]
        pickle.dump(payload, outfile)
        logging.info(f"File {cache_fname} saved : OK")
    # Print stats of the converted ROOT files
    logging.info("--------------------------------------")
    logging.info("Summary of the files converted to ROOT in this session")
    for i, item in enumerate(rProcessedSession):
        logging.info(f"{i} : {_extractFilename(item)}")
    logging.info("--------------------------------------")
    # Greetings
    logging.critical("Goodbye :)")


# Check for the existence of cache to resume runID
runID, eventID = checkCache()


##############################################################
######## Setup ###############################################
##############################################################
# Event readout queue buffer
eventsReadout = queue.Queue()

# Instance the CAENDT5730 controller class
dgt = CAENDT5730(usbLinkID = 2, evtReadoutQueue = eventsReadout, eventCutoff=-1)
# Open digitizer
dgt.open()
# Setup digitizer
dgt.setupSimple(windowSize_s = 50e-6, triggerThres_V = 1.5, channelDCOffset_V = 0.) 
#dgt.testClassWaveform(50)
#exit(0)



# Instance the ROOT file writer
diskWriter = rootconverter(path=rPath, jobEvents=1000, dgtCalibration = [0.00012782984648295086,-1.0470712607404515], periodTrg=500)


# Handle exit signal.
# It closes the acquisition and writes the last events that have been acquired
def handler_SIGINT(signum, frame):
    print()
    logging.critical("Exit signal")
    # Send internal command to the acquisition class
    dgt.daqLoop = False
    # Wait for the last event to be putted in the buffer
    producer_thread.join()
    # Send internal command to the writer class
    rootDumpStatus = False
    # Wait for the last event to to written on disk
    consumer_thread.join()
    # Dump cache file
    dumpCache()
    
    # Goodbye :3
    green = "\x1b[32;1m"
    reset = "\x1b[0m"
    from random import randint as rnd
    messageList = ["Goodbye :3", "See you later :)", "It has been nice °o°", "I'm tired :("]
    message = messageList[rnd(0, len(messageList))]
    print(f"[{time.strftime('%H:%M:%S')}] {green}GOODBYE{reset} - {message}")
    
    # Close plot
    #try:
    #    plt.close()
    #except:
    #    logging.warning("Plot close generated an exception")
    
    # Exit the program
    producer_thread.join()
    consumer_thread.join()
    logging.info("Application exit state reached")
    exit(0)
    
    
# Register the SIGINT signal as an interrupt
signal.signal(signal.SIGINT, handler_SIGINT)


# Print the report about the ROOT file converted in this session
def reportCache():
    pass

# DT5730 thread for the acquisition loop
def acquireLoop():
    global dgt
    # Open acquisition
    dgt.openAcquire()
    # Close acquisition
    dgt.closeAcquire()
    # Close digitizer
    dgt.shutdownDigitizer()


# ROOT data writing thread to store data
def diskDumpLoop():
    global traceAvgQ_FIFO
    global runID
    global rootDumpStatus 
    while rootDumpStatus:
        # If the acquisition has been closed definitely then you have to exit this tread        
        #logging.debug("diskDumpLoop - loop")
        # Prepare the ROOT file for this run
        rfname = datetime.now().strftime("%d%H%M%S_") + f"DT5730_run{runID}.root"
        diskWriter.prepareROOT(rfname)
        # Update the RunID
        #diskWriter.updateRunID(runID)
        # Save on file the setup of the digitizer
        diskWriter.processRunInfo(dgt.boardInfo)
        # 
        #print("queue contains", eventsReadout.qsize())
        while not diskWriter.isRunClosed():
            #logging.debug("diskDumpLoop - Getting item from queue")
            # Get item from the queue
            bufferItem = eventsReadout.get()
            # The None signal in the queue is generated when exit signal is listened
            if bufferItem is None:
                #logging.debug("None signal. Acquisition is closed")
                rootDumpStatus = False
                break
            else:
                # Get item from the queue and put in the ROOT file
                #print("Queue size is ", eventsReadout.qsize())
                eventInfo, eventData, runFirstTrgTime = bufferItem
                diskWriter._dsp_storeEventROOT(eventInfo, eventData, runFirstTrgTime)
                # Put the last calculated avgQ in the FIFO buffer (notice that it is in pC rather than nC)
                traceAvgQ_FIFO.append(diskWriter.avgV)
                
            if diskWriter.isRunClosed():
                runID += 1
                break        
        # Close the ROOT file
        diskWriter.closeROOT()
        rProcessedSession.append(rfname)
    logging.debug("diskDumpLoop reached end")



# Create the DT5730 readout thread
producer_thread = threading.Thread(target=acquireLoop)
# start the producer thread
producer_thread.start()

# Before creating the consumer thread, wait until the digitizer is ready to acquire...
while not (dgt.dgtConfigured==True and dgt.daqLoop==True and dgt.acquisitionMode==True):
    pass
logging.debug("Digitizer configured. Starting disk saving routine")

# Create the data saving thread
consumer_thread = threading.Thread(target=diskDumpLoop)
# start the file writing on disk
consumer_thread.start()



## Diagnostic for the data acquisition, beside event rate 
# Plotting trace over 500 events (at 10Hz we've a trace plot of 50 seconds)
# Note: this function runs in the main thread, however there is no dead times in acq. or file saving
# given that they run on parallel threads
while dgt.daqLoop and rootDumpStatus:       
    plt.title(f"Trace plot Bergoz [{traceAvgQSize} points]")
    plt.xlabel("Time [trigger units]")
    plt.ylabel("THz Bergoz [pC])")
    plt.plot(traceAvgQ_FIFO)                        # The plot has pC on the vertical axis!
    #plt.ylim(-1,100)                                # Fix the range for the typical charges (<100pC) we'll use
    
    # Calculate avg and std deviation over the N=traceAvgQSize events
    avgThz = np.mean(traceAvgQ_FIFO)
    #logging.info(avgThz)
    stdThz = np.std(traceAvgQ_FIFO)
    plt.text(0.1, 0.80, f"Avg. beam charge \n Avg: {avgThz:>6.3f} pC/train \n Std: {stdThz:>6.3f} pC/train")
    #
    # Draw, pause, clear
    plt.draw()
    plt.pause(0.1)
    plt.clf()


# Join all the threads
producer_thread.join()
consumer_thread.join()
logging.info("Application exit state reached")