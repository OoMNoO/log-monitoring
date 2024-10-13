import os
import subprocess
import socket
from datetime import datetime
import time

LogPATH= './NetworkMon.log'
TestSource= '8.8.8.8'
interval= '0.3'
count='10'

def main():
    while(True):
        CommandOutput, err=subprocess.Popen(["ping", TestSource, "-c", count, "-i", interval], stdout=subprocess.PIPE).communicate()

        if 'ttl=' in str(CommandOutput):
            for line in str(CommandOutput).split('\\n'):
                if line.find('received,') != -1:
                    PacketLoss= int(line[line.find('received,') + 10 : line.find('% packet loss')])

                elif line.find('mdev = ') != -1:
                    NetworkData= line[line.find('mdev = ') + 7 : line.find(' ms')].split('/')

                    MinPing=int(float(NetworkData[0]))
                    AvgPing=int(float(NetworkData[1]))
                    MaxPing=int(float(NetworkData[2]))
                    MdevPing=int(float(NetworkData[3]))

                    log=str(PacketLoss) + '_' + str(MinPing) + '_' + str(AvgPing) + '_' + str(MaxPing) + '_' + str(MdevPing)

        else:
            log= "TimeOut"

        subprocess.Popen('echo ' + str(datetime.now()) + ' - ' + TestSource + ' Connection status : ' + log  + ' >> ' + LogPATH, shell= True, env= os.environ)

if __name__== '__main__':
    main()


