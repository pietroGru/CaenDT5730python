from logger import create_logger
import numpy as np
import threading
import ctypes
import queue
import time
import copy

# np.set_printoptions(threshold=np.inf)

### Data structures
# Define the ctypes.Structure for CAEN_DGTZ_X742_GROUP_t
class CAEN_DGTZ_X742_GROUP_t(ctypes.Structure):
    _fields_ = [
        ("ChSize",          9 * ctypes.c_uint32),
        ("DataChannel",     9 * ctypes.POINTER(ctypes.c_float)),
        ("TriggerTimeTag",  ctypes.c_uint32),
        ("StartIndexCell",  ctypes.c_uint16)
    ]
    # Optionally, you can add a print method
    def print(self, ch=-1):
        if ch == -1:
            for i in range(9):
                self.print(i)
        else:
            print(f"Channel {ch}:")
            print(f"ChSize: {self.ChSize[ch]}")
            print(f"DataChannel: {self.DataChannel[ch]}")
            # Note: You may need to access the actual data pointed to by DataChannel[ch]
            #       using indexing or similar depending on how the data is stored.
            print(f"TriggerTimeTag: {self.TriggerTimeTag}")
            print(f"StartIndexCell: {self.StartIndexCell}")     
# Container for the waveform digitized data for DT5742B
class CAEN_DGTZ_X742_EVENT_t(ctypes.Structure):
    _fields_ = [
        ("GrPresent",          4 * ctypes.c_uint8),
        ("DataGroup",          4 * CAEN_DGTZ_X742_GROUP_t)    
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
# Board info
class CAEN_DGTZ_BoardInfo_t(ctypes.Structure):
    _fields_ = [
        ("ModelName",               12 * ctypes.c_char),
        ("Model",                   ctypes.c_uint32),
        ("Channels",                ctypes.c_uint32),
        ("FormFactor",              ctypes.c_uint32),
        ("FamilyCode",              ctypes.c_uint32),
        ("ROC_FirmwareRel",         20 * ctypes.c_char),
        ("AMC_FirmwareRel",         40 * ctypes.c_char),
        ("SerialNumber",            ctypes.c_uint32),
        ("MezzanineSerNum",         4 * 8 * ctypes.c_char),
        ("PCB_Revision",            ctypes.c_uint32),
        ("ADC_NBits",               ctypes.c_uint32),
        ("SAMCorrectionDataLoaded", ctypes.c_uint32),
        ("CommHandle",              ctypes.c_int),
        ("VMEHandle",               ctypes.c_int),
        ("License",                 17 * ctypes.c_char)]
    # Print info on screen
    def print(self):
        print(f"ModelName                  {self.ModelName}")
        print(f"Model                      {self.Model}")
        print(f"Channels                   {self.Channels}")
        print(f"FormFactor                 {self.FormFactor}")
        print(f"FamilyCode                 {self.FamilyCode}")
        print(f"ROC_FirmwareRel            {self.ROC_FirmwareRel}")
        print(f"AMC_FirmwareRel            {self.AMC_FirmwareRel}")
        print(f"SerialNumber               {self.SerialNumber}")
        print(f"MezzanineSerNum            {self.MezzanineSerNum}")
        print(f"PCB_Revision               {self.PCB_Revision}")
        print(f"ADC_NBits                  {self.ADC_NBits}")
        print(f"SAMCorrectionDataLoaded    {self.SAMCorrectionDataLoaded}")
        print(f"CommHandle                 {self.CommHandle}")
        print(f"VMEHandle                  {self.VMEHandle}")
        print(f"License                    {self.License}")
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
class CAEN_DGTZ_EventInfo_t(ctypes.Structure):
    _fields_ = [
        ("EventSize",         ctypes.c_uint32),
        ("BoardId",           ctypes.c_uint32),
        ("Pattern",           ctypes.c_uint32),
        ("ChannelMask",       ctypes.c_uint32),
        ("EventCounter",      ctypes.c_uint32),
        ("TriggerTimeTag",    ctypes.c_uint32) ]
    # Print info on screen
    def print(self):
        print(f"EventSize      {self.EventSize}")
        print(f"BoardId        {self.BoardId}")
        print(f"Pattern        {self.Pattern}")
        print(f"ChannelMask    {self.ChannelMask}")
        print(f"EventCounter   {self.EventCounter}")
        print(f"TriggerTimeTag {self.TriggerTimeTag}")
    # Convert the ctypes.Structure to a dictionary
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
class CAEN_DGTZ_UINT16_EVENT_t(ctypes.Structure):
    _fields_ = [
        ("ChSize",          64 * ctypes.c_uint32),
        ("DataChannel",     64 * ctypes.POINTER(ctypes.c_int16) )    
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
class CAEN_DGTZ_Error(Exception):
    def __init__(self, message):
        super().__init__(message)
# Error codes
CAEN_DGTZ_ErrorCode = {
    0   : ('CAEN_DGTZ_Success', 'Operation completed successfully'),
    -1  : ('CAEN_DGTZ_CommError', 'Communication error'),
    -2  : ('CAEN_DGTZ_GenericError', 'Unspecified error'),
    -3  : ('CAEN_DGTZ_InvalidParam', 'Invalid parameter'),
    -4  : ('CAEN_DGTZ_InvalidLinkType', 'Invalid Link Type'),
    -5  : ('CAEN_DGTZ_InvalidHandle', 'Invalid device handle'),
    -6  : ('CAEN_DGTZ_MaxDevicesError', 'Maximum number of devices exceeded'),
    -7  : ('CAEN_DGTZ_BadBoardType', 'The operation is not allowed on this type of board'),
    -8  : ('CAEN_DGTZ_BadInterruptLev', 'The interrupt level is not allowed'),
    -9  : ('CAEN_DGTZ_BadEventNumber', 'The event number is bad'),
    -10 : ('CAEN_DGTZ_ReadDeviceRegisterFail', 'Unable to read the registry'),
    -11 : ('CAEN_DGTZ_WriteDeviceRegisterFail', 'Unable to write into the registry'),
    -13 : ('CAEN_DGTZ_InvalidChannelNumber', 'The channel number is invalid'),
    -14 : ('CAEN_DGTZ_ChannelBusy', 'The Channel is busy'),
    -15 : ('CAEN_DGTZ_FPIOModeInvalid', 'Invalid FPIO Mode'),
    -16 : ('CAEN_DGTZ_WrongAcqMode', 'Wrong acquisition mode'),
    -17 : ('CAEN_DGTZ_FunctionNotAllowed', 'This function is not allowed for this module'),
    -18 : ('CAEN_DGTZ_Timeout', 'Communication Timeout'),
    -19 : ('CAEN_DGTZ_InvalidBuffer', 'The buffer is invalid'),
    -20 : ('CAEN_DGTZ_EventNotFound', 'The event is not found'),
    -21 : ('CAEN_DGTZ_InvalidEvent', 'The event is invalid'),
    -22 : ('CAEN_DGTZ_OutOfMemory', 'Out of memory'),
    -23 : ('CAEN_DGTZ_CalibrationError', 'Unable to calibrate the board'),
    -24 : ('CAEN_DGTZ_DigitizerNotFound', 'Unable to open the digitizer'),
    -25 : ('CAEN_DGTZ_DigitizerAlreadyOpen', 'The Digitizer is already open'),
    -26 : ('CAEN_DGTZ_DigitizerNotReady', 'The Digitizer is not ready to operate'),
    -27 : ('CAEN_DGTZ_InterruptNotConfigured', 'The Digitizer has not the IRQ configured'),
    -28 : ('CAEN_DGTZ_DigitizerMemoryCorrupted', 'The digitizer flash memory is corrupted'),
    -29 : ('CAEN_DGTZ_DPPFirmwareNotSupported', 'The digitizer dpp firmware is not supported in this lib version'),
    -30 : ('CAEN_DGTZ_InvalidLicense', 'Invalid Firmware License'),
    -31 : ('CAEN_DGTZ_InvalidDigitizerStatus', 'The digitizer is found in a corrupted status'),
    -32 : ('CAEN_DGTZ_UnsupportedTrace', 'The given trace is not supported by the digitizer'),
    -33 : ('CAEN_DGTZ_InvalidProbe', "The given probe is not supported for the given digitizer's trace"),
    -34 : ('CAEN_DGTZ_UnsupportedBaseAddress', "The Base Address is not supported, it's a Desktop device?"),
    -99 : ('CAEN_DGTZ_NotYetImplemented', 'The function is not yet implemented')
}
def CAEN_DGTZ_ErrorHandler(ret: int):
    if ret == 0:
        return True
    else:
        raise CAEN_DGTZ_Error(CAEN_DGTZ_ErrorCode[ret][0] + " - " + CAEN_DGTZ_ErrorCode[ret][1])

# Enums
class CAEN_DGTZ_TriggerMode_t():
    CAEN_DGTZ_TRGMODE_DISABLED = 0
    CAEN_DGTZ_TRGMODE_EXTOUT_ONLY = 2
    CAEN_DGTZ_TRGMODE_ACQ_ONLY = 1
    CAEN_DGTZ_TRGMODE_ACQ_AND_EXTOUT = 3
class CAEN_DGTZ_RunSyncMode_t():
    CAEN_DGTZ_RUN_SYNC_Disabled = 0
    CAEN_DGTZ_RUN_SYNC_TrgOutTrgInDaisyChain = 1
    CAEN_DGTZ_RUN_SYNC_TrgOutSinDaisyChain = 2
    CAEN_DGTZ_RUN_SYNC_SinFanout = 3
    CAEN_DGTZ_RUN_SYNC_GpioGpioDaisyChain = 4
class CAEN_DGTZ_IOLevel_t():
    CAEN_DGTZ_IOLevel_NIM = 0
    CAEN_DGTZ_IOLevel_TTL = 1
class CAEN_DGTZ_TriggerPolarity_t():
    CAEN_DGTZ_TriggerOnRisingEdge = 0
    CAEN_DGTZ_TriggerOnFallingEdge = 1
class CAEN_DGTZ_DRS4Frequency_t():
    CAEN_DGTZ_DRS4_5GHz = 0
    CAEN_DGTZ_DRS4_2_5GHz = 1
    CAEN_DGTZ_DRS4_1GHz = 2
    CAEN_DGTZ_DRS4_750MHz = 3
    _CAEN_DGTZ_DRS4_COUNT_ = 4
class CAEN_DGTZ_OutputSignalMode_t():
    CAEN_DGTZ_TRIGGER = 0
    CAEN_DGTZ_FASTTRG_ALL = 1
    CAEN_DGTZ_FASTTRG_ACCEPTED = 2
    CAEN_DGTZ_BUSY = 3
class CAEN_DGTZ_AcqMode_t():
    CAEN_DGTZ_SW_CONTROLLED = 0
    CAEN_DGTZ_S_IN_CONTROLLED = 1
    CAEN_DGTZ_FIRST_TRG_CONTROLLED = 2



class CAENDT5742B():
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
  
    def __init__(self, usbLinkID: int, evtReadoutQueue: queue.Queue, libCAENDigitizer_path = 'libCAENDigitizer.so', libCAENX742DecodeRoutines_path = './libX742DecodeRoutines.so', eventCutoff=-1, logLevel: int = 20) -> None:
        # Create the class logger instante
        self.logging = create_logger("CAENDT5742B")
        self.logging.setLevel(logLevel)      
        
        # Load CAENDigitizer library
        self.libCAENDigitizer = ctypes.cdll.LoadLibrary(libCAENDigitizer_path)
        self.libCAENX742DecodeRoutines = ctypes.cdll.LoadLibrary(libCAENX742DecodeRoutines_path)
        
        # Parameters for the digitizer
        self.handle = ctypes.c_int()                                        # Digitizer unique handler ID for the session
        self.usbLinkID = ctypes.c_int(usbLinkID)                            # Digitizer USB link ID
        self.SamplingRate = 1                                               # Initialized at 1
        self.dacFSR = 2**12-1                                               # 2^12 bit
        # self.boardInfo = None                                               # Board info var
        self.dgtConfigured = False                                          # Board setup has been done
        
        # Variables for the acquisition
        self.buffer = ctypes.POINTER(ctypes.c_char)()                       # Input buffer
        self.bufferSize = ctypes.c_uint32()                                 # Sizeof of the input buffer
        self.evtptr = ctypes.POINTER(ctypes.c_char)()                       # evtptr char event buffer - I don't remember
        self.Evt = ctypes.POINTER(CAEN_DGTZ_X742_EVENT_t)()                 # evt pointer
        self.TrgInfo = CAEN_DGTZ_EventInfo_t()                              # Event info struct
                
        # Event readout variables
        self.daqLoop = False
        self.acquisitionMode = True 
        ## Queue for events readout
        self.eventReadout = evtReadoutQueue
        self.lock = threading.Lock()
        ### Close digitizer after cutoff is reached (mainly for debugging)
        self.eventCutoff = eventCutoff
        if self.eventCutoff>0: (self.logging).warning(f"Event cutoff set. The readout will stop after {self.eventCutoff} events!")
        
        # Calibration data [(from DAC to V is just V = m*sample + q)]
        self.cal_m, self.cal_q = 0.00012782984648295086, -1.0470712607404515
        
        ############################################################################################################
        
        # Functions (for which it is super convenient to pythonize the input/output) 
        # ## CAEN_DGTZ_GetInfo
        # self.CAEN_DGTZ_GetInfo = self.libCAENDigitizer.CAEN_DGTZ_GetInfo
        # self.CAEN_DGTZ_GetInfo.argtypes = [ctypes.c_int, ctypes.POINTER(CAEN_DGTZ_BoardInfo_t)]
        # self.CAEN_DGTZ_GetInfo.restype = ctypes.c_long 
        # # CAEN_DGTZ_GetEventInfo
        # self.CAEN_DGTZ_GetEventInfo = self.libCAENDigitizer.CAEN_DGTZ_GetEventInfo
        # self.CAEN_DGTZ_GetEventInfo.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_char), ctypes.c_uint32, ctypes.c_int32, ctypes.POINTER(CAEN_DGTZ_EventInfo_t), ctypes.POINTER(ctypes.POINTER(ctypes.c_char))]
        # self.CAEN_DGTZ_GetEventInfo.restype = ctypes.c_long
        
        ####################################################################################################################################################################################
        

    # Open the digitizer and retrieve information about the boards
    def open(self):
        """
        Open the digitizer with the given USB link ID and retrieve the board information
        """
        # Open the digitizer and store the handler ID
        ret = self.libCAENDigitizer.CAEN_DGTZ_OpenDigitizer(0, self.usbLinkID, 0, 0, ctypes.byref(self.handle))
        CAEN_DGTZ_ErrorHandler(ret)
        
        # Get board information
        self.boardInfo = CAEN_DGTZ_BoardInfo_t()
        ret = self.libCAENDigitizer.CAEN_DGTZ_GetInfo(self.handle, ctypes.byref(self.boardInfo))
        self.boardInfo.print()
        CAEN_DGTZ_ErrorHandler(ret)
    
    
    # Setup of the digitizer. Unpack the input arguments and setup the calls to the libCAEN methods
    def setup(self, **kwargs):
        """
        Setup of the digitizer. Unpack the input arguments and setup the calls to the libCAEN methods
        
        Parameters
        ----------
            **kwargs (dict) : setup parameters
        """
        self.setup_DT5742B(**kwargs)
    
    
    # Enable a triangular sawtooth test pattern at the input of the ADC
    def enableTestPatter(self):
        """
        Enable a triangular sawtooth test pattern at the input of the ADC
        """
        ret = self.libCAENDigitizer.CAEN_DGTZ_WriteRegister(self.handle, 0x8004, 1<<3)
        CAEN_DGTZ_ErrorHandler(ret)
    
    
    
    # Default setup for the CAEN DT5742B digitizer.
    def setup_DT5742B(self, SWTriggerMode: CAEN_DGTZ_TriggerMode_t, ExtTriggerInputMode: CAEN_DGTZ_TriggerMode_t, RunSyncMode: CAEN_DGTZ_RunSyncMode_t, IOLevel: CAEN_DGTZ_IOLevel_t, TriggerPolarity: CAEN_DGTZ_TriggerPolarity_t, DRS4Frequency: CAEN_DGTZ_DRS4Frequency_t, OutputSignalMode: CAEN_DGTZ_OutputSignalMode_t, AcqMode: CAEN_DGTZ_AcqMode_t, GroupEnableMask: ctypes.c_uint32, RecordLength: ctypes.c_uint32, PostTriggerSizePercent: ctypes.c_uint32, ChannelDCOffset: ctypes.c_uint32):
        """
        Setup method for the DT5742B digitizer 
        
        Parameters
        ----------
            SWTriggerMode (CAEN_DGTZ_TriggerMode_t) : TRGMODE_DISABLED, TRGMODE_EXTOUT_ONLY, TRGMODE_ACQ_ONLY, TRGMODE_ACQ_AND_EXTOUT
            ExtTriggerInputMode (CAEN_DGTZ_TriggerMode_t) : TRGMODE_DISABLED, TRGMODE_EXTOUT_ONLY, TRGMODE_ACQ_ONLY, TRGMODE_ACQ_AND_EXTOUT
            RunSyncMode (CAEN_DGTZ_RunSyncMode_t) : Disabled, TrgOutTrgInDaisyChain, TrgOutSinDaisyChain, SinFanout, GpioGpioDaisyChain
            IOLevel (CAEN_DGTZ_IOLevel_t) : NIM or TTL
            TriggerPolarity (CAEN_DGTZ_TriggerPolarity_t) : Rising or Falling 
            DRS4Frequency (CAEN_DGTZ_DRS4Frequency_t) : 5GHz, 2_5GHz, 1GHz, 750MHz
            OutputSignalMode (CAEN_DGTZ_OutputSignalMode_t) : TRIGGER, FASTTRG_ALL, FASTTRG_ACCEPTED
            AcqMode (CAEN_DGTZ_AcqMode_t) : SW_CONTROLLED, S_IN_CONTROLLED, FIRST_TRG_CONTROLLED
            GroupEnableMask (ctypes.c_uint32) : Group enable mask
            RecordLength (ctypes.c_uint32) : Record length
            PostTriggerSizePercent (ctypes.c_uint32) : Post trigger size percent
            ChannelDCOffset (ctypes.c_uint32) : Channel DC offset
            
        Returns
        -------
            None
        """
        
        ret = {}
        # Reset the digitizer to restore the original configuration
        ret['CAEN_DGTZ_Reset']                          = self.libCAENDigitizer.CAEN_DGTZ_Reset(self.handle)
        time.sleep(0.100) #may be useful

        # Trigger configuration
        ret['CAEN_DGTZ_SetSWTriggerMode']               = self.libCAENDigitizer.CAEN_DGTZ_SetSWTriggerMode(self.handle, SWTriggerMode)
        ret['CAEN_DGTZ_SetExtTriggerInputMode']         = self.libCAENDigitizer.CAEN_DGTZ_SetExtTriggerInputMode(self.handle, ExtTriggerInputMode)
        # ret['CAEN_DGTZ_SetGroupSelfTrigger']            = self.libCAENDigitizer.CAEN_DGTZ_SetGroupSelfTrigger(self.handle)
        # ret['CAEN_DGTZ_SetChannelGroupMask']            = self.libCAENDigitizer.CAEN_DGTZ_SetChannelGroupMask(self.handle)
        # ret['CAEN_DGTZ_SetGroupTriggerThreshold']       = self.libCAENDigitizer.CAEN_DGTZ_SetGroupTriggerThreshold(self.handle)
        ret['CAEN_DGTZ_SetRunSynchronizationMode']      = self.libCAENDigitizer.CAEN_DGTZ_SetRunSynchronizationMode(self.handle, RunSyncMode)
        ret['CAEN_DGTZ_SetIOLevel']                     = self.libCAENDigitizer.CAEN_DGTZ_SetIOLevel(self.handle, IOLevel)
        ret['CAEN_DGTZ_SetTriggerPolarity']             = self.libCAENDigitizer.CAEN_DGTZ_SetTriggerPolarity(self.handle, TriggerPolarity)
        ret['CAEN_DGTZ_SetFastTriggerDigitizing']       = self.libCAENDigitizer.CAEN_DGTZ_SetFastTriggerDigitizing(self.handle, 0)
        ret['CAEN_DGTZ_SetFastTriggerMode']             = self.libCAENDigitizer.CAEN_DGTZ_SetFastTriggerMode(self.handle, 0)
        ret['CAEN_DGTZ_SetDRS4SamplingFrequency']       = self.libCAENDigitizer.CAEN_DGTZ_SetDRS4SamplingFrequency(self.handle, DRS4Frequency)
        ret['CAEN_DGTZ_SetOutputSignalMode']            = self.libCAENDigitizer.CAEN_DGTZ_SetOutputSignalMode(self.handle, OutputSignalMode)
        
        # Acquisition configuration
        ret['CAEN_DGTZ_SetGroupEnableMask']             = self.libCAENDigitizer.CAEN_DGTZ_SetGroupEnableMask(self.handle, GroupEnableMask)  # Enable group 0# only channel 1 acquiring
        ret['CAEN_DGTZ_SetRecordLength']                = self.libCAENDigitizer.CAEN_DGTZ_SetRecordLength(self.handle, RecordLength)
        ret['CAEN_DGTZ_SetPostTriggerSize']             = self.libCAENDigitizer.CAEN_DGTZ_SetPostTriggerSize(self.handle, PostTriggerSizePercent)
        ret['CAEN_DGTZ_SetAcquisitionMode']             = self.libCAENDigitizer.CAEN_DGTZ_SetAcquisitionMode(self.handle, AcqMode)
        ret['CAEN_DGTZ_SetChannelDCOffset']             = self.libCAENDigitizer.CAEN_DGTZ_SetChannelDCOffset(self.handle, 0, ChannelDCOffset)
        # ret['CAEN_DGTZ_SetDESMode']                     = self.libCAENDigitizer.CAEN_DGTZ_SetDESMode(self.handle)
        # ret['CAEN_DGTZ_SetDecimationFactor']            = self.libCAENDigitizer.CAEN_DGTZ_SetDecimationFactor(self.handle)
        # ret['CAEN_DGTZ_SetZeroSuppressionMode']         = self.libCAENDigitizer.CAEN_DGTZ_SetZeroSuppressionMode(self.handle)
        # ret['CAEN_DGTZ_SetChannelZSParams']             = self.libCAENDigitizer.CAEN_DGTZ_SetChannelZSParams(self.handle)
        # ret['CAEN_DGTZ_SetAnalogMonOutput']             = self.libCAENDigitizer.CAEN_DGTZ_SetAnalogMonOutput(self.handle)
        # ret['CAEN_DGTZ_SetAnalogInspectionMonParams']   = self.libCAENDigitizer.CAEN_DGTZ_SetAnalogInspectionMonParams(self.handle)
        # ret['CAEN_DGTZ_SetEventPackaging']              = self.libCAENDigitizer.CAEN_DGTZ_SetEventPackaging(self.handle)
        
        retGlobal = 0
        for key in ret:
            retGlobal |= ret[key]
            if ret[key] < 0: self.logging.error(f"Error in setting {key} ({ret[key]})")
            CAEN_DGTZ_ErrorHandler(ret[key])
        
        # Set the digitizer configured flag
        self.dgtConfigured = True
        CAEN_DGTZ_DRS4Frequency_t = {
            0 : 5.0e9,  # 'CAEN_DGTZ_DRS4_5GHz',
            1 : 2.5e9,  # 'CAEN_DGTZ_DRS4_2_5GHz',
            2 : 1.0e9,  # 'CAEN_DGTZ_DRS4_1GHz',
            3 : 750.e6, # 'CAEN_DGTZ_DRS4_750MHz',
        }
        self.SamplingPeriod_s = 1/CAEN_DGTZ_DRS4Frequency_t[DRS4Frequency]
        # print("self.SamplingPeriod_s", self.SamplingPeriod_s)
        self.ChannelDCOffset_ADC = ChannelDCOffset
        self.ChannelDCOffset_V = float(ChannelDCOffset - 0x7FFF)/0x7FFF
        self.RecordLength = int(RecordLength)
        self.waveformtime = np.linspace(0, self.RecordLength*self.SamplingPeriod_s, self.RecordLength)

    # Default setup for the CAEN DT5742B digitizer.
    def setup_DT5742BDefault(self):
        """
        Default setup for the CAEN DT5742B digitizer.
        """
        self.setup_DT5742B(
            SWTriggerMode           = CAEN_DGTZ_TriggerMode_t.CAEN_DGTZ_TRGMODE_DISABLED,
            ExtTriggerInputMode     = CAEN_DGTZ_TriggerMode_t.CAEN_DGTZ_TRGMODE_ACQ_ONLY,
            RunSyncMode             = CAEN_DGTZ_RunSyncMode_t.CAEN_DGTZ_RUN_SYNC_Disabled,
            IOLevel                 = CAEN_DGTZ_IOLevel_t.CAEN_DGTZ_IOLevel_TTL,
            TriggerPolarity         = CAEN_DGTZ_TriggerPolarity_t.CAEN_DGTZ_TriggerOnRisingEdge,
            DRS4Frequency           = CAEN_DGTZ_DRS4Frequency_t.CAEN_DGTZ_DRS4_750MHz,
            OutputSignalMode        = CAEN_DGTZ_OutputSignalMode_t.CAEN_DGTZ_TRIGGER,
            AcqMode                 = CAEN_DGTZ_AcqMode_t.CAEN_DGTZ_SW_CONTROLLED,
            GroupEnableMask         = 0b1,
            RecordLength            = 1024,
            PostTriggerSizePercent  = 100,
            ChannelDCOffset         = 0x7FFF
        )

    def setupSimple_DT5742(self, windowSize_s: float, channelDCOffset_V: float, TriggerPolarity: CAEN_DGTZ_TriggerPolarity_t = 0, GroupEnableMask: int = 0b1):
        """
        Calculate the windows size in samples and set the digitizer accordingly
        """
        
        # CAEN_DGTZ_DRS4Frequency_t = {
        #     0 : 'CAEN_DGTZ_DRS4_5GHz',
        #     1 : 'CAEN_DGTZ_DRS4_2_5GHz',
        #     2 : 'CAEN_DGTZ_DRS4_1GHz',
        #     3 : 'CAEN_DGTZ_DRS4_750MHz',
        # }
        # Calculate the sampling rate that gives a windowsSize_s in the 1024 samples
        targetSamplingRate_max = (1024/windowSize_s)        
        for CAEN_DGTZ_DRS4Frequency_value, rate in enumerate([5e9, 2.5e9, 1e9, 750e6]):
            if rate < targetSamplingRate_max:
                break
        """
        For example with a 10us I want a sampling rate such that the window of 1024 is covered.
        samplingPeriod *1024 > windowSize_s
        1024/samplingRate > windowSize_s
        samplingRate < 1024/windowSize_s
        
        samplingRate \in {750e6, 1e9, 2.5e9, 5e9}
        e.g. windowSize_s = 10e-6
        
        samplingRate < 1024/10e-6 = 1.024e8
        
        9.7e-9
        750MHz
        """
        
        if np.abs(channelDCOffset_V)>0.5: raise Exception("Channel DC offset must be within +/- 0.5V (Vpp is 1V)")
        if channelDCOffset_V>0:
            value = -channelDCOffset_V/0.5 * 2**15 + 0x7FFF + 1
        else:
            value = -channelDCOffset_V/0.5* 2**15 + 0x7FFF
        channelDCOffset = int(value)
        # print("channelDCOffset", hex(channelDCOffset), channelDCOffset, channelDCOffset-2**15)
        
        self.setup_DT5742B(
            SWTriggerMode           = CAEN_DGTZ_TriggerMode_t.CAEN_DGTZ_TRGMODE_DISABLED,
            ExtTriggerInputMode     = CAEN_DGTZ_TriggerMode_t.CAEN_DGTZ_TRGMODE_ACQ_ONLY,
            RunSyncMode             = CAEN_DGTZ_RunSyncMode_t.CAEN_DGTZ_RUN_SYNC_Disabled,
            IOLevel                 = CAEN_DGTZ_IOLevel_t.CAEN_DGTZ_IOLevel_TTL,
            TriggerPolarity         = TriggerPolarity,
            DRS4Frequency           = CAEN_DGTZ_DRS4Frequency_value,
            OutputSignalMode        = CAEN_DGTZ_OutputSignalMode_t.CAEN_DGTZ_TRIGGER,
            AcqMode                 = CAEN_DGTZ_AcqMode_t.CAEN_DGTZ_SW_CONTROLLED,
            GroupEnableMask         = GroupEnableMask,
            RecordLength            = 1024,
            PostTriggerSizePercent  = 100,
            ChannelDCOffset         = channelDCOffset
        )
    


    # Get the current setup and print
    def printSetup(self):
        CAEN_DGTZ_TriggerMode_t = { 
            'CAEN_DGTZ_TRGMODE_DISABLED' : 0,
            'CAEN_DGTZ_TRGMODE_EXTOUT_ONLY' : 2,
            'CAEN_DGTZ_TRGMODE_ACQ_ONLY' : 1,
            'CAEN_DGTZ_TRGMODE_ACQ_AND_EXTOUT' : 3
        }
        CAEN_DGTZ_RunSyncMode_t = {       
            'CAEN_DGTZ_RUN_SYNC_Disabled': 0,
            'CAEN_DGTZ_RUN_SYNC_TrgOutTrgInDaisyChain': 1,
            'CAEN_DGTZ_RUN_SYNC_TrgOutSinDaisyChain': 2,
            'CAEN_DGTZ_RUN_SYNC_SinFanout': 3,
            'CAEN_DGTZ_RUN_SYNC_GpioGpioDaisyChain': 4
        }
        CAEN_DGTZ_IOLevel_t = {
            'CAEN_DGTZ_IOLevel_NIM' : 0,
            'CAEN_DGTZ_IOLevel_TTL' : 1
        }
        CAEN_DGTZ_TriggerPolarity_t = {
            'CAEN_DGTZ_TriggerOnRisingEdge' : 0,
            'CAEN_DGTZ_TriggerOnFallingEdge' : 1
        }
        CAEN_DGTZ_EnaDis_t = {
            'CAEN_DGTZ_ENABLE' : 1,
            'CAEN_DGTZ_DISABLE' : 0
        }
        CAEN_DGTZ_DRS4Frequency_t = {
            'CAEN_DGTZ_DRS4_5GHz' : 0,
            'CAEN_DGTZ_DRS4_2_5GHz' : 1,
            'CAEN_DGTZ_DRS4_1GHz' : 2,
            'CAEN_DGTZ_DRS4_750MHz' : 3,
            '_CAEN_DGTZ_DRS4_COUNT_' : 4
        }
        CAEN_DGTZ_OutputSignalMode_t = {
            'CAEN_DGTZ_TRIGGER' : 0,
            'CAEN_DGTZ_FASTTRG_ALL' : 1,
            'CAEN_DGTZ_FASTTRG_ACCEPTED' : 2,
            'CAEN_DGTZ_BUSY' : 3
        }
        CAEN_DGTZ_AcqMode_t = {
            'CAEN_DGTZ_SW_CONTROLLED' : 0,
            'CAEN_DGTZ_S_IN_CONTROLLED' : 1,
            'CAEN_DGTZ_FIRST_TRG_CONTROLLED' : 2
        }
        
        # Invert the key with the value
        def invertKeyValue(aDict: dict):
            return {v: k for k, v in aDict.items()}
        for item in [CAEN_DGTZ_TriggerMode_t, CAEN_DGTZ_RunSyncMode_t, CAEN_DGTZ_IOLevel_t, CAEN_DGTZ_TriggerPolarity_t, CAEN_DGTZ_EnaDis_t, CAEN_DGTZ_DRS4Frequency_t, CAEN_DGTZ_OutputSignalMode_t, CAEN_DGTZ_AcqMode_t]:
            item = invertKeyValue(item)
    
        # Trigger configuration
        SWTriggerMode = ctypes.c_long()
        ExtTriggerInputMode = ctypes.c_long()
        IOLevel = ctypes.c_long()
        TriggerPolarity = ctypes.c_long()
        FastTriggerDigitizing = ctypes.c_long()
        FastTriggerMode = ctypes.c_long()
        DRS4SamplingFrequency = ctypes.c_long()
        OutputSignalMode = ctypes.c_long()
        GroupEnableMask = ctypes.c_uint32()
        RecordLength = ctypes.c_uint32()
        PostTriggerSize = ctypes.c_uint32()
        AcquisitionMode = ctypes.c_long()
        ChannelDCOffset = {i : ctypes.c_uint32() for i in range(8)}
        
        ret = {}
        ret['CAEN_DGTZ_GetSWTriggerMode']               = self.libCAENDigitizer.CAEN_DGTZ_GetSWTriggerMode(self.handle, ctypes.byref(SWTriggerMode))
        ret['CAEN_DGTZ_GetExtTriggerInputMode']         = self.libCAENDigitizer.CAEN_DGTZ_GetExtTriggerInputMode(self.handle, ctypes.byref(ExtTriggerInputMode))
        ret['CAEN_DGTZ_GetIOLevel']                     = self.libCAENDigitizer.CAEN_DGTZ_GetIOLevel(self.handle, ctypes.byref(IOLevel))
        ret['CAEN_DGTZ_GetTriggerPolarity']             = self.libCAENDigitizer.CAEN_DGTZ_GetTriggerPolarity(self.handle, ctypes.byref(TriggerPolarity))
        ret['CAEN_DGTZ_GetFastTriggerDigitizing']       = self.libCAENDigitizer.CAEN_DGTZ_GetFastTriggerDigitizing(self.handle, ctypes.byref(FastTriggerDigitizing))
        ret['CAEN_DGTZ_GetFastTriggerMode']             = self.libCAENDigitizer.CAEN_DGTZ_GetFastTriggerMode(self.handle, ctypes.byref(FastTriggerMode))
        ret['CAEN_DGTZ_GetDRS4SamplingFrequency']       = self.libCAENDigitizer.CAEN_DGTZ_GetDRS4SamplingFrequency(self.handle, ctypes.byref(DRS4SamplingFrequency))
        ret['CAEN_DGTZ_GetOutputSignalMode']            = self.libCAENDigitizer.CAEN_DGTZ_GetOutputSignalMode(self.handle, ctypes.byref(OutputSignalMode))
        ret['CAEN_DGTZ_GetGroupEnableMask']             = self.libCAENDigitizer.CAEN_DGTZ_GetGroupEnableMask(self.handle, ctypes.byref(GroupEnableMask))
        ret['CAEN_DGTZ_GetRecordLength']                = self.libCAENDigitizer.CAEN_DGTZ_GetRecordLength(self.handle, ctypes.byref(RecordLength))
        ret['CAEN_DGTZ_GetPostTriggerSize']             = self.libCAENDigitizer.CAEN_DGTZ_GetPostTriggerSize(self.handle, ctypes.byref(PostTriggerSize))
        ret['CAEN_DGTZ_GetAcquisitionMode']             = self.libCAENDigitizer.CAEN_DGTZ_GetAcquisitionMode(self.handle, ctypes.byref(AcquisitionMode))
        for i in range(8):
            ret[f'CAEN_DGTZ_GetChannelDCOffset_ch{i}']  = self.libCAENDigitizer.CAEN_DGTZ_GetChannelDCOffset(self.handle, i, ctypes.byref(ChannelDCOffset[i]))

        flagErr = False
        def errHandler(err):
            if err==0:
                return self.logging.info
            else:
                flagErr = True
                return self.logging.error
        
        errHandler(ret['CAEN_DGTZ_GetSWTriggerMode'])               (f"SWTriggerMode:         {CAEN_DGTZ_TriggerMode_t[SWTriggerMode.value][10:]}")
        errHandler(ret['CAEN_DGTZ_GetExtTriggerInputMode'])         (f"ExtTriggerInputMode:   {CAEN_DGTZ_TriggerMode_t[ExtTriggerInputMode.value][10:]}")
        errHandler(ret['CAEN_DGTZ_GetIOLevel'])                     (f"IOLevel:               {CAEN_DGTZ_IOLevel_t[IOLevel.value][10:]}")
        errHandler(ret['CAEN_DGTZ_GetTriggerPolarity'])             (f"TriggerPolarity:       {CAEN_DGTZ_TriggerPolarity_t[TriggerPolarity.value][10:]}")
        errHandler(ret['CAEN_DGTZ_GetFastTriggerDigitizing'])       (f"FastTriggerDigitizing: {CAEN_DGTZ_EnaDis_t[FastTriggerDigitizing.value][10:]}")
        errHandler(ret['CAEN_DGTZ_GetFastTriggerMode'])             (f"FastTriggerMode:       {CAEN_DGTZ_TriggerMode_t[FastTriggerMode.value][10:]}")
        errHandler(ret['CAEN_DGTZ_GetDRS4SamplingFrequency'])       (f"DRS4SamplingFrequency: {CAEN_DGTZ_DRS4Frequency_t[DRS4SamplingFrequency.value][10:]}")
        errHandler(ret['CAEN_DGTZ_GetOutputSignalMode'])            (f"OutputSignalMode:      {CAEN_DGTZ_OutputSignalMode_t[OutputSignalMode.value][10:]}")
        errHandler(ret['CAEN_DGTZ_GetGroupEnableMask'])             (f"GroupEnableMask:       {GroupEnableMask.value}")
        errHandler(ret['CAEN_DGTZ_GetRecordLength'])                (f"RecordLength:          {RecordLength.value}")
        errHandler(ret['CAEN_DGTZ_GetPostTriggerSize'])             (f"PostTriggerSize:       {PostTriggerSize.value}")
        errHandler(ret['CAEN_DGTZ_GetAcquisitionMode'])             (f"AcquisitionMode:       {CAEN_DGTZ_AcqMode_t[AcquisitionMode.value][10:]}")
        for i in range(8):
            errHandler(ret[f'CAEN_DGTZ_GetChannelDCOffset_ch{i}'])  (f"ChannelDCOffset ({i}): {ChannelDCOffset[i]}")


  
    # Try to scan the linkID ports to look where the digitizer is connected
    def autoScan_UsbLinkID(self, start : int = 0, stop : int = 500) -> int:
        """
        Try to scan the linkID ports to look where the digitizer is connected. If successful, returns the digitizer linkID
        
        Parameters
        ----------
            start (int) : the starting linkID
            stop (int) : the ending linkID
        
        Returns
        -------
            usbLinkID (int) : the linkID where the digitizer is connected
        """
        (self.logging).info("Autoscan for digitizer linkID starting")
        for usbLinkID in range(start, stop):
            # Open the digitizer and store the handler ID
            ret = self.libCAENDigitizer.CAEN_DGTZ_OpenDigitizer(0, usbLinkID, 0, 0, ctypes.byref(self.handle))
            time.sleep(0.250)
            if ret!=0:
                (self.logging).critical(f"CAEN_DGTZ_OpenDigitizer failed on {usbLinkID}")
            else:
                (self.logging).status(f"CAEN_DGTZ_OpenDigitizer OK on linkID {usbLinkID}\n")
                return usbLinkID
        raise Exception(f"Digitizer not found in the linkID range {start}-{stop}")
    
    def setDaqLoop(self, value:bool):
        self.lock.acquire()
        self.daqLoop = value
        self.eventReadout.put(None)
        self.lock.release()
        
    # Acquire function
    def acquireLoop(self):
        """
        Acquire function. Pipeline
        1. Allocate the readout buffer
        2. Start the acquisition
        3. LOOP
            3.1 Read the data
            3.2 Allocate the Event buffer
            3.3 Process the readout buffer and fit the Event buffer
            3.4 Read the Event data and put in the queue the readout structed Event
            3.5 Deallocate the Event buffer
        4. Deallocate the readout buffer
        """
        
        # Checks that the digitizer is configured
        if self.dgtConfigured is False: (self.logging).warning("The digitizer is not configured. Maybe missed the call?")
        
        # Class handling the statistics of event/rate etc.
        stats = self.statsManager()  # Event/rate statistics manager
                        
        # Allocate the readout buffer
        # NOTE1: The mallocs must be done AFTER digitizer's configuration!
        ret = self.libCAENDigitizer.CAEN_DGTZ_MallocReadoutBuffer(self.handle, ctypes.byref(self.buffer), ctypes.byref(self.bufferSize))
        CAEN_DGTZ_ErrorHandler(ret)
        # (self.logging).trace("CAEN_DGTZ_MallocReadoutBuffer OK")
        
        # Start the acquisition main loop
        ret = self.libCAENDigitizer.CAEN_DGTZ_SWStartAcquisition(self.handle)
        CAEN_DGTZ_ErrorHandler(ret)
        # (self.logging).trace("CAEN_DGTZ_SWStartAcquisition OK")
        self.acquisitionMode = True
        
        # Variables for the event readout
        ## for the digitizer
        bsize = ctypes.c_uint32(0)
        numEvents = ctypes.c_uint32(0)
        
        # Readout HW loop
        while self.acquisitionMode:
            if self.daqLoop:
                # Send single SW trigger
                # print("Send a SW Trigger:", self.libCAENDigitizer.CAEN_DGTZ_SendSWtrigger(self.handle)) # Send a SW Trigger
               
                # Read data payload from the digitizer
                ret = self.libCAENDigitizer.CAEN_DGTZ_ReadData(self.handle, ctypes.c_long(0), self.buffer, ctypes.byref(bsize))
                if ret==0:
                    # (self.logging).trace(f"CAEN_DGTZ_ReadData OK | {bsize.value} bytes")
                    pass
                else:
                    (self.logging).error("CAEN_DGTZ_ReadData failed")
                    self.daqLoop = False
                    self.acquisitionMode = False
                    self.eventReadout.put(None)
                    break
                
                # The buffer red from the digStart theitizer is used in the other functions to get the event data.
                # The following function returns the number of events in the buffer
                # Get the number of events
                ret = self.libCAENDigitizer.CAEN_DGTZ_GetNumEvents(self.handle, self.buffer, bsize, ctypes.byref(numEvents))
                # ret = self.libCAENX742DecodeRoutines.GetNumEvents(self.buffer, bsize, ctypes.byref(numEvents))
                if ret==0:
                    # (self.logging).trace(f"CAEN_DGTZ_GetNumEvents OK | {numEvents.value} events")
                    pass
                else:
                    (self.logging).error("CAEN_DGTZ_GetNumEvents failed")
                    self.daqLoop = False
                    self.acquisitionMode = False
                    self.eventReadout.put(None)
                    break

                # If the readout buffer contains any event, process the data
                if numEvents.value:
                    # Update data thoughput statistics
                    stats.update(bsize.value, numEvents.value, 1)
                    
                    # Process the buffer containing a certain number 'eventNb' of events 
                    self.processBuffer(bsize, numEvents)
            
                # If a limit on event number is set, the acquisition will be stopped after this number of events
                if (self.eventCutoff > 0) and (stats.getTotalEvents() >= self.eventCutoff):
                    self.daqLoop = False
                    (self.logging).info(f"Event cutoff reached ({stats.getTotalEvents()}/{self.eventCutoff}). Stopping HW loop...")
            
            # else:
            #     # signal that there are no further items
            #     self.eventReadout.put(None)
            #     break
            
            # Reduce CPU overhead
            time.sleep(0.040)
            
        # Close the acquisition
        ret = self.libCAENDigitizer.CAEN_DGTZ_SWStopAcquisition(self.handle)
        CAEN_DGTZ_ErrorHandler(ret)
        # (self.logging).trace("CAEN_DGTZ_SWStopAcquisition OK")

        # Free readout buffer
        ret = self.libCAENDigitizer.CAEN_DGTZ_FreeReadoutBuffer(ctypes.byref(self.buffer))
        CAEN_DGTZ_ErrorHandler(ret)
        # (self.logging).trace("CAEN_DGTZ_FreeReadoutBuffer OK")

    # Process the Event object
    def _processEvt(self, Evt: CAEN_DGTZ_X742_EVENT_t):
        eventReadoutItem = {'blockTimestamp': time.time(), 'TrgInfo': copy.copy(self.TrgInfo), 'data' : {}}
        
        for group in range(4):
            if Evt.GrPresent[group]:
                EvtGroup = Evt.DataGroup[group] 
                TriggerTimeTag = EvtGroup.TriggerTimeTag
                eventReadoutItem['data'].update({'TriggerTimeTag': np.array(TriggerTimeTag)})
                for j in range(9):
                    ChSize_ch = EvtGroup.ChSize[j]
                    DataChannel_ch = EvtGroup.DataChannel[j][0:ChSize_ch]
                    eventReadoutItem['data'].update({j : np.array(DataChannel_ch)})
        
        # Put the event object in the eventReadout queue
        (self.eventReadout).put(eventReadoutItem)        
        

    # Process the buffer and the events within   
    def processBuffer(self, bsize: ctypes.c_uint32, eventsNb: ctypes.c_uint32):
        """
        Process the readout buffer (char*) and unpack into the events
        """
        
        # Get the values for the bsize, eventsNb
        bsize = bsize.value
        eventsNb = eventsNb.value

        # Allocate the Event pointer
        ret = self.libCAENDigitizer.CAEN_DGTZ_AllocateEvent(self.handle, ctypes.byref(self.Evt))
        CAEN_DGTZ_ErrorHandler(ret)
        # (self.logging).trace("CAEN_DGTZ_AllocateEvent OK")

        # Unpack the events
        for i in range(0, eventsNb):
            # Get the event info
            ret = self.libCAENDigitizer.CAEN_DGTZ_GetEventInfo(self.handle, self.buffer, bsize, i, ctypes.byref(self.TrgInfo), ctypes.byref(self.evtptr))
            CAEN_DGTZ_ErrorHandler(ret)
            # (self.logging).trace(f"CAEN_DGTZ_GetEventInfo OK | Event {i}")
            ## Print the event info if in debug mode 
            if self.logging.level == 10: (self.logging).debug(self.TrgInfo.print())
            
            # The event pointer is already obtained with the EventInfo object
            # ret = self.libX742Decoder.GetEventPtr(self.buffer, bsize, i, ctypes.byref(self.evtptr))
            
            # Decode event into the Evt data ctypes.Structure
            ret = self.libCAENDigitizer.CAEN_DGTZ_DecodeEvent(self.handle, self.evtptr, ctypes.byref(self.Evt))
            # ret = self.libCAENX742DecodeRoutines.X742_DecodeEvent(self.evtptr, ctypes.byref(self.Evt))
            CAEN_DGTZ_ErrorHandler(ret)
            
            ########################################
            ########## Event elaboration ###########
            ########################################
            # Event elaboration
            Evt = self.Evt.contents
            self._processEvt(Evt)
            # self.eventContainer.append(myEvent)
            ########################################
            ########## /Event elaboration ##########
            ########################################
        #
        # Deallocate the Event memory
        ret = self.libCAENDigitizer.CAEN_DGTZ_FreeEvent(self.handle, ctypes.byref(self.Evt))
        CAEN_DGTZ_ErrorHandler(ret)
        # (self.logging).trace("CAEN_DGTZ_FreeEvent OK")


    # Close the connection with the digitizer
    def close(self):
        """
        Close the connection with the digitizer
        """
        
        # Make sure the HW readout loop exited 
        self.lock.acquire()
        # (self.logging).trace("Acquiring lock to stop the HW loop...")
        self.acquisitionMode = False
        self.lock.release()

        print("CAEN_DGTZ_CloseDigitizer", self.handle)
        ret = self.libCAENDigitizer.CAEN_DGTZ_CloseDigitizer(self.handle)
        CAEN_DGTZ_ErrorHandler(ret)
        # (self.logging).trace("CAEN_DGTZ_CloseDigitizer OK")
      


    #####################################################################################################################
    #################################### Auxiliary methods (calibration and testing) ####################################
    #####################################################################################################################
    
    # Get the waveform with absolute units (timestamp, value) [s, V]
    def calibrated(self, waveform: np.ndarray) -> np.ndarray:
        #timestamps = np.linspace(0, 327.66e-6, 163830)
        return waveform/self.dacFSR*1.0 - 0.5 + self.ChannelDCOffset_V
    
    
    def findCalibration(self, wave, levels = (1.52e-3, 506.0e-3)):
            raise Exception("Implement me")
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
        
    
    ##########################################################################################################################################################################################################################################
    ############################## Debug methods ############################################################### Debug methods ############################################################### Debug methods #################################
    ##########################################################################################################################################################################################################################################
    eventContainer = []
    trgTimetags = []
    
    # Plot
    def plotWaveform(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.set(xlabel = "time (s)", ylabel = "ADC value", title = "First event of the readout")
        axx = ax.twinx()
        axx._get_patches_for_fill.get_next_color()
        axx.set_ylabel("voltage (V)")
        fig.suptitle("Waveform display")

        # Get the event
        eventReadoutItem = self.eventReadout.get()
        if eventReadoutItem is None:
            (self.logging).warning("No event in the readout, but None exit signal found!")
            return
        
        # Print the event readout item
        print(f"blockTimestamp:                 {eventReadoutItem['blockTimestamp']}")
        eventReadoutItem['TrgInfo'].print()
        print(f"TriggerTimeTag:                 {eventReadoutItem['data']['TriggerTimeTag']}")
        print(f"There are {len(eventReadoutItem['data'])-1} channels data. They are channels: {list(eventReadoutItem['data'])[0:]}")

        # print(self.ChannelDCOffset_ADC, self.ChannelDCOffset_V)
        # self.ChannelDCOffset_ADC = 2**15-16300

        waveformtime = np.linspace(0, 1024*self.SamplingPeriod_s, 1024)
        for ch in range(9):
            if ch in eventReadoutItem['data']:
                waveformData = eventReadoutItem['data'][ch]
                if len(waveformData) == 0: continue
                ax.plot(waveformtime, waveformData, label=f"channel {ch}")
                axx.plot(waveformtime, waveformData/self.dacFSR*1.0 - 0.5 + self.ChannelDCOffset_V)
                # axx.plot(waveformtime, (waveformData-self.dacFSR/2)/(self.dacFSR) - self.ChannelDCOffset_V)
            
        ax.legend(loc="upper right")
        fig.show()
        fig.savefig("waveform.png")
    
    # Debug - Function to test the class
    def testClass(self, eventCutoff: int):
        # Set the event cutoff
        self.eventCutoff = eventCutoff
        # Open digitizer
        self.open()
        # Setup digitizer
        # self.setup_DT5742B(
        #     SWTriggerMode           = CAEN_DGTZ_TriggerMode_t.CAEN_DGTZ_TRGMODE_DISABLED,
        #     ExtTriggerInputMode     = CAEN_DGTZ_TriggerMode_t.CAEN_DGTZ_TRGMODE_ACQ_ONLY,
        #     RunSyncMode             = CAEN_DGTZ_RunSyncMode_t.CAEN_DGTZ_RUN_SYNC_Disabled,
        #     IOLevel                 = CAEN_DGTZ_IOLevel_t.CAEN_DGTZ_IOLevel_TTL,
        #     TriggerPolarity         = CAEN_DGTZ_TriggerPolarity_t.CAEN_DGTZ_TriggerOnRisingEdge,
        #     DRS4Frequency           = CAEN_DGTZ_DRS4Frequency_t.CAEN_DGTZ_DRS4_750MHz,
        #     OutputSignalMode        = CAEN_DGTZ_OutputSignalMode_t.CAEN_DGTZ_TRIGGER,
        #     AcqMode                 = CAEN_DGTZ_AcqMode_t.CAEN_DGTZ_SW_CONTROLLED,
        #     GroupEnableMask         = 0b1,
        #     RecordLength            = 1024,
        #     PostTriggerSizePercent  = 100,
        #     ChannelDCOffset         = (2**15)
        # )
        self.setupSimple_DT5742(windowSize_s=500.0e-9, channelDCOffset_V=-0.25)
        # self.setup_DT5742BDefault()
        # Open acquisition
        self.acquireLoop()
        # Close digitizer
        self.close()
        # Plot waveform
        self.plotWaveform()
        
    # Debug - Function to test the class
    def testClassWaveform(self, eventCutoff: int):
        self.eventCutoff = eventCutoff
        # Open acquisition
        self.acquireLoop()
        # Close acquisition
        self.closeAcquire()       
        # Close digitizer
        self.close()
        # Plot waveform
        self.plotWaveform()
    ##########################################################################################################################################################################################################################################
    ############################## /Debug methods ############################################################### /Debug methods ############################################################### /Debug methods ##############################
    ##########################################################################################################################################################################################################################################