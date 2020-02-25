#TestScript.py created 2020-02-18 14:59:36.434564

setGlobal("TestGlobalVar",0,"")
GlobalVar = getGlobal("TestGlobalVar")
while GlobalVar < 10:
    startScan(globalOverrides=list(), wait=True)
    GlobalVar += 1
    setGlobal("TestGlobalVar",GlobalVar,"")
    if scriptIsStopped():
        break