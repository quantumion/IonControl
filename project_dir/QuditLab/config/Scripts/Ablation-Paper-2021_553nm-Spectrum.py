#Ablation-Paper-2021_553nm-Spectrum.py created 2020-11-16 13:32:18.845837

import numpy as np
import os
import sys
import glob
import time

sys.path.append(r'C:\Users\ions\Documents\IonControl\project_dir\QuditLab\config\Scripts')
from TrapFunctions import *

NeutralFluorescenceProgram = "Ablation_For-Script_NeutralFluorescence_Nat"
PulseAblationDummyProgram = "PulseAblation_For-Script_Dummy_Ba138"
FreqSetWaitTime = 3

def NeutralFluoresencePulse(NeutProgram, setScan, startScan, stopScan, getAllData):
    setScan(NeutProgram)
    startScan(globalOverrides=list(), wait=True)
    time.sleep(0.05)
    data = getAllData()['PMT Count'] #Returns all data associated with scan.
    ydata = data[1]
    ydataAvg = np.mean(np.array(ydata))
    ydataStD = np.std(np.array(ydata))
    ydataVar = ydataStD/np.sqrt(len(ydata))
    stopScan()   
    return (ydata, ydataAvg, ydataStD, ydataVar)

Filepath = r"Z:\Lab Data\Sessions\2020\2020_11\2020_11_17"
filename = "Neut-Fluor_Freq_18uW_69uJ_5HzRep_155usWin_10Samp.txt"

if not os.path.exists(os.path.abspath(Filepath)):
    os.mkdir(os.path.abspath(Filepath))

(Freq493, Freq650, Freq553) = SetGlobalLaserFreqs("Ba138", getGlobal, setGlobal)

FreqCalibration = Freq553 + 100e-6
Freq553Start = Freq553
Freq553End = Freq553 + 600e-6
Freq553Resolution = 10e-6
Freqs553 = np.arange(Freq553Start, Freq553End, Freq553Resolution)
ExperimentCount = 0


#os.system('ssh pi@192.168.168.122 cd Documents; python press_stop_button.py')
#time.sleep(4)
#os.system('ssh pi@192.168.168.122 cd Documents; python press_start_button.py')


#setScan(PulseAblationDummyProgram)
#startScan(globalOverrides=list(), wait=False)
#time.sleep(2)
#stopScan()

#save_file = glob.glob(os.path.abspath(Filepath + "\\" + filename))  
for LaserFreq in Freqs553:
    if scriptIsStopped():
        break
    if ExperimentCount == 0:
        ExperimentCount += 1
        if not "%s"%getGlobal("IonizationFreq") == "%s THz"%FreqCalibration:
            setGlobal("IonizationFreq", FreqCalibration, "THz")
            time.sleep(FreqSetWaitTime)
        (dataRaw, dataAvg, dataStD, dataVar) = NeutralFluoresencePulse(NeutralFluorescenceProgram, setScan, startScan, stopScan, getAllData)
        print("Step number: %i, Laser frequency setpoint: %f, Average Data: %f, Var: %f"%(ExperimentCount, FreqCalibration, dataAvg, dataVar))
        save_file = glob.glob(os.path.abspath(Filepath + "\\" + filename))
        if not save_file:
            savetextfile = open(os.path.abspath(Filepath + "\\" + filename),'w+')
        else:
            savetextfile = open(os.path.abspath(Filepath + "\\" + filename),'a+')
        savetextfile.write(str(ExperimentCount) + "\t" + str(FreqCalibration) + "\t" + str(dataAvg) + "\t" + str(dataStD) + "\t" + str(dataVar) + "\t" + str(dataRaw) + "\n")
        savetextfile.close()
    
    ExperimentCount += 1
    if not "%s"%getGlobal("IonizationFreq") == "%s THz"%LaserFreq:
        setGlobal("IonizationFreq", LaserFreq, "THz")
        time.sleep(FreqSetWaitTime)
    (dataRaw, dataAvg, dataStD, dataVar) = NeutralFluoresencePulse(NeutralFluorescenceProgram, setScan, startScan, stopScan, getAllData)
    print("Step number: %i, Laser frequency setpoint: %f, Average Data: %f, Var: %f"%(ExperimentCount, LaserFreq, dataAvg, dataVar))
    save_file = glob.glob(os.path.abspath(Filepath + "\\" + filename))
    if not save_file:
        savetextfile = open(os.path.abspath(Filepath + "\\" + filename),'w+')
    else:
        savetextfile = open(os.path.abspath(Filepath + "\\" + filename),'a+')
    savetextfile.write(str(ExperimentCount) + "\t" + str(LaserFreq) + "\t" + str(dataAvg) + "\t" + str(dataStD) + "\t" + str(dataVar) + "\t" + str(dataRaw) + "\n")
    savetextfile.close()

    ExperimentCount += 1
    if not "%s"%getGlobal("IonizationFreq") == "%s THz"%FreqCalibration:
        setGlobal("IonizationFreq", FreqCalibration, "THz")
        time.sleep(FreqSetWaitTime)
    (dataRaw, dataAvg, dataStD, dataVar) = NeutralFluoresencePulse(NeutralFluorescenceProgram, setScan, startScan, stopScan, getAllData)
    print("Step number: %i, Laser frequency setpoint: %f, Average Data: %f, Var: %f"%(ExperimentCount, FreqCalibration, dataAvg, dataVar))
    save_file = glob.glob(os.path.abspath(Filepath + "\\" + filename))
    if not save_file:
        savetextfile = open(os.path.abspath(Filepath + "\\" + filename),'w+')
    else:
        savetextfile = open(os.path.abspath(Filepath + "\\" + filename),'a+')
    savetextfile.write(str(ExperimentCount) + "\t" + str(FreqCalibration) + "\t" + str(dataAvg) + "\t" + str(dataStD) + "\t" + str(dataVar) + "\t" + str(dataRaw) + "\n")
    savetextfile.close()
