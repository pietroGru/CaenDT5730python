#################################################################################################
# @info Script to simulate production of events from the digitizer at a given trigger rate      #
#       DT5742B producer. The bytes in the Event's payload contains the data collected by the   #
#       digitizer.                                                                              #
# @author   Pietro Grutta (pietro.grutta@pd.infn.it)                                            #
# @date     03/04/2024                                                                          #
#                                               more text here eventually                       #
#                                               more text here eventually                       #
#                                               more text here eventually                       #
#################################################################################################
from caendt5742b import CAENDT5742B
import threading
import queue


import numpy as np
import pyeudaq
import time

## DT5742B datatype
dt5742b_dtypes = [('run',np.uint32),('runTime',np.float64),('event',np.uint32),('timestamp',np.float64),('dgt_evt',np.uint32),('dgt_trgtime',np.uint64),('dgt_evtsize',np.uint32),('avg',np.float64),('std',np.float64),('ptNb',np.uint32),('avgV',np.float64),('stdV',np.float64),('avgQ',np.float64)]
dt5742bStruct = np.zeros(1, dtype=dt5742b_dtypes)


# Catch exceptions and forward the exception emssage to the EUDAQ log collector
def exception_handler(method):
    def inner(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception as e:
            pyeudaq.EUDAQ_ERROR(str(e))
            raise e
    return inner



class dt5742bEUDAQ(pyeudaq.Producer):
    def __init__(self, name, runctrl):
        super().__init__(name, runctrl)        
        self.is_running = 0
        pyeudaq.EUDAQ_INFO('New instance of dt5742bEUDAQ')

        # Event readout queue buffer
        self.eventsReadout = queue.Queue()

    @exception_handler
    def DoInitialise(self):        
        pyeudaq.EUDAQ_INFO('DoInitialise')
        #print 'key_a(init) = ', self.GetInitItem("key_a")
        

    @exception_handler
    def DoConfigure(self):        
        pyeudaq.EUDAQ_INFO('DoConfigure')
        
        # Get the configuration from the ini section for the a1561hdp
        confDict = self.GetConfiguration().as_dict()
        ## Checks that all the required keys are present
        for key in ['usbLinkID','SWTriggerMode','ExtTriggerInputMode','RunSyncMode','IOLevel','TriggerPolarity','DRS4Frequency','OutputSignalMode','AcqMode','GroupEnableMask','RecordLength','PostTriggerSizePercent','ChannelDCOffset']:
            if key not in confDict: raise Exception(f"Configuration file does not contain {key}")
        
        CAEN_DGTZ_TriggerMode_t = {'CAEN_DGTZ_TRGMODE_DISABLED' : 0, 'CAEN_DGTZ_TRGMODE_EXTOUT_ONLY' : 2, 'CAEN_DGTZ_TRGMODE_ACQ_ONLY' : 1, 'CAEN_DGTZ_TRGMODE_ACQ_AND_EXTOUT' : 3}
        CAEN_DGTZ_RunSyncMode_t = {'CAEN_DGTZ_RUN_SYNC_Disabled': 0, 'CAEN_DGTZ_RUN_SYNC_TrgOutTrgInDaisyChain': 1, 'CAEN_DGTZ_RUN_SYNC_TrgOutSinDaisyChain': 2, 'CAEN_DGTZ_RUN_SYNC_SinFanout': 3, 'CAEN_DGTZ_RUN_SYNC_GpioGpioDaisyChain': 4}
        CAEN_DGTZ_IOLevel_t = {'CAEN_DGTZ_IOLevel_NIM' : 0, 'CAEN_DGTZ_IOLevel_TTL' : 1}
        CAEN_DGTZ_TriggerPolarity_t = {'CAEN_DGTZ_TriggerOnRisingEdge' : 0, 'CAEN_DGTZ_TriggerOnFallingEdge' : 1}
        CAEN_DGTZ_DRS4Frequency_t = {'CAEN_DGTZ_DRS4_5GHz' : 0, 'CAEN_DGTZ_DRS4_2_5GHz' : 1, 'CAEN_DGTZ_DRS4_1GHz' : 2, 'CAEN_DGTZ_DRS4_750MHz' : 3, '_CAEN_DGTZ_DRS4_COUNT_' : 4}
        CAEN_DGTZ_OutputSignalMode_t = {'CAEN_DGTZ_TRIGGER' : 0, 'CAEN_DGTZ_FASTTRG_ALL' : 1, 'CAEN_DGTZ_FASTTRG_ACCEPTED' : 2, 'CAEN_DGTZ_BUSY' : 3}
        CAEN_DGTZ_AcqMode_t = {'CAEN_DGTZ_SW_CONTROLLED' : 0,'CAEN_DGTZ_S_IN_CONTROLLED' : 1,'CAEN_DGTZ_FIRST_TRG_CONTROLLED' : 2}
        
        usbLinkID = int(confDict['usbLinkID'])
        dt5742bConfiguration = {
            'SWTriggerMode' : CAEN_DGTZ_TriggerMode_t[confDict['SWTriggerMode']],
            'ExtTriggerInputMode' : CAEN_DGTZ_TriggerMode_t[confDict['ExtTriggerInputMode']],
            'RunSyncMode' : CAEN_DGTZ_RunSyncMode_t[confDict['RunSyncMode']],
            'IOLevel' : CAEN_DGTZ_IOLevel_t[confDict['IOLevel']],
            'TriggerPolarity' : CAEN_DGTZ_TriggerPolarity_t[confDict['TriggerPolarity']],
            'DRS4Frequency' : CAEN_DGTZ_DRS4Frequency_t[confDict['DRS4Frequency']],
            'OutputSignalMode' : CAEN_DGTZ_OutputSignalMode_t[confDict['OutputSignalMode']],
            'AcqMode' : CAEN_DGTZ_AcqMode_t[confDict['AcqMode']],
            'GroupEnableMask' : int(confDict['GroupEnableMask'], 2),
            'RecordLength' : int(confDict['RecordLength']),
            'PostTriggerSizePercent' : int(confDict['PostTriggerSizePercent']),
            'ChannelDCOffset' : int(confDict['ChannelDCOffset'], 16)
        }
        print("dt5742bConfiguration", dt5742bConfiguration)

        # # Instance the CAENDT5742B controller class
        self.dgt = CAENDT5742B(usbLinkID = usbLinkID, evtReadoutQueue = self.eventsReadout, eventCutoff=25)
        try:
            self.dgt.open()
        except Exception as e:
            if e.args[0] == "CAEN_DGTZ_DigitizerAlreadyOpen - The Digitizer is already open": # -25 : ('CAEN_DGTZ_DigitizerAlreadyOpen', 'The Digitizer is already open')
                pyeudaq.EUDAQ_WARN('The Digitizer is already open')
            else:
                raise e
        self.dgt.setup_DT5742B(**dt5742bConfiguration)
        # Run the acquisition loop thread
        self.dgtHWLoopThread = threading.Thread(target=self.dgt.acquireLoop, args=(), daemon=True)
        self.dgtHWLoopThread.start()
        

    @exception_handler
    def DoStartRun(self):
        pyeudaq.EUDAQ_INFO('DoStartRun')
        self.is_running = 1
        self.dgt.setDaqLoop(True)
        
        # Set the run number
        dt5742bStruct['run'] = self.GetRunNumber()
        dt5742bStruct['runTime'] = time.time()
        
        
    @exception_handler
    def DoStopRun(self):
        pyeudaq.EUDAQ_INFO('DoStopRun')
        self.is_running = 0
        self.dgt.setDaqLoop(False)
        print("DoStopRun")


    @exception_handler
    def DoReset(self):        
        pyeudaq.EUDAQ_INFO('DoReset')
        self.is_running = 0
        if hasattr(self, 'hwLoopThread'):
            self.dgt.lock.acquire()
            self.dgt.daqLoop = False
            self.dgt.acquisitionMode = False
            self.dgt.lock.release()
            self.dgtHWLoopThread.join()
            self.eventsReadout.put(None)
            print("A")
            del self.dgtHWLoopThread
            print("B")

    def GetRunNumber(self):
        pyeudaq.EUDAQ_WARN('MEMO: UPLOAD new eudaq sw')
        return 0


    def bergozMap_toCharge(self, voltage):
        return voltage * 50.0


    def processEvent(self, event: int, dgtEventItem: dict):
        if 'data' not in dgtEventItem: return
        
        waveformtime = self.dgt.waveformtime
        waveformData = dgtEventItem['data'][0]
        
        dt5742bStruct['event'] = event
        dt5742bStruct['timestamp'] = dgtEventItem['data']['TriggerTimeTag']
        dt5742bStruct['dgt_evt'] = dgtEventItem['TrgInfo'].EventCounter
        dt5742bStruct['dgt_trgtime'] = dgtEventItem['TrgInfo'].EventCounter
        dt5742bStruct['dgt_evtsize'] = len(waveformData)
        
        # Calculate the average value over the last 100 samples (dirty)
        dt5742bStruct['avg'] = np.mean(waveformData[:-100])
        dt5742bStruct['std'] = np.std(waveformData[:-100])
        dt5742bStruct['ptNb'] = 100
        dt5742bStruct['avgV'] = self.dgt.calibrated(dt5742bStruct['avg'])
        dt5742bStruct['stdV'] = self.dgt.calibrated(dt5742bStruct['std'])
        
        dt5742bStruct['avgQ'] = self.bergozMap_toCharge(dt5742bStruct['avgV'])


    @exception_handler
    def RunLoop(self):
        pyeudaq.EUDAQ_INFO("Start of RunLoop in dt5742bEUDAQ")
        trigger_n = 0
        while(self.is_running):
            # Get an event from the queue
            preQueryTime = time.time_ns()
            dgtEvent = self.eventsReadout.get()
            postQueryTime = time.time_ns()
            if dgtEvent is None: break
            
            self.processEvent(trigger_n, dgtEvent)
            
            # The basler is used in the DataCollector to tag the Event payload as coming from the camera
            ev = pyeudaq.Event("RawEvent", "dt5742b")
            ev.SetTriggerN(trigger_n)
            ev.SetTimestamp(preQueryTime, postQueryTime)
            ev.AddBlock(0, dt5742bStruct.tobytes())
            self.SendEvent(ev)
            
            trigger_n += 1
        pyeudaq.EUDAQ_INFO("End of RunLoop in dt5742bEUDAQ")


    @exception_handler
    def DoTerminate(self):
        pyeudaq.EUDAQ_INFO('DoTerminate')
        self.is_running = 0
        if hasattr(self, 'hwLoopThread'):
            self.dgt.lock.acquire()
            self.dgt.daqLoop, self.dgt.acquisitionMode = False
            self.dgt.lock.release()
            self.dgtHWLoopThread.join()
            (self.dgt).close()
            self.eventsReadout.put(None)
            del self.dgtHWLoopThread


if __name__ == "__main__":
    dt5742bProducer = dt5742bEUDAQ("dt5742b", "tcp://localhost:44000")
    print ("connecting to runcontrol in localhost:44000", )
    dt5742bProducer.Connect()
    time.sleep(2)
    while(dt5742bProducer.IsConnected()):
        time.sleep(1)
