# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import os
from mpl_toolkits.mplot3d import Axes3D
import scipy 
from scipy.optimize import curve_fit
import pywt
import sys

def loadfidold(name,plot):
    """loads Topspin FID and other useful info"""
    
    f=open(name, mode='rb') #open(path + "fid", mode='rb')
    fid = np.frombuffer(f.read(), dtype = int) #float to avoid condvta nonsense
    l = int(len(fid))
    Re = fid[0:l:2]
    Im = 1j*fid[1:l:2]
    fid = Re + Im
    
    g=open("acqus", mode='r')
    lines=g.readlines()
    SW = float(lines[269].split()[1]) #269
    DW = 1/SW
    
    td = len(fid)
    time = np.linspace(0, DW*td, num=td)
    
    if plot == 'yes':
        plt.subplot(211)
        plt.plot(time,np.real(fid),'b')
        plt.subplot(212)
        plt.plot(time,np.imag(fid),'r')
        plt.xlabel('Time (s)')
    return fid, SW

def loadfid(name,plot):
    """loads Topspin FID and other useful info"""
    
    f=open(name, mode='rb') #open(path + "fid", mode='rb')
    fid = np.frombuffer(f.read(), dtype = float) #float to avoid condvta nonsense
    l = int(len(fid))
    Re = fid[0:l:2]
    Im = 1j*fid[1:l:2]
    fid = Re + Im
    
    g=open("acqus", mode='r')
    lines=g.readlines()
    #SW = float(lines[268].split()[1])
    SW = float(lines[267].split()[1])
    DW = 1/SW
    td = len(fid)
    time = np.linspace(0, DW*td, num=td)
    
    if plot == 'yes':
        plt.subplot(211)
        plt.plot(time,np.real(fid),'b')
        plt.subplot(212)
        plt.plot(time,np.imag(fid),'r')
        plt.xlabel('Time (s)')
    return fid, SW

def freqaxis(fid,SW):
    "Generate the referenced frequency axis (in kHz) as an array"
    
    zfi = autozero(fid)
    g=open("acqus", mode='r')
    lines=g.readlines()
    #SW = float(lines[268].split()[1]) #problem reading SW b/t pp's
    #BF1 = float(lines[19].split()[1])
    #SFO1 = float(lines[227].split()[1])
    cwd = os.getcwd()
    path = cwd + "\pdata\\1"
    
    os.chdir(path)
    h=open("procs", mode='r')
    lines=h.readlines()
    SF = float(lines[107].split()[1])
    OFFSET = float(lines[87].split()[1])
    
    off = ((OFFSET*SF)-SW/2)*1e-3
    freq = np.linspace(-SW/2e3+off, SW/2e3+off, num=zfi)
    os.chdir(cwd)
    
    return freq

def autozero(fid):
    """Automatically zero fill fid"""
    td = len(fid)
    zf = [2**n for n in range(28)] #auto zero-fill
    for i in range(24):
        if td < zf[i]:
            a = i
            break
    zfi = int(zf[a+2])
    return zfi

def gauss(fid,lb):
    """Gaussian line broadening for whole echo fid"""
    td = len(fid)
    if lb != 0: #line broadening bit
        sd = 1e3/(lb)
        n = np.linspace(-td/2,td/2,td)
        gauss = ((1/(2*np.pi*sd))*np.exp(-((n-1)**2)/(2*sd**2)))
        gbfid = np.multiply(fid,gauss)
    else:
        gbfid = fid
    return gbfid

def fft(fid):
    zfi = autozero(fid)
    spec = np.fft.fftshift(np.fft.fft(fid,n=zfi))
    return spec

def fmc(fid,SW):
    """Calculates a FT and magnitude calculation of the FID"""
    
    zfi = autozero(fid)
    spec = np.fft.fftshift(scipy.fft(fid,n=zfi))
    freq = freqaxis(fid,SW)
    
    plt.gca().invert_xaxis()
    plt.plot(freq,np.abs(spec),'m')
    plt.xlabel('Frequency (kHz)')
    return spec

def mesh(matrix):
    """3D mesh plot of a 2D matrix"""
    
    x = np.arange(matrix.shape[0])
    y = np.arange(matrix.shape[1])
    x, y = np.meshgrid(x, y)
    fig = plt.figure()
    ax = Axes3D(fig)
    surf=ax.plot_surface(x.T, y.T, matrix, cmap='jet')
    fig.colorbar(surf, shrink=0.5, aspect=10)
    plt.show()
    return

def phase(spec, phases):
    "Phase spectrum up to 2nd-order"
    #phs will come from a list when autophase is done
    #ph[0] = ph0, ph[1] = ph1, etc...
    ph0 = phases[0]
    ph1 = phases[1]
    ph2 = phases[2]
    off = phases[3]
    #m,n = spec.shape
    m = spec.size
    #print(m)
    n = 1 #1D spectrum for now, maybe need if statement to do matrix
    a = np.transpose(np.arange(-m/2, m/2, 1))/m
    b = (np.transpose(np.arange((-m/2-off),(m/2-off),1)**2)) / ((m**2)/2)
    phase = ph0 + a*ph1 + b*ph2
    spec= np.multiply( spec, (np.exp((phase*(3.14159j/180)))*np.ones((1,n))) )
    return spec

def autophase(spec,n,phase2):
    td = spec.size
    size = td
    if size > 512:
        size = 512
    i = np.linspace(0,td,size)     # ph1 variables (in pts)
    j = np.linspace(0,360,size)     # ph0 variables  (in degrees)
    l = np.linspace(600*90,-600*90,size)  # ph2 variables (in degrees)
    ph0_1 = np.zeros(n)
    BestOffset = np.zeros(n)
    #offsets = np.arange(td,-td+1,-4)
    offsets = np.linspace(-td/2,td/2,10)
    Iter1 = np.zeros((n,size))
    M_ph1 = np.zeros(n)
    M_ph0 = np.zeros(n)
    ph1_1 = np.zeros(n)
    Iter3 = np.zeros((n,size))
    area1 = np.zeros(n)
    ph2_1 = np.zeros(n)
    if phase2 == 'yes':
        Iter2 = np.zeros((n,len(offsets),size))
        M_ph2 = np.zeros((n,len(offsets)))
        
    for k in range(n):
        #Find first order phase 
        for r in range(len(i)):
            Iter1[k,r] = np.sum(np.real(phase(spec,[ph0_1[k],360*i[r],ph2_1[k],round(BestOffset[k])])))
        M_ph1[k] = np.max(np.abs(Iter1[k,:]))
        ph1_1[k] = i[np.argwhere(abs(Iter1[k,:]) == M_ph1[k])]
        
        #Find zero order phase
        for r in range(len(j)):
            Iter3[k,r] = np.sum(np.real(phase(spec,[j[r],360*ph1_1[k],ph2_1[k],round(BestOffset[k])])))
        M_ph0[k] = np.max(np.real(Iter3[k,:]))
        a = np.argwhere(np.real(Iter3[k,:]) == M_ph0[k])
        if len(a) > 1:
            a = a[1]
        ph0_1[k] = j[a]
        
        if phase2 == 'yes':
        #Find second order phase
            for mm in range(len(offsets)):
                for r in range(len(l)):
                    Iter2[k,mm,r] = np.sum(np.real(phase(spec,[ph0_1[k],360*ph1_1[k],l[r],(offsets[mm])])))
                M_ph2[k,mm] = np.max(abs(Iter2[k,mm,:]))
        
            BestOffsetIndex = int( np.min( np.argwhere(abs(M_ph2[k,:]) == np.max(abs(M_ph2[k,:]))) ))
            BestOffset[k] = offsets[BestOffsetIndex]
            ph2_1[k] = l[np.argwhere((abs(Iter2[k,BestOffsetIndex])) == abs(M_ph2[k,BestOffsetIndex]))]
    
        else:
            BestOffset[k] = 0
        
        area1[k] = np.sum(np.real(phase(spec,[ph0_1[k],360*ph1_1[k],ph2_1[k],round(BestOffset[k])])))
        
        a = np.argmax(area1) 
        ph0 = ph0_1[a]
        ph1 = ph1_1[a]
        ph2 = ph2_1[a]
    
        i = ph1 + np.linspace(-64/(k+1), 64/(k+1), round(size/(k+1))) #MJJ shrinks these sizes each run, but mismatches with spec
        j = ph0 + np.linspace(0, 360/(k+1), round(size/(k+1)))
        l = ph2 + np.linspace(400*90/(k+1), -400*90/(k+1), round(size/(k+1)))
        offsets = BestOffset[a] + np.linspace(128,-128, round(len(offsets)))
        #offsets = BestOffset[a] + np.linspace(round(td/(2*(k+1))),-round(td/(2*(k+1))), round(td/(k+1)))
        
        print('Iteration %d/%d' % (k+1,n))
        
    off = BestOffset[a]
    phases = [ph0,ph1*360,ph2,off]
    plt.plot(np.real(phase(spec,phases))[0,:] + 1*np.max(np.abs(spec)),'m',label='Phased')
    plt.plot(np.abs(spec),'k',label='Magnitude')
    plt.plot(np.abs(spec) - np.real(phase(spec,phases))[0,:] + 2*np.max(np.abs(spec)),'r--',label='Difference')
    plt.gca().invert_xaxis()
    plt.legend(loc='upper right')
    
    print(phases)
    return phases

def coadd(fid,lb,plot):
    """Automatically coadd all spin echos and FT and MC"""
    """Specifically works for WCPMG data acquired on NEO"""
    
    ##Numbers are all different for diff WCPMG pp :(
    g=open("acqus", mode='r')
    lines=g.readlines()
    #SW = float(lines[268].split()[1])
    SW = float(lines[267].split()[1])
    d3 = float(lines[42].split()[3]) #d3 dead time (s)
    d6 = float(lines[42].split()[6]) #d6 acq time (s)
    #decim = int(lines[47].split()[1]) #decimation number
    decim = int(lines[49].split()[1]) #decimation number
    #l22 = int(lines[118].split()[22]) #number of echoes
    l22 = int(lines[121].split()[22]) #number of echoes
    #tp = float(lines[168].split()[11]) #p11 pulse width in WCPMG (us)*
    tp = float(lines[170].split()[11]) #p11 pulse width in WCPMG (us)*
    DW = 1/SW #(s)
    
    fid = fid[(2*decim-1):] #remove decimation points
    fid = fid[:int((l22)*np.round((d6 + 2*d3 + 2e-6 + tp*1e-6)/DW))] #remove trailing pts
    
    #plt.plot(np.real(fid))
    
    cpmg = np.transpose( np.reshape(fid, (l22, int(len(fid)/l22) )) )
                      
    fidcoadd = np.sum(cpmg, axis=1) #note that it's more robust to do 2D FT and then coadd
    group = int(np.round((2*d3 + 2e-6 + tp*1e-6)/DW))
    fidcoadd = fidcoadd[round(group/2):len(fidcoadd)-round(group/2)] #kills filters too
       
    #zfi = autozero(fidcoadd)#auto zero-fill code
    fidcoadd = gauss(fidcoadd,lb)
    spec = fft(fidcoadd)
    freq = freqaxis(fidcoadd,SW)
    
    if plot=='yes':
        plt.gca().invert_xaxis()
        plt.plot(freq,np.abs(spec),'m')
        plt.xlabel('Frequency (kHz)')
    
    return cpmg, fidcoadd, spec

def coaddOLD(fid,SW,lb,plot):
    """Automatically coadd all spin echos and FT and MC"""
    """Works for custom qcpmg data pre-NEO"""
    
    DW = 1/SW #(s)
    g=open("acqus", mode='r')
    lines=g.readlines()
    d3 = float(lines[41].split()[3]) #d3 dead time (s)
    d6 = float(lines[41].split()[6]) #d6 acq time (s)
    decim = int(lines[47].split()[1]) #decimation number
    l22 = int(lines[121].split()[22]) #number of echoes
    tp = float(lines[171].split()[4]) #p4 pulse width in QCPMG (us)*
    
    group = int(np.round((2*d3 + tp*1e-6)/DW))
    grouph = int(np.round(group/2))
    
    fid = fid[(decim-1):] #remove decimation points
    #fid = fid[:int((l22)*np.round((d6 + 2*d3 + tp*1e-6)/DW))-2*group] #remove trailing pts
    #plt.plot(np.real(fid))
    cpmg = np.zeros((int(d6/DW),l22),dtype=complex)
    for n in range(l22):
        cpmg[:,n] = fid[ n*( int(round(d6/DW))+group ) : n*( int(round(d6/DW))+group ) + (int(round(d6/DW)))]
    #mesh(np.abs(cpmg))
    #print(cpmg.shape)
    #Eliminate trailing dead time points
    #fid((np*nechoes + 1):end) = [];
    
    #plt.plot(np.real(fid))
    
    #cpmg = np.transpose( np.reshape(fid, (l22, int(round(len(fid)/l22) ))) )
    
    #mesh(np.real(cpmg))
    zfi = autozero(cpmg[:,0])
    m,n=cpmg.shape
    spec = np.zeros((zfi,n))
    for i in range(l22):
        cpmg[:,i] = gauss(cpmg[:,i],lb)
        spec[:,i] = np.abs(np.fft.fftshift(scipy.fft(cpmg[:,i],n=zfi)))
    
    #mesh(np.real(spec))
    fidcoadd= gauss(np.sum(cpmg, axis=1),lb)
    coadd = np.sum(spec, axis=1) #note that it's more robust to do 2D FT and then coadd
    #group = int(np.round((2*d3 + 2e-6 + tp*1e-6)/DW))
    #fidcoadd = fidcoadd[round(group/2):len(fidcoadd)-round(group/2)] #kills filters too
       
    #zfi = autozero(fid)#auto zero-fill code
    #fidcoadd = gauss(fidcoadd,lb)
    
    #spec = np.fft.fftshift(scipy.fft(fidcoadd,n=zfi))
    freq=freqaxis(SW,zfi)
    
    if plot=='yes':
        plt.gca().invert_xaxis()
        plt.plot(freq,coadd,'m')
        plt.xlabel('Frequency (kHz)')
    
    return cpmg, coadd, spec, fidcoadd

def T2fit(fid,SW):
    """Fit the monoexponential T2 / T2eff of the WCPMG echo train"""
    
    fid = np.abs(fid)
    DW = 1/SW #(s)
    g=open("acqus", mode='r')
    lines=g.readlines()
    d3 = float(lines[42].split()[3]) #d3 dead time (s)
    d6 = float(lines[42].split()[6]) #d6 acq time (s)
    decim = int(lines[47].split()[1]) #decimation number
    l22 = int(lines[118].split()[22]) #number of echoes
    tp = float(lines[168].split()[11]) #p11 pulse width in WCPMG (us)*
    
    #want the index so you can figure out the time with the dwell
    indx1 = np.argmax(fid[:int(2*decim + (d6+ 2*d3 + 2e-6 + tp*1e-6)/DW -1)]) 
    #print(tau1, indx1)
    
    indx=[indx1]
    tops = []
    tau  = []
    group = int((d6/2+ 2*d3 + 2e-6 + tp*1e-6)/DW) #group delay of dead time and half echo
    for i in range(l22):
        run = np.argmax(fid[ indx[i] + group : indx[i] + group + int((d6)/DW)-1])
        indx.append( indx[i] + group + run )
        tops.append(fid[indx[i]])
        tau.append(indx[i]*DW) #index*DW gives the times of the echo tops
        
    tops = tops/np.amax(tops)
    tau = np.asarray(tau)
    plt.plot(tau,tops,'k')
    plt.xlabel('Time (ms)')
    def f(x,a,T2):
        return a*np.exp(-x/T2)
    
    popt, pcov = curve_fit(f, tau, tops, bounds= (0.0, [3., 1000.]) )
    print('a = %5.3f' % popt[0])
    print('T2 = %5.5f (s)' % popt[1])
    
    rmse = np.sqrt(np.mean(np.square(f(tau, popt[0], popt[1])-tops)))
    print('RMSE = %5.4f' % rmse)
    
    plt.plot(tau, f(tau, popt[0], popt[1]),'r',
             label='fit a*exp[-t/T2]: a=%5.3f, T2=%5.3f (s), RMSE = %5.3f' % (popt[0],popt[1],rmse))        
    plt.legend()
    return tau
    
def snr(spec,j):
    """SNR measure in the frequency domain. Specturm needs to be phased for accurate measure"""
    
    spec = np.real(spec)
    #plt.plot(spec) #plot the spectrum to determine the index #'s of noise basline
    if j!=0:    
        sn = np.max(spec) / np.std(spec[0:j])
    else:
        sn = np.max(spec) / np.std(spec[0:100])
    print('SNR = %.3f' %sn)
    return sn

def PCA(matrix,r):
    """Denoises m x n complex spectal matrix with PCA reconstruction using r number of components"""
    
    m,n = matrix.shape
    for j in range(n): #'center' the matrix to have mean 0 on the columns
        matrix[:,j] = matrix[:,j] - np.mean(matrix[:,j])
    
    U, s, Vh = scipy.linalg.svd(matrix) #s is a vector of singular values, not a matrix
    plt.figure(1)
    plt.plot(np.abs(s))
    plt.yscale('log')
    plt.ylabel('Singular Value Magnitude')
    plt.xlabel('Singular Value Entry')
    sigma = scipy.linalg.diagsvd(s, m, n) #rebuilds s as sigma matrix
    b = np.dot(sigma, Vh) ##replace with np.matmul or @ 
    z = np.dot(U[:,:r], b[:r,:]) #retain 'r' principal components
    
    #plot the real part of the original and the denoised
    matrix = np.real(matrix)
    fig = plt.figure(figsize=plt.figaspect(0.5))
    ax = fig.add_subplot(1, 2, 1, projection='3d')
    x = np.arange(matrix.shape[0])
    y = np.arange(matrix.shape[1])
    x, y = np.meshgrid(x, y)
    surf = ax.plot_surface(x.T, y.T, matrix, cmap='jet')
    fig.colorbar(surf, shrink=0.5, aspect=10)
    plt.title('Raw')
    
    zp = np.real(z)
    ax = fig.add_subplot(1, 2, 2, projection='3d')
    x = np.arange(zp.shape[0])
    y = np.arange(zp.shape[1])
    x, y = np.meshgrid(x, y)
    surf = ax.plot_surface(x.T, y.T, zp, cmap='jet')
    fig.colorbar(surf, shrink=0.5, aspect=10)
    plt.title('Denoised')
    
    return z

def deT2fit(matrix,tau):
    """Fit the T2 of denoised CPMG data"""
    #can either reccomend to run T2fit first or use T2fit funciton in this function to get tau
    #and either suppress the plot or use as subplot somehow
    matrix = np.abs(matrix)
    m,n = matrix.shape
    tops=[]
    for i in range(n):
        tops.append(np.max(matrix[:,i]))
        
    tops = tops/np.amax(tops)
    #plt.plot(tops)
    plt.plot(tau,tops,'k')
    plt.xlabel('Time (ms)')
    def f(x,a,T2):
        return a*np.exp(-x/T2)
    
    popt, pcov = curve_fit(f, tau, tops, bounds= (0.0, [3., 1000.]) )
    print('a = %5.3f' % popt[0])
    print('T2 = %5.5f (s)' % popt[1])
    
    rmse = np.sqrt(np.mean(np.square(f(tau, popt[0], popt[1])-tops)))
    print('RMSE = %5.4f' % rmse)
    
    plt.plot(tau, f(tau, popt[0], popt[1]),'r',
             label='fit a*exp[-t/T2]: a=%5.3f, T2=%5.3f (s), RMSE = %5.3f' % (popt[0],popt[1],rmse))        
    plt.legend()
    return

def cadzow(fid,phases,SW,lb):
    """Create Hankel matrix and use SVD to denoise fid"""
    
    l = round(len(fid)/2)
    print(l)
    a = fid[:l+1] ##Note that in hankel(c,r) r[0] is ignored*
    ##...so need to incude r[0] as the last point in c!!
    b = fid[l:]
    
    hank = scipy.linalg.hankel(a,b)
    m,n = hank.shape
    print('Hanekl Dimensions = ',m,n)
    #U, s, Vt = scipy.linalg.svd(hank) #s is a vector of singular values, not a matrix, Vt is already transposed
    U, s, Vt = np.linalg.svd(hank) #s is a vector of singular values, not a matrix, Vt is already transposed
    s = np.array(s)
    s1 = np.flipud(np.diff(np.flipud(s)))
    #plt.figure(1)
    #plt.plot(s,'*')
    #plt.plot(s1,'m.')
    #plt.yscale('log')
    #plt.ylabel('Singular Value Magnitude')
    #plt.xlabel('Singular Value Entry')
    
    r = np.argmax(s1[round(0.1*len(s1)):]) + round(0.1*len(s1))
    print('Retaining %d singular values' % r)
    
    s[(r):] = 0
    sigma = scipy.linalg.diagsvd(s, m, n) #rebuilds s as sigma matrix
    #plt.imshow(np.abs(sigma))
    hankrecon = np.matmul( np.matmul(U,sigma), Vt )
    
    #plt.imshow(np.abs(hank))
    #plt.imshow(np.abs(hankrecon))
    
    ad = [] #welcome to the inefficient anti-diagonal averaging algorithm
    for i in range(m-1):
        ad.append( np.mean( np.fliplr( hankrecon[:i+1,:i+1] ).diagonal()))
    ad = np.array(ad)

    ad2 = []
    for i in range(n):
        ad2.append( np.mean( np.fliplr( hankrecon[(m-1-i):,(n-1-i):] ).diagonal()))
    ad2 = np.flip(ad2)
    
    fidrecon = np.append( ad, ad2 ) #instead of rebuilding hank, just extract the fid
    
    fid = gauss(fid,lb)
    fidrecon = gauss(fidrecon,lb)
    
    plt.figure(2)
    plt.subplot(121)
    plt.plot(np.real(fid),'k')
    plt.plot(np.real(fidrecon),'r')
    plt.title('Cadzow Denoising', fontsize=18)
    
    #zfi = autozero(fid)
    spec = fft(fid)
    specrecon = fft(fidrecon)
    freq = freqaxis(fid,SW)
    
    if phases == 0:
        spec = np.abs(spec)
        specrecon = np.abs(specrecon)
    else:
        spec = phase(spec,phases)[0,:]
        specrecon = phase(specrecon,phases)[0,:]
    
    rawsnr = snr(spec,j=0)
    reconsnr = snr(specrecon,j=0)
    
    plt.subplot(122)
    plt.plot(freq,np.real(spec),'k',label='SNR = %.2f' %rawsnr)
    plt.plot(freq,np.real(specrecon) + 1*np.max(np.abs(spec)),'r',label='SNR = %.2f' %reconsnr)
    plt.legend()
    plt.gca().invert_xaxis()
    plt.xlabel('Frequency (kHz)', fontsize=14)
    
    return fidrecon

def dwt(fid,SW,phases,thresh,lb):
    """Denoising with discrete wavelet transform"""
    
    def autozero2(fid):
        """Automatically zero fill fid up to first possible Fourier number"""
        td = len(fid)
        zf = [2**n for n in range(28)] #auto zero-fill
        for i in range(24):
            if td < zf[i]:
                a = i
                break
        zfi = int(zf[a])
        print(zfi)
        return zfi
    q = autozero2(fid)
    fid= np.pad(fid,(0,q-len(fid)), 'constant', constant_values=(0, 0))
    print(len(fid))
    wavelet="sym10" #"coif5","sym5","db6","bior2.4","rbio3.7"
    thresh = thresh*np.max(fid)
    coeff = pywt.wavedec(fid, wavelet)#, mode="per" ) #careful on mode
    ##Calc the Sj's
    S = np.zeros(len(coeff),dtype='complex')
    for i in range(len(coeff)):
        S[i] = (np.max( np.abs(coeff[i]) ) / np.sum( np.abs(coeff[i]) ))
    T = 0.002
    k = np.argwhere(  S <= T ) 
    coeff[np.min(k):] = (pywt.threshold(i, value=thresh, mode="soft" ) for i in coeff[np.min(k):])
    print(S)
    #k = 8
    #coeff[k:] = (pywt.threshold(i, value=thresh, mode="soft" ) for i in coeff[k:])
    fidrecon = pywt.waverec(coeff, wavelet)#, mode="per" ) #careful on mode
    #rec = lowpassfilter(signal, 0.4)
    
    #coeff = pywt.swt(fid, wavelet)
    
    #fid = gauss(fid,lb)
    #fidrecon = gauss(fidrecon,lb)
    
    plt.figure(1)
    for i in range(len(coeff)):
        plt.plot(np.real(coeff[i]) - i*np.max(np.real(np.array(coeff[i]))), label = 'D_%1d'%i)
    plt.legend()
    
    plt.figure(2)
    plt.subplot(121)
    plt.plot(np.real(fid), color="k", alpha=0.7, label='Raw')
    plt.plot(np.real(fidrecon), 'r', label='Wavelet', linewidth=2)
    plt.legend()
    plt.title('Wavelet Reconstruction', fontsize=18)
    plt.ylabel('Intensity (a.u.)', fontsize=14)
    
    zfi = autozero(fid)
    spec = fft(fid)
    specrecon = fft(fidrecon)
    freq = freqaxis(SW,zfi)
    
    if phases == 0:
        spec = np.abs(spec)
        specrecon = np.abs(specrecon)
    else:
        spec = phase(spec,phases)[0,:]
        specrecon = phase(specrecon,phases)[0,:]
    
    rawsnr = snr(spec,j=0)
    reconsnr = snr(specrecon,j=0)
    
    plt.subplot(122)
    plt.plot(freq,np.real(spec),'k',label='SNR = %.2f' %rawsnr)
    plt.plot(freq,np.real(specrecon) + 1*np.max(np.abs(spec)),'r',label='SNR = %.2f' %reconsnr)
    plt.gca().invert_xaxis()
    plt.legend()
    plt.xlabel('Frequency (kHz)', fontsize=14)
    
    return fidrecon, coeff

def swt(fid,SW,phases,thresh,lb):
    """Denoising with stationary wavelet transform"""
    
    k = 6
    
    def autozero2(fid):
        """Automatically zero fill fid"""
        td = len(fid)
        zf = [2**n for n in range(28)] #auto zero-fill
        for i in range(24):
            if td < zf[i]:
                a = i
                break
        zfi = int(zf[a])
        return zfi
    q = autozero2(fid)
    fid= np.pad(fid,(0,q-len(fid)), 'constant', constant_values=(0, 0))
    print(len(fid))
    wavelet="sym15" #"coif5","sym5","db6","bior2.4","rbio3.7"
    thresh = thresh*np.max(fid)
    
    coeff = pywt.swt(fid, wavelet)

    plt.figure(1)
    plt.subplot(131)
    for i in range(len(coeff)):
        plt.plot(np.real(coeff[i][1]) - i*np.max(np.real(np.array(coeff[:][1]))), label = 'D_%1d'%i)
    plt.title('Detail Component')
    plt.legend(loc='upper right')
    
    plt.subplot(132)
    for i in range(len(coeff)):
        plt.plot(np.real(coeff[i][0]) - i*np.max(np.real(np.array(coeff[:][0]))), label = 'A_%1d'%i)
    plt.title('Approximation Component')
    plt.legend(loc='upper right')
    
    kcoeff = np.array(coeff)[k:,:,:]
    m,n,s = kcoeff.shape
    DCth = np.zeros((s,m),dtype='complex')
    for i in range(len(coeff) - k):
        DCth[:,i] = pywt.threshold(kcoeff[i,1,:], value=thresh, mode="soft" )
    
    plt.subplot(133)
    for i in range(m):
        plt.plot(np.real(DCth[:,i]) - i*np.max(np.real(DCth[:,:])), label = 'D_%1d'%(k+i))
    plt.title('Detail Component Thresholding')
    plt.legend(loc='upper right')
    
    ##Big note that the ordering of the levels is backwards from Srivastava
    
    coeffrecon = coeff[:k][:]
    for i in range(len(coeff) - k):
        coeffrecon.append( ( coeff[k+i][0] , DCth[:,i] ) )
    
    fidrecon = pywt.iswt(coeffrecon, wavelet)#, mode="per" ) #careful on mode
    
    fid = gauss(fid,lb)
    fidrecon = gauss(fidrecon,lb)
    
    plt.figure(2)
    plt.subplot(121)
    plt.plot(np.real(fid), color="k", alpha=0.7, label='Raw')
    plt.plot(np.real(fidrecon), 'r', label='Wavelet', linewidth=2)
    plt.legend()
    plt.title('Wavelet Reconstruction', fontsize=18)
    plt.ylabel('Intensity (a.u.)', fontsize=14)
    
    zfi = autozero(fid)
    spec = fft(fid)
    specrecon =fft(fidrecon)
    freq = freqaxis(SW,zfi)
    
    if phases == 0:
        spec = np.abs(spec)
        specrecon = np.abs(specrecon)
    else:
        spec = phase(spec,phases)[0,:]
        specrecon = phase(specrecon,phases)[0,:]
    
    rawsnr = snr(spec,j=0)
    reconsnr = snr(specrecon,j=0)
    
    plt.subplot(122)
    plt.plot(freq,np.real(spec),'k',label='SNR = %.2f' %rawsnr)
    plt.plot(freq,np.real(specrecon) + 1*np.max(np.abs(spec)),'r',label='SNR = %.2f' %reconsnr)
    plt.gca().invert_xaxis()
    plt.legend()
    plt.xlabel('Frequency (kHz)', fontsize=14)
    
    return fidrecon, coeff

def dwtf(fid,SW,phases,thresh,lb):
    """Denoising with discrete wavelet transform in the frequency domain"""
    
    zfi = autozero(fid)
    spec = np.fft.fftshift(scipy.fft(fid,n=zfi))
    freq = freqaxis(SW,zfi)
    
    wavelet="sym10" #"coif5","sym5","db6","bior2.4","rbio3.7"
    thresh = thresh*np.max(fid)
    coeff = pywt.wavedec(spec, wavelet)#, mode="per" ) #careful on mode
    ##Calc the Sj's
    S = np.zeros(len(coeff),dtype='complex')
    for i in range(len(coeff)):
        S[i] = (np.max( np.abs(coeff[i]) ) / np.sum( np.abs(coeff[i]) ))
    T = 0.02
    k = np.argwhere(  S <= T ) 
    coeff[np.min(k):] = (pywt.threshold(i, value=thresh, mode="soft" ) for i in coeff[np.min(k):])
    print(S)
    #k = 8
    #coeff[k:] = (pywt.threshold(i, value=thresh, mode="soft" ) for i in coeff[k:])
    specrecon = pywt.waverec(coeff, wavelet)#, mode="per" ) #careful on mode
    #rec = lowpassfilter(signal, 0.4)
    
    #coeff = pywt.swt(fid, wavelet)
    
    #fid = gauss(fid,lb)
    #fidrecon = gauss(fidrecon,lb)
    
    plt.figure(1)
    for i in range(len(coeff)):
        plt.plot(np.real(coeff[i]) - i*np.max(np.real(np.array(coeff[i]))), label = 'D_%1d'%i)
    plt.legend()
    
    plt.figure(2)
    # plt.subplot(121)
    # plt.plot(np.real(spec), color="k", alpha=0.7, label='Raw')
    # plt.plot(np.real(specrecon), 'r', label='Wavelet', linewidth=2)
    # plt.legend()
    # plt.title('Wavelet Reconstruction', fontsize=18)
    # plt.ylabel('Intensity (a.u.)', fontsize=14)
    
    if phases == 0:
        spec = np.abs(spec)
        specrecon = np.abs(specrecon)
    else:
        spec = phase(spec,phases)[0,:]
        specrecon = phase(specrecon,phases)[0,:]
    
    rawsnr = snr(spec,j=0)
    reconsnr = snr(specrecon,j=0)
    
    #plt.subplot(122)
    plt.plot(freq,np.real(spec),'k',label='SNR = %.2f' %rawsnr)
    plt.plot(freq,np.real(specrecon) + 1*np.max(np.abs(spec)),'r',label='SNR = %.2f' %reconsnr)
    plt.gca().invert_xaxis()
    plt.legend()
    plt.xlabel('Frequency (kHz)', fontsize=14)
    
    return specrecon, coeff