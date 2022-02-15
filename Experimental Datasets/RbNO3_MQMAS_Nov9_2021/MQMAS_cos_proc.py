# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0,'/Users/SRG/Documents/Adam/Python/SSNMR/functions')
import numpy as np
import functions as proc
import simpson as simproc
import wavelet_denoise as wave
import matplotlib.pyplot as plt
import matplotlib as mpl
import time
start_time = time.time()

cwd =  os.getcwd()
os.chdir(cwd + '\\' + '15')
fid = proc.loadfid2('ser',plot='no')

#Params:
nzf1 = 512
nzf2 = 4096
base = 1 #base contour %'age
sh = -7/9

##SH = -7/9 for this coherence selection
spec = proc.mqproc(fid, SH = sh, zf1=nzf1, zf2=nzf2, lb1=0, lb2=15) 

fid2 = np.fft.ifft(spec,axis = 0)
fid2 = np.roll(fid2,1,axis=0)   #shift 1 point in t1 to correct phase since t1 = 0 is not acq'd in cos/cos
spec = np.fft.fft(fid2,axis=0)

spec = np.flip(spec,axis=0)

#PCA Denoise
# spec = proc.PCA(spec,3)
# plt.close()

#Phase
#ph = [0,0, 0, 0]
ph = [361-32-6, 798382-340-80, 0, 0]
#ph = [362-25 - 10, 798157 - 150, 0, 0]
#ph = proc.autophase(spec[313,:],50,phase2='no')
# ph = proc.autophase(spec[:,1766],10,phase2='no')
spec = proc.phase(spec,ph,ax=1)
# proc.mphase(spec,fine=1000)
#sys.exit()

#2D SWT
#spec, coeffin, coeffs = wave.wavelet_denoise2(2, np.real(spec), 0, wave = 'bior2.2', threshold = 'mod', alpha = 0)

#SNRs
a = np.unravel_index(spec.argmax(), spec.shape)
snrF2 = proc.snr(spec[a[0],:],1000)
snrF1 = proc.snr(spec[:,a[1]],100)

#snrp1 = simproc.snrp(spec[290,:],2293,2464)
#snrp2 = simproc.snrp(spec[422,:],2130,2408)
#snrp3 = simproc.snrp(spec[433,:],1836,2118)

#print('SNRp 1 = %.1f' %snrp1)
#print('SNRp 2 = %.1f' %snrp2)
#print('SNRp 3 = %.1f' %snrp3)
print('SNR over F2 = %5.1f' %snrF2)
print('SNR over F1 = %5.1f' %snrF1)

#Plotting Stuff
mpl.rcParams['font.family'] = "arial"
mpl.rcParams['font.size'] = 14
mpl.rcParams['pdf.fonttype'] = 42

freq2 = proc.freqaxis(spec[0,:],unit='ppm')
fiso = proc.fiso(spec[:,0],SH = -sh,unit='ppm')

h = np.max(np.real(spec))
lvls = np.linspace((base*1e-2)*h,h,30)

# Set up the axes with gridspec 
fig = plt.figure(figsize=(12, 8)) # figure size w x h
grid = plt.GridSpec(4, 5, hspace=0.3, wspace=0.6) #4x5 grid of subplots #spacings for h and w
main_ax = fig.add_subplot(grid[1:, 1:4]) 

yplot = fig.add_subplot(grid[1:, 0], yticklabels=[])
xplot = fig.add_subplot(grid[0, 1:4], yticklabels=[], sharex=main_ax)

main_ax.contour(freq2,fiso,(np.real(spec)),lvls,cmap='jet')
main_ax.set_xlabel('F$_{2}$ (ppm)')#, fontfamily = 'Arial')
#main_ax.set_ylabel('F1_iso Frequency (ppm)')#, fontfamily = 'Arial')
main_ax.set_ylabel("F$_{iso}$ (ppm)",labelpad=-429)
main_ax.tick_params(right = True,left = False,labelleft = False, 
                    labelright=True, which = 'both')
main_ax.invert_yaxis()
main_ax.invert_xaxis()
main_ax.set_xlim(-24, -40) ##CHK BACK
main_ax.set_ylim(-22, -39)  ##CHK BACK
main_ax.minorticks_on()

#xplot.plot(freq2,(np.sum(np.real(spec),0)),'k') #sum
xplot.plot(freq2,(np.max(np.real(spec),0)),'k') #skyline

yplot.plot(np.real(np.sum(spec,1)),fiso,'k')
yplot.invert_xaxis()
yplot.invert_yaxis()
yplot.set_ylim(-22, -39)  ##CHK BACK

#Plot the sub-spectra
s1 = fig.add_subplot(grid[1, 4], yticklabels=[])
s2 = fig.add_subplot(grid[2, 4], yticklabels=[],sharex=s1)
s3 = fig.add_subplot(grid[3, 4], yticklabels=[],sharex=s1)
s1.invert_xaxis()
#s1.minorticks_on()
s1.set_xlim(-24,-40) ##CHK BACK
s3.set_xlabel('F$_{2}$ (ppm)')


# s1.plot(freq2,(np.real(spec[196,:])),'c')
# s2.plot(freq2,(np.real(spec[338,:])),'b')
# s3.plot(freq2,(np.real(spec[356,:])),'m')

s3.plot(freq2,(np.real(spec[simproc.nearest(fiso,-26.6504),:])),'c')
s2.plot(freq2,(np.real(spec[simproc.nearest(fiso,-27.43),:])),'b')
s1.plot(freq2,(np.real(spec[simproc.nearest(fiso,-33.82),:])),'m')

os.chdir(cwd)
print('Finished!')
print("-- %5.5f s Run Time --" % (time.time() - start_time))