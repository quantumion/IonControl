#Functions/TrapFunctions.py created 2020-08-30 17:15:52.614551
import numpy as np
import sys
import time
sys.path.append(r'C:\Users\ions\Documents\IonControl\scripting')
from Script import *

FreqSetTime = 1

def IsotopeFreqs(Isotope):
    #Ba138 Freqs
    Freq493_Ba138 = 607.42596
    Freq650_Ba138 = 461.31204
    Freq553_Ba138 = 541.43290
    #Ba137 Freqs
    Ba137Offset493 = 20e-6
    Freq493_Ba137 = round(Freq493_Ba138 + Ba137Offset493, 5)
    Ba137Offset650 = 80e-6
    Freq650_Ba137 = round(Freq650_Ba138 + Ba137Offset650, 5)
    Ba137Offset553 = 275e-6
    Freq553_Ba137 = round(Freq553_Ba138 + Ba137Offset553, 5)
    #Ba133 Freqs
    Ba133Offset493 = 0
    Freq493_Ba133 = round(Freq493_Ba138 + Ba133Offset493, 5)
    Ba133Offset650 = 500e-6
    Freq650_Ba133 = round(Freq650_Ba138 + Ba133Offset650, 5)
    Ba133Offset553 = 390e-6
    Freq553_Ba133 = round(Freq553_Ba138 + Ba133Offset553, 5)
    if Isotope == "Ba138":
        Freqs = (Freq493_Ba138, Freq650_Ba138, Freq553_Ba138)
    elif Isotope == "Ba137":
        Freqs = (Freq493_Ba137, Freq650_Ba137, Freq553_Ba137)
    elif Isotope == "Ba133":
        Freqs = (Freq493_Ba133, Freq650_Ba133, Freq553_Ba133)
    return Freqs

def GetPMTCounts(CountProgram, setScan, startScan, stopScan, getAllData):
    setScan(CountProgram)
    startScan(globalOverrides=list(), wait=True)
    time.sleep(0.05)
    data = getAllData()['PMT Count'] #Returns all data associated with scan.
    ydata = data[1]
    ydataAvg = np.mean(np.array(ydata))
    ydataStD = np.std(np.array(ydata))
    stopScan()   
    return (ydataAvg, ydataStD)
    
def FlushTrapRF(setScan, startScan, stopScan):
    setScan("FlushTrap")
    startScan(globalOverrides=list(), wait=True)
    stopScan()
    
def SetGlobalLaserFreqs(Isotope, getGlobal, setGlobal):
    CoolingFreq, RepumpFreq, IonizationFreq = (getGlobal("CoolingFreq"), getGlobal("RepumpFreq"), getGlobal("IonizationFreq"))
    (Freq493, Freq650, Freq553) = IsotopeFreqs(Isotope)
    if not "%s"%CoolingFreq == "%s THz"%Freq493:
        setGlobal("CoolingFreq", Freq493, "THz")
        time.sleep(FreqSetTime)
    if not "%s"%RepumpFreq == "%s THz"%Freq650:
        setGlobal("RepumpFreq", Freq650, "THz")
        time.sleep(FreqSetTime)
    if not "%s"%IonizationFreq == "%s THz"%Freq553:
        setGlobal("IonizationFreq", Freq553, "THz")
        time.sleep(FreqSetTime)
    return (Freq493, Freq650, Freq553)
        
def SetCoolLaserFreqs(Isotope, getGlobal, setGlobal):
    CoolingFreq, RepumpFreq = (getGlobal("CoolingFreq"), getGlobal("RepumpFreq"))
    (Freq493, Freq650, Freq553) = IsotopeFreqs(Isotope)
    if not "%s"%getGlobal("CoolingFreq") == "%s THz"%Freq493:
        setGlobal("CoolingFreq", Freq493, "THz")
        time.sleep(FreqSetTime)
    if not "%s"%getGlobal("RepumpFreq") == "%s THz"%Freq650:
        setGlobal("RepumpFreq", Freq650, "THz")
        time.sleep(FreqSetTime)
    return (Freq493, Freq650, Freq553)
        
def SweepCool493(Freq, CoolSweepsNum, getGlobal, setGlobal):
    TimeSwitchFreq = getGlobal("TimeSwitchLaserFreqWM")
    TimeCool = getGlobal("TimeCoolBeforeCheck")
    FreqMove1 = Freq - 0.00001
    FreqMove2 = Freq
    FreqChange = FreqMove1
    for i in range(0, CoolSweepsNum):
        cmd = "i=%i, FreqChange=%f"%tuple([i, FreqChange])
        os.system(cmd)
        setGlobal("CoolingFreq",FreqChange,"THz")
        time.sleep(TimeSwitchFreq)
        if i%2 == 1:
            FreqChange = FreqMove1
        else:
            FreqChange = FreqMove2
    time.sleep(TimeCool)
    if not "%s"%getGlobal("CoolingFreq") == "%s THz"%Freq:
        setGlobal("CoolingFreq", Freq, "THz")
        time.sleep(FreqSetTime)
    
    
def CheckIonTrapped(BGyAvg, BGyStDev, yAvg, Count, Isotope, getGlobal, setGlobal):
    BGNumStDevs = getGlobal("BGCheckNumStDevs")
    if not (BGyAvg - BGNumStDevs*BGyStDev < yAvg < BGyAvg + BGNumStDevs*BGyStDev):
        if Isotope == "Ba138":
            IonTrapped = True
            os.system("C:/Users/ions/Documents/Beep.bat")
            cmd = "start /wait cmd /k echo Ion trapped, with %f counts average. Total ablation pulses: %i"%tuple([yAvg, Count])
            os.system(cmd)
        elif Isotope == "Ba137" or Isotope == "Ba133":
            #Move cooling freqs to Ba138 freqs
            (Freq493_Ba138, Freq650_Ba138, Freq553_Ba138) = SetCoolLaserFreqs("Ba138", getGlobal, setGlobal)
            #Get counts with Ba138 freqs, and EOMs turned off
            (yAvg_Ba138, yStD_Ba138) = GetPMTCounts("PMT_CheckCounts_For-Script_Even")
            
            if (BGyAvg - BGNumStDevs*BGyStDev < yAvg_Ba138 < BGyAvg + BGNumStDevs*BGyStD):
                #Return to Isotope Freqs
                if Isotope == "Ba137":
                    (Freq493_Ba137, Freq650_Ba137, Freq553_Ba137) = SetCoolLaserFreqs("Ba137", getGlobal, setGlobal)
                else:
                    (Freq493_Ba133, Freq650_Ba133, Freq553_Ba133) = SetCoolLaserFreqs("Ba133", getGlobal, setGlobal)
            IonTrapped = True
            os.system("C:/Users/ions/Documents/Beep.bat")
            cmd = "start /wait cmd /k echo Ion trapped, with %f counts average. Total ablation pulses: %i. With Ba138 settings, counts are %f average."%tuple([yAvg, Count, ydataAvg_Ba138])
            os.system(cmd)
    else:
        IonTrapped = False
    return IonTrapped