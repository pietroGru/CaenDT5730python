from array import array
from logger import *
import numpy as np
import ROOT
import time

from caendt5730 import CAENDT5730
CAEN_DGTZ_BoardInfo_t = CAENDT5730.CAEN_DGTZ_BoardInfo_t
del CAENDT5730


##############################################################
######## rootconverter class #################################
##############################################################
class rootconverter():
    def __init__(self, path = "/home/pietro/work/CLEAR_March/DT5730/clear/", jobEvents=1000, dgtCalibration = [0.00012782984648295086,-1.0470712607404515], bgzGain = 32, periodTrg=20) -> None:
        logging.debug(f"rootlogger. Output dir: {path}. Run is made of {jobEvents} events.")
        self.fname = ""
        self.outputROOTdirectory = path
        # Number of events for every file
        self.jobEvents = jobEvents
        # Run ID (from file), path of the filename of the data file and info file
        self.runID = -1
        # Number of channels in the energy histogram
        self.histoCh = -1
        # Window start/stop position in samples
        self.avgWindow = (-5000,-1)
        #
        self.eventID = 0
        self.startTime = -1
        self.stopTime = -1
        self.elapsedTime = -1
        #
        self.parseLineData_prev = []
        self.strData_prev = ["-1" for i in range(6)]
        # Global variables for ROOT filesaving
        self.rfile = None               # pointer to the ROOT TFile
        self.runSetupTree = None        # setup ttree
        self.runDataTree = None         # data ttree
        self.runDataTreeRaw = None      # raw data ttree
        self.rFileOpen = False 
        # TTree: setup
        self.vrunIDs = ROOT.vector('int')()
        self.vparName = ROOT.vector('string')()
        self.vparValue = ROOT.vector('string')()
        self.vparDescr = ROOT.vector('string')()
        # TTree: dataRaw
        self.irun = array("i", [-1])
        self.irunTime = array("Q", [0])
        self.ievent = array("i", [-1])
        self.ftimestamp = array("d", [-1])
        self.fTrgTstamp_us = array("d", [-1])
        self.iTrgID = array("i", [-1])
        self.vwaveform = ROOT.vector('int')()
        self.vwaveformTime = ROOT.vector('int')()
        
        # Digitizer calibration data (ADC to volt)
        self.cal_m = dgtCalibration[0] 
        self.cal_q = dgtCalibration[1] 
        # Bergoz calibration data
        # Table is 6,12...dB and it contains V/nC
        bgzCLEARCal = {
           #6  : 2.085,
           #12 : 4.180,
           #18 : 8.350,
           #20 : 10.42,
           #26 : 20.95,
            32 : 4.190#/2.0,
            #40 : 105.0
            } 
        # storing the actual one
        self.bgz_m = bgzCLEARCal[bgzGain]
        self.bgz_q = 0
        # The calculated average charge [in nC]
        self.avgQ = 0
        self.avgV = 0

        # Save the waveform every N triggers
        self.periodTrg = periodTrg

    def __del__(self):
        self.clear_runSetupTreeVectors()
        self.clear_runDataTreeRawVectors()
        logging.info("[rootconverter] Memory cleared")

    # Set the output directory of the ROOT files
    def setOutputROOTDir(self, path: str):
        if path[-1] != '/':
            path = path + '/' 
        self.outputROOTdirectory = path
    
    # Set the gating of the averaging window
    def setAvgGatingWindow(self, window):
        self.avgWindow = window
        logging.warning(f"Averaging window request to {self.avgWindow}. Make sure samples are enough")
     
    # Process the waveform
    def _dsp_processWaveform(self, waveform = np.array([0])):
        gateWindow = waveform[self.avgWindow[0]:self.avgWindow[1]]
        avg = gateWindow.mean()
        std = gateWindow.std()
        ptNb = self.avgWindow[1]-self.avgWindow[0]
        return (avg, std, ptNb)
    
    # Apply the calibration to convert from ADC value to absolute voltage
    def _dsp_applyCalibration(self, prcWavOut : tuple):
        avgV = prcWavOut[0] * self.cal_m + self.cal_q
        stdV = prcWavOut[1]
        self.avgQ = avgV/self.bgz_m + self.bgz_q 
        return (avgV, stdV, self.avgQ)
    

    # Boolean flag checker for the waveform saving feature of the event
    def waveformTimer(self):
        if self.periodTrg<0:
            return False
        elif self.eventID % self.periodTrg == 0:
            return True
        else:
            return False
    
    # Parse the single event line
    def _dsp_storeEventROOT(self, info, waveform: list, trg0Time):
        # Event info (header of the dgt payload)
        # Get the event info
        evtInfo = (info).toDict()
        dgt_evt = evtInfo["EventCounter"]
        dgt_trgtime = evtInfo["TriggerTimeTag"]
        dgt_evtsize = evtInfo["EventSize"]      

        # Calculate the average value, standard deviation and number of points in the average. Based on raw values (samples)
        avg, std, ptNb = self._dsp_processWaveform(waveform)
        # Get calibrated values in V
        self.avgV, stdV, self.avgQ = self._dsp_applyCalibration((avg, std, ptNb))      
        #(TrgTstamp_us, TrgID, avg, std, ptNb, avgV, stdV, avgQ)
        trgtime = trg0Time #to be calculated
        runTime = time.time_ns()
        # If this flag is enable, then store the entire waveform in the dedicated TTree
        if self.waveformTimer():
            # TODO implement
            # Generate timetags
            #timetags = np.linspace(0, evtInfo["EventSize"])
            # Dump waveform on the TTree
            self.irun[0] = self.runID
            self.irunTime[0] = runTime
            self.ievent[0] = self.eventID
            self.ftimestamp[0] = trgtime
            self.fTrgTstamp_us[0] = dgt_trgtime
            self.iTrgID[0] = 0
            for i, adc in enumerate(waveform):
                self.vwaveformTime.push_back(int(i))
                self.vwaveform.push_back(int(adc)) 
            self.runDataTreeRaw.Fill()
            self.clear_runDataTreeRawVectors()
            #
        
        # Data object
        if self.rFileOpen:
            self.runDataTree.Fill(self.runID, runTime, self.eventID, dgt_evt, dgt_trgtime, dgt_evtsize, avg, std, ptNb, self.avgV, stdV, self.avgQ, trgtime)
            self.eventID += 1
        return 0

    # Clear rundataRaw vectors
    def clear_runDataTreeRawVectors(self):
        self.vwaveform.clear()
        self.vwaveformTime.clear()
    # Clear setup vectors
    def clear_runSetupTreeVectors(self):
        self.vrunIDs.clear()
        self.vparName.clear()
        self.vparValue.clear()
        self.vparDescr.clear()

    # Create the "a:b:c" string that describes the root data structure of say a TTree
    def _utils_mkRootTtreeDefineFromDict(self, input: dict) -> str:
        result = ""
        for item in list(input.keys()):
            result += f"{item}:"
        return result[:-1]
    # Set description (better readibility)
    def _utils_mkRootTtreeHumanDescrFromDict(self, tree, tree_nametypes):
        # If a branch name is not compatible with ROOT name conventions, the
        # name is first sanified and then a branch with that name is created.
        # For example 'myname2.' cannot exist
        # A naive comparison like 
        # for entry in tree_nametypes:
        #     tree.GetBranch(entry[0]).SetTitle(entry[3])
        # would fail since the GetBranch for 'myname2.' would return nullpointer

        # WARNING: using GetLeaf works but it produces a bug in the generated ROOT output
        # file such that the Data is not displayed when using sca. With the traditional TBrowser
        # it won't work either while with the web ROOT interface it works.

        for entry in tree_nametypes:
                try:
                    branch = tree.GetBranch(entry[0])
                    branch.SetTitle(entry[3])
                except ReferenceError:
                    (self.logging).error(f"Branch {entry[0]} not found. This is nullptr")



    # Prepare the ROOT file
    def prepareROOT(self, fname: str):
        # Set filename
        self.fname = fname
        #
        self.rfile = ROOT.TFile.Open(self.outputROOTdirectory+self.fname, "RECREATE")
        # Create TTree to store run setup data
        self.runSetupTree = ROOT.TTree('DT5730setup', 'TTree with run DT5730 setup settings')
        self.runSetupTree.Branch("run", self.vrunIDs)
        self.runSetupTree.Branch("parName", self.vparName)
        self.runSetupTree.Branch("parValue", self.vparValue)
        self.runSetupTree.Branch("parDescr", self.vparDescr)
        logging.debug(self.runSetupTree)
        # Create TTree to store run datapoints (TrgTstamp_us, TrgID, avg, std, ptNb, avgV, stdV, avgQ)
        setupEntries = {
            "run"         : "Run id number",
            "runTime"     : "Posix time of the run start on the PC",
            "event"       : "Event id number",
            "dgt_evt"     : "Dgt event counter",
            "dgt_trgtime" : "Dgt trg counter [32-bit counter, 8ns res., 17.179s range]",
            "dgt_evtsize" : "Number of samples in the waveform [1sample=2ns]",
            "avg"         : f"Average ADC value in window ({self.avgWindow[0]}:{self.avgWindow[1]}) [0-16383]",
            "std"         : "Standard deviation ADC values [0-16383]",
            "ptNb"        : "Number of points in the avgGatingwindow [#]",
            "avgV"        : "Average voltage in the window [V]",
            "stdV"        : "Standard deviation in the window [V]",
            "avgQ"        : "Average cal. charge in the window [nC]",
            "trgtime"     : "Dgt trg counter converted in time using runTime as T0 start"
        }
        self.runDataTree = ROOT.TNtuple("DT5730", "DT5730 processed data", self._utils_mkRootTtreeDefineFromDict(setupEntries))
        # Description for the various entries
        self._utils_mkRootTtreeHumanDescrFromDict(self.runDataTree, setupEntries)
        # Raw waveforms (saved only some times)
        self.runDataTreeRaw = ROOT.TTree("DT5730raw", "DT5730 raw values")
        self.runDataTreeRaw.Branch("run",          self.irun            , "run/I")
        self.runDataTreeRaw.Branch("runTime",      self.irunTime        , "runTime/I")
        self.runDataTreeRaw.Branch("event",        self.ievent          , "event/I")
        self.runDataTreeRaw.Branch("timestamp",    self.ftimestamp      , "timestamp/I")
        self.runDataTreeRaw.Branch("TrgTstamp_us", self.fTrgTstamp_us   , "TrgTstamp_us/I")
        self.runDataTreeRaw.Branch("TrgID",        self.iTrgID          , "TrgID/I")
        self.runDataTreeRaw.Branch("waveform",     self.vwaveform)
        self.runDataTreeRaw.Branch("waveformTime", self.vwaveformTime)
        logging.debug(self.runDataTreeRaw)
        # Clear runSetup vectors
        self.clear_runSetupTreeVectors()
        # Set the ROOT file status to open
        self.rFileOpen = True

    # Close the instance of the ROOT file currently open
    def closeROOT(self):
        if self.rFileOpen:
            self.runSetupTree.Write()
            self.runDataTree.Write()
            self.runDataTreeRaw.Write()
            self.rfile.Close()
            self.rFileOpen = False
            self.eventID = 0
        logging.debug("closeROOT")

    # Get run info parsing
    def processRunInfo(self, stream: CAEN_DGTZ_BoardInfo_t):
        if stream is None:
            logging.warning("processRunInfo is None")
            return
        # Fill the self.runInfo var
        for item in stream.getBrdInfo():
            # For ROOT
            self.vrunIDs.push_back(self.runID)
            self.vparName.push_back(item[0])
            self.vparValue.push_back(item[1])
            self.vparDescr.push_back("")
        # Fill the data on the TTree
        self.runSetupTree.Fill()
        logging.info(f"ROOT file {self.fname} saved")
       

    # Check if the run has been completed (condition verified when the info file is written)
    def isRunClosed(self):
        if self.eventID > self.jobEvents:
            return True
        else:
            return False

    def updateRunID(self, id):
        self.runID = id       
##############################################################
######## / rootconverter class ###############################
##############################################################