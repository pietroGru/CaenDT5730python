from ctypes import c_int, c_float, c_void_p, c_char_p, c_char, c_ushort, pointer, cdll, cast, POINTER, byref, Structure, c_uint32, c_long, c_int32, c_int16
import numpy as np
import time
import queue
from logger import *

##############################################################
######## CAENDT5730 class ####################################
##############################################################
class CAENDT5730():
    ### Data structures
    # Board info
    class CAEN_DGTZ_BoardInfo_t(Structure):
        _fields_ = [
            ("ModelName",               12 * c_char),
            ("Model",                   c_uint32),
            ("Channels",                c_uint32),
            ("FormFactor",              c_uint32),
            ("FamilyCode",              c_uint32),
            ("ROC_FirmwareRel",         20 * c_char),
            ("AMC_FirmwareRel",         40 * c_char),
            ("SerialNumber",            c_uint32),
            ("MezzanineSerNum",         4 * 8 * c_char),
            ("PCB_Revision",            c_uint32),
            ("ADC_NBits",               c_uint32),
            ("SAMCorrectionDataLoaded", c_uint32),
            ("CommHandle",              c_int),
            ("VMEHandle",               c_int),
            ("License",                 17 * c_char)]
        # Print info on screen
        def print(self):
            logging.info(f"ModelName                  {self.ModelName}")
            logging.info(f"Model                      {self.Model}")
            logging.info(f"Channels                   {self.Channels}")
            logging.info(f"FormFactor                 {self.FormFactor}")
            logging.info(f"FamilyCode                 {self.FamilyCode}")
            logging.info(f"ROC_FirmwareRel            {self.ROC_FirmwareRel}")
            logging.info(f"AMC_FirmwareRel            {self.AMC_FirmwareRel}")
            logging.info(f"SerialNumber               {self.SerialNumber}")
            logging.info(f"MezzanineSerNum            {self.MezzanineSerNum}")
            logging.info(f"PCB_Revision               {self.PCB_Revision}")
            logging.info(f"ADC_NBits                  {self.ADC_NBits}")
            logging.info(f"SAMCorrectionDataLoaded    {self.SAMCorrectionDataLoaded}")
            logging.info(f"CommHandle                 {self.CommHandle}")
            logging.info(f"VMEHandle                  {self.VMEHandle}")
            logging.info(f"License                    {self.License}")
        def getBrdInfo(self):
            brdInfo = [
                ("ModelName", self.ModelName.decode('utf-8')),
                ("Model", f"{self.Model}"),
                ("Channels", f"{self.Channels}"),
                ("FormFactor", f"{self.FormFactor}"),
                ("FamilyCode", f"{self.FamilyCode}"),
                ("ROC_FirmwareRel", self.ROC_FirmwareRel.decode('utf-8')),
                ("AMC_FirmwareRel", self.AMC_FirmwareRel.decode('utf-8')),
                ("SerialNumber", f"{self.SerialNumber}"),
                ("MezzanineSerNum", self.MezzanineSerNum.decode('utf-8')),
                ("PCB_Revision", f"{self.PCB_Revision}"),
                ("ADC_NBits", f"{self.ADC_NBits}"),
                ("SAMCorrectionDataLoaded", f"{self.SAMCorrectionDataLoaded}"),
                ("CommHandle", f"{self.CommHandle}"),
                ("VMEHandle", f"{self.VMEHandle}"),
                ("License", self.License.decode('utf-8'))]
            return brdInfo
    # Event info
    class CAEN_DGTZ_EventInfo_t(Structure):
        _fields_ = [
            ("EventSize",         c_uint32),
            ("BoardId",           c_uint32),
            ("Pattern",           c_uint32),
            ("ChannelMask",       c_uint32),
            ("EventCounter",      c_uint32),
            ("TriggerTimeTag",    c_uint32) ]
        # Print info on screen
        def print(self):
            logging.info(f"EventSize      {self.EventSize}")
            logging.info(f"BoardId        {self.BoardId}")
            logging.info(f"Pattern        {self.Pattern}")
            logging.info(f"ChannelMask    {self.ChannelMask}")
            logging.info(f"EventCounter   {self.EventCounter}")
            logging.info(f"TriggerTimeTag {self.TriggerTimeTag}")
        # Convert the structure to a dictionary
        def toDict(self):
            result = {
                "EventSize"         : self.EventSize,
                "BoardId"           : self.BoardId,
                "Pattern"           : self.Pattern,
                "ChannelMask"       : self.ChannelMask,
                "EventCounter"      : self.EventCounter,
                "TriggerTimeTag"    : self.TriggerTimeTag
            }
            return result
    # Container for the waveform digitized data
    class CAEN_DGTZ_UINT16_EVENT_t(Structure):
        _fields_ = [
            ("ChSize",          64 * c_uint32),
            ("DataChannel",     64 * POINTER(c_int16) )    
        ]
        # Print info on screen
        def print(self, ch = -1):
            # Print all channels samples
            if ch==-1:
                # todo implement me by looking non-empty channels and print the samples
                #for ch in range():
                #    print(f"Samples ch={}")
                pass
            else:
                print(f"Samples ch={ch}")
                samplesNb = self._fields_[0][ch]
                samples = self._fields_[1][ch*samplesNb:(ch+1)*samplesNb]
                print(samples)
    
    ### Variables
    ## Digitizer connection settings
    usbLinkID = c_int(2)                        # Digitizer USB link ID
    handle = c_int()                            # Digitizer unique handler ID for the session
    samplingRate = 500e6                        # 500 MS/s
    dacResolution = 16384                       # 2^14 bit
    boardInfo = None                            # Board info var
    dgtConfigured = False                       # Board setup has been done
    # Digitizer board info
    boardInfo = None
    ## Calibration values [(from DAC to V is just V = m*sample + q)]
    cal_m = 0.00012782984648295086
    cal_q = -1.0470712607404515
    ## Acquisition
    buffer = POINTER(c_char)()                  # Input buffer
    size = c_uint32()                           # Sizeof of the input buffer
    eventInfo = CAEN_DGTZ_EventInfo_t()         # Event info struct
    evtptr = POINTER(c_char)()                  # evtptr char event buffer - I don't remember
    Evt = POINTER(CAEN_DGTZ_UINT16_EVENT_t)()   # evt pointer
    #
    daqLoop = True
    acquisitionMode = True 
    eventCutoff = -1
    
    ### Utils
    # Class for data throughput measurement
    class statsManager():        
        # Variables
        totBufferSize = 0
        totEventNb = 0
        startTime = 0
        dataThro = -1
        eventRate = -1  
        closed = False
        
        def __init__(self) -> None:
            self.startTime = time.time_ns()            
                    
        def __del__(self) -> None:
            print("\n", flush=True)
            
        def update(self, bfrsz, evts, display = -1):
            currentTime = (time.time_ns() - self.startTime)*1e-9
            # Add to the counter for the total data/event transferred
            self.totBufferSize += 4*bfrsz
            self.totEventNb += evts
            # Calculate the throughput
            self.dataThro = self.totBufferSize / currentTime
            self.eventRate = self.totEventNb / currentTime
            #
            # Print option
            if display > 0 and self.totEventNb % display == 0:
                self.printINFO(f"Event rate {self.eventRate:.2f} evt/s ({self.dataThro*1e-6:.3f} MB/s)")
        
        def printINFO(self, message):
            green = "\x1b[32;1m"
            reset = "\x1b[0m"
            header = f"[{time.strftime('%H:%M:%S')}] {green}STATUS{reset} - {message}"
            print(header, end="\r", flush=True)
        
        # Return the event rate
        def getEventRate(self):
            return self.eventRate
        
        # Return the data throughput rate
        def getThroughput(self):
            return self.dataThro

        # Return the total number of events acquired so far
        def getTotalEvents(self):
            return self.totEventNb
  
    def __init__(self, usbLinkID: int, evtReadoutQueue: queue.Queue, libPath = 'libCAENDigitizer.so', eventCutoff=-1) -> None:
        # Load CAENDigitizer library
        self.libCAENDigitizer = cdll.LoadLibrary(libPath)
        # @todo: implement exception handler
        self.usbLinkID = c_int(usbLinkID)
        
        ## ctypes implementation of the functions
        # CAEN_DGTZ_GetInfo.
        # @brief Get digitizer information
        self.CAEN_DGTZ_GetInfo = self.libCAENDigitizer.CAEN_DGTZ_GetInfo
        self.CAEN_DGTZ_GetInfo.argtypes = [c_int, POINTER(self.CAEN_DGTZ_BoardInfo_t)]
        self.CAEN_DGTZ_GetInfo.restype = c_long 
        # CAEN_DGTZ_GetEventInfo
        # @brief Get event information
        self.CAEN_DGTZ_GetEventInfo = self.libCAENDigitizer.CAEN_DGTZ_GetEventInfo
        self.CAEN_DGTZ_GetEventInfo.argtypes = [c_int, POINTER(c_char), c_uint32, c_int32, POINTER(self.CAEN_DGTZ_EventInfo_t), POINTER(POINTER(c_char))]
        self.CAEN_DGTZ_GetEventInfo.restype = c_long
        
        # Thread-safe queue with events readout
        self.eventReadout = evtReadoutQueue
        # Close digitizer after cutoff is reached (mainly for debugging)
        self.eventCutoff = eventCutoff
        if self.eventCutoff > 0:
            logging.warning(f"Event cutoff set. The readout will stop after {self.eventCutoff} events!")
    
    # Open the digitizer and retrieve information about the boards
    def open(self):
        # Open the digitizer and store the handler ID
        ret = self.libCAENDigitizer.CAEN_DGTZ_OpenDigitizer(0, self.usbLinkID, 0, 0, byref(self.handle))
        if ret!=0:
            logging.critical("CAEN_DGTZ_OpenDigitizer failed.")
            exit()
        else:
            logging.debug("CAEN_DGTZ_OpenDigitizer OK")
        
        # Get board information
        self.boardInfo = self.CAEN_DGTZ_BoardInfo_t()
        ret = self.CAEN_DGTZ_GetInfo(self.handle, byref(self.boardInfo))
        if ret!=0:
            logging.critical("CAEN_DGTZ_GetInfo failed.")
        else:
            logging.debug("CAEN_DGTZ_GetInfo OK")
            (self.boardInfo).print()
            
    # Setup the digitizer 
    # Here I follow the same order of the WaveDump.C setup
    def setup(self, recordlength = 163830, triggerThreshold = 8196, postTriggerSize = 99, maxNumEventsBLT = 1024, channelDCOffset = 32767):
        ret = self.libCAENDigitizer.CAEN_DGTZ_Reset(self.handle)                                                        # Reset Digitizer
        ret |= self.libCAENDigitizer.CAEN_DGTZ_Calibrate(self.handle)                                                   # Calibrate the digitizers
        time.sleep(0.100) #may be useful
        #
        recordLen = c_uint32(recordlength)
        ret |= self.libCAENDigitizer.CAEN_DGTZ_SetRecordLength(self.handle, recordLen)                                  # Set the lenght of each waveform (in samples) (1sample = 2ns) [7us+ 2x4us + 30us = 45us -> 22500 samples / 150000 samples = 300us]
        ret |= self.libCAENDigitizer.CAEN_DGTZ_GetRecordLength(self.handle, byref(recordLen))                           # Retrieve the set value for the record length
        #
        postTrgSz = c_uint32(postTriggerSize)
        ret |= self.libCAENDigitizer.CAEN_DGTZ_SetPostTriggerSize(self.handle, postTrgSz)                               # Sets post trigger for next acquisitions (99% of the window)
        ret |= self.libCAENDigitizer.CAEN_DGTZ_GetPostTriggerSize(self.handle, byref(postTrgSz))                        # Retrieve the set value record length
        #
        ret |= self.libCAENDigitizer.CAEN_DGTZ_SetIOLevel(self.handle, c_long(1))                                       # Set TTL levels 
        ret |= self.libCAENDigitizer.CAEN_DGTZ_SetMaxNumEventsBLT(self.handle, c_uint32(maxNumEventsBLT))               # Set the max number of events to transfer in a sigle readout
        ret |= self.libCAENDigitizer.CAEN_DGTZ_SetAcquisitionMode(self.handle, c_long(0))                               # Set the acquisition mode
        ret |= self.libCAENDigitizer.CAEN_DGTZ_SetExtTriggerInputMode(self.handle, c_long(1))                           # Sets external trigger input mode to CAEN_DGTZ_TRGMODE_ACQ_ONLY
        #
        ret |= self.libCAENDigitizer.CAEN_DGTZ_SetChannelEnableMask(self.handle, 1)                                     # Enable channel 0
        ret |= self.libCAENDigitizer.CAEN_DGTZ_SetChannelDCOffset(self.handle, c_uint32(1), c_uint32(channelDCOffset))  # Sets the DC offset for a specified channel. Tvalue is expressed in channel DAC (Digital to Analog Converter) steps. Please refer to digitizer documentation for possible value range. [for DT5730 it is 16-bit (0-65535) DAC up to +- 1V if FSR is 2Vpp]
        
        ret |= self.libCAENDigitizer.CAEN_DGTZ_SetChannelTriggerThreshold(self.handle, 0, c_uint32(triggerThreshold))   # Set selfTrigger threshold    
        ret |= self.libCAENDigitizer.CAEN_DGTZ_SetTriggerPolarity(self.handle, c_uint32(1), c_long(0))                  # Sets the trigger polarity of a specified channel
        ret |= self.libCAENDigitizer.CAEN_DGTZ_SetChannelSelfTrigger(self.handle, c_long(1), 0)                         # Set trigger on channel 0 to be ACQ_ONLY
        
        # Check setup successfully completed     
        if ret==0:
            logging.info("Digitizer setup OK")
            self.dgtConfigured = True
        else:
            logging.warning("Digitizer setup not completed correctly")
            self.dgtConfigured = False
        time.sleep(0.200)                                                                                              # This time is important to make sure that board configuration is written
    
    # TODO generalize to list channelDCOffset_V
    def setupSimple(self, windowSize_s = 300e-6, triggerThres_V = 1.5, channelDCOffset_V = 0.):
        # Convert window size from s to sample units
        recordlength = windowSize_s * self.samplingRate
        logging.info(f"Target window of {windowSize_s*1e6}us is achieved with {recordlength}samples ({recordlength*self.samplingRate*1e6}us)") 
        #
        # Trigger threshold
        triggerThreshold = (triggerThres_V-self.cal_q) / self.cal_m
        logging.info(f"Target threshold of {triggerThres_V}V is achieved with a {triggerThreshold}samples trigger threshold") 
        
        # DC offset (+/- 1V at 2Vpp op.)
        dcOffsetDAC = 65536 # 16-bit
        channelDCOffset = dcOffsetDAC/2
        if channelDCOffset_V not in [-1, 1]:
            logging.warning("Channels DC offset must be within +/- 1V for DT5730 in 2Vpp operation.")
        else:
            channelDCOffset = dcOffsetDAC/2 + int(channelDCOffset_V/2.0 * dcOffsetDAC)
            logging.info(f"Target DC offset of {channelDCOffset_V}V is applied by setting DCoffset DAC value reg. to {channelDCOffset}")                  
        
        self.setup(recordlength=int(recordlength), triggerThreshold=int(triggerThreshold), channelDCOffset=int(channelDCOffset))
    
    # Get the current setup and print
    def printCurrentSetup(self):
        ret = 0
        # Here I follow the same order of the WaveDump.C setup
        RecordLength = c_uint32()
        ret |= self.libCAENDigitizer.CAEN_DGTZ_GetRecordLength(self.handle, byref(RecordLength))                          # Retrieve the set value for the record length
        #
        PostTriggerSize = c_uint32()
        ret |= self.libCAENDigitizer.CAEN_DGTZ_GetPostTriggerSize(self.handle, byref(PostTriggerSize))                       # Retrieve the set value record length
        #
        IOLevel = c_long()
        ret |= self.libCAENDigitizer.CAEN_DGTZ_GetIOLevel(self.handle, byref(IOLevel))                                 # Set TTL levels 
        #
        MaxNumEventsBLT = c_uint32()
        ret |= self.libCAENDigitizer.CAEN_DGTZ_GetMaxNumEventsBLT(self.handle, byref(MaxNumEventsBLT))              # Set the max number of events to transfer in a sigle readout
        #
        AcquisitionMode = c_long()
        ret |= self.libCAENDigitizer.CAEN_DGTZ_GetAcquisitionMode(self.handle, byref(AcquisitionMode))                              # Set the acquisition mode
        #
        ExtTriggerInputMode = c_long()
        ret |= self.libCAENDigitizer.CAEN_DGTZ_GetExtTriggerInputMode(self.handle, byref(ExtTriggerInputMode))                          # Sets external trigger input mode to CAEN_DGTZ_TRGMODE_ACQ_ONLY
        #
        ChannelEnableMask = c_uint32()
        ret |= self.libCAENDigitizer.CAEN_DGTZ_GetChannelEnableMask(self.handle, byref(ChannelEnableMask))                                    # Enable channel 0
        #
        ChannelDCOffset = c_uint32()
        ret |= self.libCAENDigitizer.CAEN_DGTZ_GetChannelDCOffset(self.handle, c_uint32(1), byref(ChannelDCOffset)) # Sets the DC offset for a specified channel. Tvalue is expressed in channel DAC (Digital to Analog Converter) steps. Please refer to digitizer documentation for possible value range. [for DT5730 it is 16-bit (0-65535) DAC up to +- 1V if FSR is 2Vpp]
        #
        ChannelTriggerThreshold = c_uint32()
        ret |= self.libCAENDigitizer.CAEN_DGTZ_GetChannelTriggerThreshold(self.handle, 0, byref(ChannelTriggerThreshold))  # Set selfTrigger threshold    
        #
        TriggerPolarity = c_long()
        ret |= self.libCAENDigitizer.CAEN_DGTZ_GetTriggerPolarity(self.handle, c_uint32(1), byref(TriggerPolarity))                 # Sets the trigger polarity of a specified channel
        #
        ChannelSelfTrigger = c_long()
        ret |= self.libCAENDigitizer.CAEN_DGTZ_GetChannelSelfTrigger(self.handle, c_long(1), byref(ChannelSelfTrigger))                        # Set trigger on channel 0 to be ACQ_ONLY
        
        if ret==0:
            logging.info("GetSetup OK")
            logging.info(f"RecordLength:                            {RecordLength.value}")        
            logging.info(f"PostTriggerSize:                         {PostTriggerSize.value}")        
            logging.info(f"GetIOLevel:                              {IOLevel.value}")        
            logging.info(f"GetMaxNumEventsBLT:                      {MaxNumEventsBLT.value}")        
            logging.info(f"GetAcquisitionMode:                      {AcquisitionMode.value}")        
            logging.info(f"GetExtTriggerInputMode:                  {ExtTriggerInputMode.value}")        
            logging.info(f"CAEN_DGTZ_GetChannelEnableMask:          {ChannelEnableMask.value}")        
            logging.info(f"CAEN_DGTZ_GetChannelDCOffset:            {ChannelDCOffset.value}")        
            logging.info(f"CAEN_DGTZ_GetChannelTriggerThreshold:    {ChannelTriggerThreshold.value}")        
            logging.info(f"CAEN_DGTZ_GetTriggerPolarity:            {TriggerPolarity.value}")        
            logging.info(f"CAEN_DGTZ_GetChannelSelfTrigger:         {ChannelSelfTrigger.value}")        
        else:
            logging.warning("GetSetup failed")
   
    # Try to scan the linkID ports to look where the digitizer is connected
    def autoScan(self):
        logging.info("Autoscan for digitizer linkID starting")
        for usbLinkID in range(0,500):
            # Open the digitizer and store the handler ID
            ret = self.libCAENDigitizer.CAEN_DGTZ_OpenDigitizer(0, usbLinkID, 0, 0, byref(self.handle))
            time.sleep(0.250)
            if ret!=0:
                logging.critical(f"CAEN_DGTZ_OpenDigitizer failed on {usbLinkID}")
                #exit()
            else:
                logging.warning(f"CAEN_DGTZ_OpenDigitizer OK on linkID {usbLinkID}")
                break
   
    # Acquire function
    def openAcquire(self):
        # Malloc Readout Buffer.
        # NOTE1: The mallocs must be done AFTER digitizer's configuration!
        if self.dgtConfigured is False:
            logging.critical("Malloc called before digitizer setup")
            exit()
        # NOTE2: In this example we use the same buffer, for every board. We
        # Use the first board to allocate the buffer, so if the configuration
        # is different for different boards (or you use different board models), may be
        # that the size to allocate must be different for each one.
        ret = self.libCAENDigitizer.CAEN_DGTZ_MallocReadoutBuffer(self.handle, byref(self.buffer), byref(self.size))
        if ret==0:
            logging.info("Allocation OK")
        else:
            logging.critical("Allocation failed")
            exit()
        # Start the acquisition main loop
        ret = self.libCAENDigitizer.CAEN_DGTZ_SWStartAcquisition(self.handle)
        if ret==0:
            logging.info("Acquisition started OK")
            self.acquisitionMode = True
        else:
            logging.critical("Acquisition failed to start")
            exit()
        
        # Acquisition loop
        bsize = c_uint32(0)
        numEvents = c_uint32(0)
        
        # First event stream from the buffer
        firstBuffer = True
        firstBufferTime = -1
        
        stats = self.statsManager()  # Event/rate statistics manager
        while self.acquisitionMode:
            if self.daqLoop:
                # Send single SW trigger
                #print("Send a SW Trigger:", libCAENDigitizer.CAEN_DGTZ_SendSWtrigger(handle)) # Send a SW Trigger
                # Read data
                ret = self.libCAENDigitizer.CAEN_DGTZ_ReadData(self.handle, c_long(0), self.buffer, byref(bsize))
                if ret!=0:
                    logging.critical("CAEN_DGTZ_ReadData failed")
                    self.daqLoop = False
                    exit()

                # The buffer red from the digStart theitizer is used in the other functions to get the event data.
                # The following function returns the number of events in the buffer
                # Get the number of events
                ret = self.libCAENDigitizer.CAEN_DGTZ_GetNumEvents(self.handle, self.buffer, bsize, byref(numEvents))
                if ret!=0:
                    logging.critical("CAEN_DGTZ_GetNumEvents failed")
                    self.daqLoop = False
                    exit()
                        
                # Process buffer data
                if numEvents.value:
                    # Get machine time here
                    if firstBuffer:
                        firstBufferTime = time.time_ns()
                    else:
                        firstBufferTime = -1
                    # Process the buffer containing a certain number 'eventNb' of events 
                    self.processBuffer(bsize = bsize.value, eventsNb = numEvents.value, currentTime = firstBufferTime)
                    # Update data thoughput statistics
                    stats.update(bsize.value, numEvents.value, 10)
                            
                # For the sake of testing, exit the acquire loop closing the run after 4 events 
                if (stats.getTotalEvents() >= self.eventCutoff) and (self.eventCutoff >0):
                    self.daqLoop = False
                    logging.warning("Event cutoff reached. Force stop.")
            else:
                # signal that there are no further items
                self.eventReadout.put(None)
                logging.warning("Closing digitizer")
                break
            # Reduce CPU overhead
            #time.sleep(0.010)
                

    # Process the buffer and the events within   
    def processBuffer(self, bsize: int, eventsNb: int, currentTime: int):
        #return
        for i in range(0, eventsNb):
            # Retrieve event info
            ret = self.CAEN_DGTZ_GetEventInfo(self.handle, self.buffer, bsize, i, byref(self.eventInfo), byref(self.evtptr))
            if ret!=0:
                logging.critical("CAEN_DGTZ_GetEventInfo failed")
                exit()
            else:
                #logging.info(f"CAEN_DGTZ_GetEventInfo processing event {i}")
                #(self.eventInfo).print()
                #self.trgTimetags.append((self.eventInfo).TriggerTimeTag)
                pass
            # Decode event into the Evt data structure
            ret = self.libCAENDigitizer.CAEN_DGTZ_DecodeEvent(self.handle, self.evtptr, byref(self.Evt))
            if ret!=0:
                logging.critical("CAEN_DGTZ_DecodeEvent failed")
                exit()
            
            ########################################
            ########## Event elaboration ###########
            ########################################
            # Event elaboration
            samplesNb = self.Evt.contents.ChSize[0]
            myEvent = np.array(self.Evt.contents.DataChannel[0][0:samplesNb])
            #self.eventContainer.append(myEvent)
            (self.eventReadout).put((self.eventInfo, myEvent, currentTime))
            ########################################
            ########## /Event elaboration ##########
            ########################################

    # Close the acquisition
    def closeAcquire(self):
        # Close the acquisition
        ret = self.libCAENDigitizer.CAEN_DGTZ_SWStopAcquisition(self.handle)
        if ret!=0:
            logging.critical("CAEN_DGTZ_SWStopAcquisition failed")
            return -1
        else:
            logging.debug("CAEN_DGTZ_SWStopAcquisition success")
            self.acquisitionMode = False
        # Clear event
        ret = self.libCAENDigitizer.CAEN_DGTZ_FreeEvent(self.handle, byref(self.Evt))
        if ret!=0:
            logging.critical(f"CAEN_DGTZ_FreeEvent failed")
        # Free readout buffer
        ret = self.libCAENDigitizer.CAEN_DGTZ_FreeReadoutBuffer(byref(self.buffer))
        if ret!=0:
            logging.critical(f"CAEN_DGTZ_FreeReadoutBuffer failed")
        # Log
        logging.info("Acquisition stopped successfully")
        
    # Close the connection with the digitizer
    def shutdownDigitizer(self):
        ret = self.libCAENDigitizer.CAEN_DGTZ_CloseDigitizer(self.handle)
        if ret!=0:
            logging.critical(f"CAEN_DGTZ_CloseDigitizer failed - return is {ret}")
            return -1
        self.acquisitionMode = False
      
    # Print digitizer info
    def printDigitizerInfo(self):
        if self.boardInfo is not None:
            self.boardInfo.print()
        else:
            print("TODO")
            exit() 
    
    # Calibrate the DT5730 digitizer
    def calibrate(self):
        ret = self.libCAENDigitizer.CAEN_DGTZ_Calibrate(self.handle)
        if ret==0:
            logging.info("CAEN_DGTZ_Calibrate OK")
        else:
            logging.warning("CAEN_DGTZ_Calibrate failed")
    
    # Get the waveform with absolute units (timestamp, value) [s, V]
    def calibrated(self, wave) -> tuple:
        #timestamps = np.linspace(0, 327.66e-6, 163830)
        return self.cal_m * wave + self.cal_q
    
    def findCalibration(self, wave, levels = (1.52e-3, 506.0e-3)):
            lowWaveform = np.concatenate((wave[:8000], wave[90400:163400]))
            LL_mean = lowWaveform.mean()
            LL_std = lowWaveform.std()
            #
            highWaveform = wave[16220:82980]
            HL_mean = highWaveform.mean()
            HL_std = highWaveform.std()
            
            self.cal_m = (levels[1]-levels[0])/(HL_mean-LL_mean) # V/DAC
            self.cal_q = levels[0] - self.cal_m * LL_mean
            #
            # Debug information
            print(f"LL of {levels[0]} is {LL_mean}[ADC] (std {LL_std})")
            print(f"HL of {levels[1]} is {HL_mean}[ADC] (std {HL_std})")
            print(f"y=mx + q -> m: {self.cal_m} [V/ADC] | q: {self.cal_q} V")
            #LL of 0.00152 is 8203.023703703704[ADC] (std 7.042329238071286)
            #HL of 0.506 is 12149.519877171959[ADC] (std 10.249691005727641)
            #y=mx + q -> m: 0.00012782984648295086 [V/ADC] | q: -1.0470712607404515 V
        
    eventContainer = []
    trgTimetags = []
    
########################
###### Debug methods ###
########################
    # Plot
    def plotWaveform(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        fig.suptitle("First four waveforms of the run")
        ax2 = ax.twinx()
        ax2.set_ylabel("voltage [V]")
        samplesNb = len(self.eventContainer[0])
        timestamps = np.linspace(0, samplesNb*2e-9, samplesNb)
        for ch, wav_ch in enumerate(self.eventContainer):
            ax.plot(timestamps*1e6, wav_ch, label=f"ch{ch}")
            ax2.plot(timestamps*1e6, wav_ch*self.cal_m + self.cal_q, label=f"ch{ch}")
            if ch>=4:
                break
            #ax2.plot(timestamps*1e6, self.calibrated(wav_ch), label=f"calibrated ch{ch}")
        ax.set_xlabel("time [us]")
        ax.set_ylabel("ADC value [0-16383]")
        ax.legend(loc="upper right")
        fig.show()
        input()
    
    # Debug - Function to test the class
    def testClass(self, eventCutoff: int):
        # Set the event cutoff
        self.eventCutoff = eventCutoff
        # Open digitizer
        self.open()
        # Setup digitizer
        self.setupSimple(windowSize_s = 50e-6, triggerThres_V = 1.5, channelDCOffset_V = 0.)
        # Open acquisition
        self.openAcquire()
        # Close acquisition
        self.closeAcquire()       
        # Close digitizer
        self.shutdownDigitizer()
        # Plot waveform
        self.plotWaveform()
        
    # Debug - Function to test the class
    def testClassWaveform(self, eventCutoff: int):
        self.eventCutoff = eventCutoff
        # Open acquisition
        self.openAcquire()
        # Close acquisition
        self.closeAcquire()       
        # Close digitizer
        self.shutdownDigitizer()
        # Plot waveform
        self.plotWaveform()
##############################################################
######## / CAENDT5730 class ##################################
##############################################################
