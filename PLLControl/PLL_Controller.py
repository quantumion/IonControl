#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This only works on a Windows machine with plink installed (i.e Putty)
# Run this from a computer on the lab network, not on the raspberry pis themselves
import subprocess
import cmd
import time

class PllController:
    '''
    Opens a basic connection to the raspberry pi's and allows control of attenuation.
    Can be easlily updated to allow control of other things later.
    '''
    # Initial command to connect to pi through plink
    init_cmd = 'plink -ssh %s@%s -pw %s -batch'
    # Command to run Brendan's attenuation adjustment program once connected
    change_attn_command = ('python /home/pi/pll-evalboard-synthesizer'
                           '/src/Control-Programs/att1.py %s \n')
    change_freq_command =('python /home/pi/pll-evalboard-synthesizer'
                           '/src/Control-Programs/rf1.py %s \n')
    sweep_freq_command = ('python /home/pi/pll-evalboard-synthesizer'
                           '/src/Control-Programs/rf1_sweep.py %s \n')
    # Dictionaries conataining info on the pis
    # Frequencies are in MHz
    pi_database = {
        'pi1':{
            'ip': '192.168.168.101',
            'usr': 'pi',
            'pwd': 'raspberry',
            'val': '-1'
         }
        'pi2':{
            'ip': '192.168.168.102',
            'usr': 'pi',
            'pwd': 'raspberry',
            'val': '-1'
         }
        'pi3':{
            'ip': '192.168.168.103',
            'usr': 'pi',
            'pwd': 'raspberry',
            'val': '-1'
         }
        'pi4':{
            'ip': '192.168.168.104',
            'usr': 'pi',
            'pwd': 'raspberry',
            'val': '-1'
         }
        'pi5':{
            'ip': '192.168.168.105',
            'usr': 'pi',
            'pwd': 'raspberry',
            'val': '-1'
        }
        'pi6':{
            'ip': '192.168.168.106',
            'usr': 'pi',
            'pwd': 'raspberry',
            'val': '-1'
         }
    }   

    def __init__(self, name):
        # Initiate everything and setup a connection to the named pi
        self.name = name
        self.connect_cmd = self.init_cmd % (self.pi_database[self.name]['usr'],
                                        self.pi_database[self.name]['ip'],
                                        self.pi_database[self.name]['pwd'])
        # print(self.connect_cmd)
        # Connect to the named pi through ssh
        # get rid of stdout and stderr to see output from pi
        self.sp = subprocess.Popen(self.connect_cmd,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                text=True, bufsize=0)
        time.sleep(1.5)
        print('\nConnection established')

    @attenuation.setter
    def change_attn(self, gpio, level):
        # Changes the attentuation using Brendan's script on the pi
        function = 'attn'
        command = self.change_attn_command % (gpio + ' ' + level)
        self.sp.stdin.write(command)
        time.sleep(0.75)
        self.pi_database[self.name]['val'] = level
        print('Attentuation changed to %s' % level)
        return level
    
    @frequency.setter
    def change_freq(self, gpio, freq):
        'Changes the frequency of the aom corresponding to the laser.'
        function = 'freq'
        command = self.change_freq_command % (gpio + ' ' + freq)
        self.sp.stdin.write(command)
        time.sleep(0.75)
        self.pi_database[self.name]['val'] = freq
        print('AOM frequency changed to %s' % freq, 'MHz')
        return freq

    def terminate(self):
        # Exits the session and kills the subprocess just in case
        self.sp.stdin.write('exit \n')
        time.sleep(0.1)
        self.sp.stdin.close()
        self.sp.kill()
        return True