#Ba138_LoadSingle.py created 2020-08-26 20:29:28.755609

import numpy as np
import os

def GetCounts(CountProgram):
    setScan(CountProgram)
    startScan(globalOverrides=list(), wait=True)
    data = getAllData()['PMT Count'] #Returns all data associated with scan.
    ydata = data[1]
    ydataAvg = np.mean(np.array(ydata))
    ydataStD = np.std(np.array(ydata))
    stopScan()   
    return (ydataAvg, ydataStD)

CurrLoadAttempts = getGlobal("LoadAttempts")
if int(CurrLoadAttempts) != 0:
    setGlobal("LoadAttempts", 0, "")
CycleLimit = getGlobal("MaxTrapAttemps")
GUILoadAttempts = getGlobal("LoadAttempts")
IonTrapped = False
TimeSwitchFreq = getGlobal("TimeSwitchLaserFreqWM")
TimeCool = getGlobal("TimeCoolBeforeCheck")
CoolSweepsNum = int(getGlobal("NumCoolSweeps"))
BGNumStDevs = getGlobal("BGCheckNumStDevs")
BGCountsProgram = "PMT_CheckCounts_For-Script_BG"
CountsProgram = "PMT_CheckCounts_For-Script_Even"
PulseAblationProgram = "PulseAblation_For-Script_Even_Nat"
PulseAblationDummyProgram = "PulseAblation_For-Script_Dummy_Ba138"

#Ba138 Freqs
Freq493 = 607.42596
Freq650 = 461.31205
Freq553 = 541.43293
#Freq553 = round(541.43293 + 275e-6, 5)

#Params for cool sweep
FreqMove2 = Freq493
FreqMove1 = FreqMove2 - 0.00001


#Get BG counts data
(BGydataAvg, BGydataStD) = GetCounts(BGCountsProgram)    

if not "%s"%getGlobal("CoolingFreq") == "%s THz"%Freq493:
    setGlobal("CoolingFreq", Freq493, "THz")
    time.sleep(1)
if not "%s"%getGlobal("RepumpFreq") == "%s THz"%Freq650:
    setGlobal("RepumpFreq", Freq650, "THz")
    time.sleep(1)
if not "%s"%getGlobal("IonizationFreq") == "%s THz"%Freq553:
    setGlobal("IonizationFreq", Freq553, "THz")
    time.sleep(1)
 
Count = 0
while not IonTrapped  and Count < CycleLimit:
    if scriptIsStopped():
        break
        
    setScan("FlushTrap")
    startScan(globalOverrides=list(), wait=True)
    stopScan()
    setScan(PulseAblationProgram)
    startScan(globalOverrides=list(), wait=True)
    stopScan()

    setScan(PulseAblationDummyProgram)
    startScan(globalOverrides=list(), wait=False)
    for i in range(0, CoolSweepsNum):
        setGlobal("CoolingFreq",FreqMove1,"THz")
        time.sleep(TimeSwitchFreq)
        setGlobal("CoolingFreq",FreqMove2,"THz")
        time.sleep(TimeSwitchFreq)
    time.sleep(TimeCool)
    stopScan()
    
    (ydataAvg, ydataStD) = GetCounts(CountsProgram)
    Count += 1
    setGlobal("LoadAttempts", Count, "")
    
    if not (BGydataAvg - BGNumStDevs*BGydataStD < ydataAvg < BGydataAvg + BGNumStDevs*BGydataStD):
        IonTrapped = True
        os.system("C:/Users/ions/Documents/Beep.bat")
        cmd = "start /wait cmd /k echo Ion trapped, with %f counts average. Total ablation pulses: %i"%tuple([ydataAvg, Count])
        os.system(cmd)
