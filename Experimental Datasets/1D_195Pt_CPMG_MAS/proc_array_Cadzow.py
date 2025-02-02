import sys
import os
sys.path.insert(0,'/Users/SRG/Documents/Adam/Python/SSNMR/functions')
import numpy as np
import functions as proc
import simpson as simproc
import time
import matplotlib.pyplot as plt
from tabulate import tabulate
start_time = time.time()

##Script will loop over array of Pt spectra
##Also used highest signal avg as SSIM 

##Get High SNR ref spectrum for SSIM:
gb = 5 #global gaussian broaden
p = 15 # global cadzow % cut off
path = 'C:\\Users\\SRG\\Documents\\Adam\\Spectromter_Data\\Pt(NH3)4Cl2_Sept28_2021\\' 
os.chdir( path ) #1k scan EXP
fidcoadd = np.load('fid2k.npy')  ##Load the pre-processed 2k scan FID
#fid, SW = proc.loadfid('fid',plot='no')  
#cpmg, fidcoadd, dumspec = proc.coadd(fid,lb = 0, plot='no')
#freq = proc.freqaxis(fidcoadd,SW)
#fidcoadd = fidcoadd[1:]  #Weird glitch, need to throw out first point to balance
fidcoadd = proc.gauss(fidcoadd,gb)
ph = [326, 680344, -9343, 455]
spec = proc.phase(proc.fft(fidcoadd),ph)
spec = np.real(spec)/np.max(np.real(spec))

fidrecon = proc.cadzow(fidcoadd,p)
specout = proc.phase(proc.fft(proc.gauss(fidrecon,gb)),ph)
specout = np.real(specout)/np.max(np.real(specout))
##Move on to main loop
m = 6
k = 2976#5953 #peak-peak SNR indices
l = 5298#10595

SSIMin =  np.zeros(m)
SSIMout =  np.zeros(m)
specrecon = np.zeros((len(spec),m),dtype='complex64')
specin = np.zeros((len(spec),m),dtype='complex64')
snrpin = np.zeros(m)
snrpout =  np.zeros(m)

#Entried for 2K scan:
SSIMin[0] = simproc.ssim(spec,spec)
snrpin[0] = simproc.snrp(spec,k,l)
specin[:,0] = spec
SSIMout[0] = simproc.ssim(spec,specout)
snrpout[0] = simproc.snrp(specout,k,l)
specrecon[:,0] = specout

for i in range(m-1):
    kk = 50 + i
    print(kk)
    os.chdir( path + str(kk) )
    fid, SW = proc.loadfid('fid',plot='no')  

    cpmg, fidcoadd, dumspec = proc.coaddg(fid) #save lb for cadzow
    
    specintemp = proc.phase(proc.fft(proc.gauss(fidcoadd,gb)),ph)
    specin[:,i+1] = np.real(specintemp)/np.max(np.real(specintemp))
    SSIMin[i+1] = simproc.ssim(spec,specin[:,i+1]) #SSIM of raw spec
    snrpin[i+1] = simproc.snrp(specin[:,i+1] ,k,l)

    #Denoise
    fidrecon = proc.cadzow(fidcoadd,p)
    
    specrecont = proc.phase(proc.fft(proc.gauss(fidrecon,gb)),ph)
    specrecon[:,i+1] = np.real(specrecont)/np.max(np.real(specrecont))
    SSIMout[i+1] = simproc.ssim(spec,specrecon[:,i+1])
    snrpout[i+1] = simproc.snrp(specrecon[:,i+1],k,l)

##Plotting
c = 0.000061038881768 #SSIMin of 2048 against itself has this difference from 1.0000
SSIMin = SSIMin - c
SSIMout = SSIMout - c

freq = proc.freqaxis(fidcoadd,SW)

plt.figure(1)
for i in range(len(snrpin)):
    plt.plot(freq,np.real(specin[:,i]) - i*np.max(np.real(specin[:,i])), label = 'SNRpp_in = %.1f , SSIM_in = %.4f' % (snrpin[i],SSIMin[i]))
plt.legend(loc='upper right')
plt.title('Noisey Spectra')
plt.xlabel('Frequency (kHz)')
plt.gca().invert_xaxis()

plt.figure(2)
for i in range(len(snrpin)):
    plt.plot(freq,np.real(specrecon[:,i]) - i*np.max(np.real(specrecon[:,i])), label = 'SNRpp_out = %.1f , SSIM_out = %.4f' % (snrpout[i],SSIMout[i]))
plt.legend(loc='upper right')
plt.title('Denoised Spectra')
plt.xlabel('Frequency (kHz)')
plt.gca().invert_xaxis()

##Table SNR peak-peak
ns = [2048, 1024, 512, 256, 128, 64]
data=[]
for i in range(len(snrpin)):
    data.append( ["%d"%ns[i],  "%.1f"%snrpin[i], "%.4f"%SSIMin[i], "%.1f"%snrpout[i], "%.4f"%SSIMout[i]] )
# create header
head = ['ns', 'SNRpp_in', 'SSIM_in', 'SNRpp_out', 'SSIM_out']
# display table
print(tabulate(data, headers=head, tablefmt="pretty", floatfmt="5.4f"))
#generate ns counter at end

print('Finished!')
print("-- %5.5f s Run Time --" % (time.time() - start_time))