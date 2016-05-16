"""
Note on adding fit functions - Gerwin Koolstra May 2016

The form of fit functions that are added, from now on, should be

    fitfunc(x, *p)

where x is the x-data and p is a list containing all the parameters. This function should be documented, especially
the order in which the parameters appear in p. The function should return the value of the
function at point x, and nothing else. fitfunc may then be used as argument in fitbetter, to create the actual
fitting procedure.
"""
import numpy as np
import math as math
import matplotlib.pyplot as plt2
import scipy, sys, cmath, common
import scipy.fftpack
from scipy import optimize

def argselectdomain(xdata,domain):
    ind=np.searchsorted(xdata,domain)
    return (ind[0],ind[1])

def selectdomain(xdata,ydata,domain):
    ind=np.searchsorted(xdata,domain)
    return xdata[ind[0]:ind[1]],ydata[ind[0]:ind[1]]

def zipsort(xdata,ydata):
    inds=np.argsort(xdata)
    return np.take(xdata,inds),np.take(ydata,inds,axis=0)

def get_rsquare(ydata, ydatafit):
    """
    Get the rsquare goodness of fit measure. This is a value between 0 and 1, indicating how well the fit
    approximates the data. A value of 0 indicating extremely bad, 1 the best fit. For further reading:
    https://en.wikipedia.org/wiki/Coefficient_of_determination
    :param ydata: Data
    :param ydatafit: Fit evaluated at the data points
    :return:R squared value
    """
    ybar = np.mean(ydata)
    total_sum_of_squares = np.sum((ydata-ybar)**2)
    residual_sum_of_squares = np.sum((ydata-ydatafit)**2)
    return 1 - residual_sum_of_squares/total_sum_of_squares

def fitgeneral(xdata, ydata, fitfunc, fitparams, domain=None, showfit=False, showstartfit=False,
               showdata=True, label="", mark_data='bo', mark_fit='r-', show_diagnostics=False):
    """
    Uses optimize.leastsq to fit xdata ,ydata using fitfunc and adjusting fit params
    :param xdata: x-axis
    :param ydata: y-axis
    :param fitfunc: One of the fitfunctions below
    :param fitparams: Parameters for the fitfunction
    :param domain: Domain for the xdata
    :param showfit: Show the fit
    :param showstartfit: Show the curve with initial guesses
    :param showdata: Plot the data.
    :param label: Label for the data
    :param mark_data: Marker format for the data
    :param mark_fit: Marker format for the fit
    :param show_diagnostics: Print best fit parameters etc.
    :return:
    """
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata

    errfunc = lambda p, x, y: (fitfunc(p,x) - y) #there shouldn't be **2 # Distance to the target function
    startparams=fitparams # Initial guess for the parameters
    bestfitparams, success = optimize.leastsq(errfunc, startparams[:], args=(fitdatax,fitdatay))
    if showfit:
        if showdata:
            plt.plot(fitdatax,fitdatay,mark_data,label=label+" data")
        if showstartfit:
            plt.plot(fitdatax,fitfunc(startparams, fitdatax),label=label+" startfit")
        plt.plot(fitdatax,fitfunc(bestfitparams, fitdatax),mark_fit,label=label+" fit")
        if label!='': plt.legend()
    err=math.fsum(errfunc(bestfitparams, fitdatax, fitdatay))

    if show_diagnostics:
        return bestfitparams, err, success
    else:
        return bestfitparams

def fitbetter(xdata, ydata, fitfunc, fitparams, domain=None, showfit=False, showstartfit=False,
              showdata=True, label="", mark_data='bo', mark_fit='r-', show_diagnostics=False):
    """
    Uses curve_fit from scipy.optimize to fit a non-linear least squares function to ydata, xdata
    Input mostly the same as fitgeneral
    """
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata

    startparams = fitparams
    bestfitparams, covmatrix = optimize.curve_fit(fitfunc, fitdatax, fitdatay, startparams)

    try:
        fitparam_errors = np.sqrt(np.diag(covmatrix))
    except:
        print covmatrix
        print "Error encountered in calculating errors on fit parameters. This may result from a very flat parameter space"

    if showfit:
        if showdata:
            plt2.plot(fitdatax,fitdatay,mark_data,label=label+" data")
        if showstartfit:
            plt2.plot(fitdatax,fitfunc(fitdatax, *startparams),label=label+" startfit")
        plt2.plot(fitdatax,fitfunc(fitdatax, *bestfitparams),mark_fit,label=label+" fit")
        if label!='': plt.legend()

    if show_diagnostics:
        return bestfitparams, fitparam_errors
    else:
        return bestfitparams

def get_phase(array):
    phase_out = np.zeros([len(array)])
    for idx,k in enumerate(array):
        phase_out[idx] = cmath.phase(k)

    return phase_out

#######################################################################
#######################################################################
#################### WRAPPERS FOR FITFUNCTIONS ########################
#######################################################################
#######################################################################

def fitlor(xdata, ydata, fitparams=None, domain=None, showfit=False, showstartfit=False,
           label="", debug=False, verbose=True,**kwarg):
    """
    Fit a Lorentzian; returns
    The quality factor can be found by Q = center/fwhm = center/(2*hwhm)
    :param xdata: Frequency
    :param ydata: Power in W
    :param fitparams: [offset,amplitude,center,hwhm]
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :param debug:
    :param verbose: Prints the fit results
    :return: [fitresult, fiterrors] if successful
    """
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata
    if fitparams is None:
        fitparams=[0,0,0,0]
        fitparams[0]=(fitdatay[0]+fitdatay[-1])/2.
        fitparams[1]=max(fitdatay)-min(fitdatay)
        fitparams[2]=fitdatax[np.argmax(fitdatay)]
        fitparams[3]=(max(fitdatax)-min(fitdatax))/10.
    if debug==True: print fitparams

    p1, p1_errors = fitbetter(fitdatax,fitdatay,lorfunc_better,fitparams,domain=None,showfit=showfit,
                    showstartfit=showstartfit,label=label,show_diagnostics=True,**kwarg)

    if verbose:
        parnames = ['offset', 'amplitude', 'center', 'hwhm']
        for par, name, err in zip(p1, parnames, p1_errors):
            print "%s : %.6f +/- %.6f"%(name, par, err)

    try:
        p1[3]=abs(p1[3])
    except:
        p1[0][3]=abs(p1[0][3])

    return p1, p1_errors

def fit_kinetic_fraction(xdata, ydata, fitparams=None, Tc_fixed=False, domain=None, showfit=False, showstartfit=False,
                         label="", debug=False, **kwarg):
    """
    Fits resonance frequencies (absolute, not shifts) vs. temperature due to kinetic inductance. Uses kinfunc
    Returns [f0, alpha, Tc]
    :param xdata: Temperature
    :param ydata: Resonance frequency
    :param fitparams: [f0_guess, alpha_guess, Tc_guess]
    :param Tc_fixed: True/False
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :param debug: True/False
    :return: List of optimal fitparameters (if successful) / None (if not successful)
    """
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata

    if fitparams is None:
        print "Please provide some initial guesses."

    if Tc_fixed:
        fitparams=fitparams[:2]

    p1 = fitgeneral(fitdatax, fitdatay, kinfunc, fitparams, domain=None, showfit=showfit, 
            showstartfit=showstartfit, label=label, **kwarg)
    return p1

def fit_double_lor(xdata, ydata, fitparams=None, domain=None, showfit=False, showstartfit=False,
                   label="", debug=False, **kwarg):
    """
    Fits two lorentzians. Uses twolorfunc. Convert to Q: center1/2*hwhm1, center2/2*hwhm2
    :param xdata: Frequency
    :param ydata: Power in W
    :param fitparams: [offset, amplitude 1, center 1, hwhm 1, amplitude 2, center 2, hwhm 2]
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :param debug: True/False
    :return: List of optimal fitparameters (if successful) / None (if not successful)
    """

    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata

    if fitparams is None:
        print "Please provide some initial guesses."

    p1 = fitgeneral(fitdatax, fitdatay, twolorfunc, fitparams, domain=None, showfit=showfit,
            showstartfit=showstartfit, label=label, no_offset = False)
    return p1

def fit_N_gauss(xdata, ydata, fitparams=None, domain=None, showfit=False, showstartfit=False,
                label="", debug=False, no_offset=False, **kwarg):
    """
    Fits a series of N Gaussian peaks or dips.
    If no_offset = True : Uses Ngaussfunc_no_offset
    If no_offset = False : uses Ngaussfunc
    :param xdata: x-data
    :param ydata: y-data
    :param fitparams: [offset, amplitude 1, res freq 1, sigma 1, ...] or [amplitude 1, res freq 1, sigma 1, ...] if no_offset=True
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :param debug: True/False
    :param no_offset: True/False
    :return: Optimal fit result (if successful).
    """
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata

    if fitparams is None:
        print "Please provide some initial guesses."

    if no_offset:
        p1 = fitgeneral(fitdatax, fitdatay, Ngaussfunc_no_offset, fitparams, domain=None, showfit=showfit,
                showstartfit=showstartfit, label=label, **kwarg)
    else:
        p1 = fitgeneral(fitdatax, fitdatay, Ngaussfunc, fitparams, domain=None, showfit=showfit,
                showstartfit=showstartfit, label=label, **kwarg)
    return p1

def fitexp(xdata, ydata, fitparams=None, domain=None, showfit=False, showstartfit=False, label=""):
    """
    Fit exponential decay of the form (p[0]+p[1]*exp(-(x-p[2])/p[3])). Uses expfunc.
    :param xdata: x-data
    :param ydata: y-data
    :param fitparams: [offset, amplitude, t0, tau]
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :return: Optimal fit parameters.
    """
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata
    if fitparams is None:
        fitparams=[0.,0.,0.,0.]
        fitparams[0]=fitdatay[-1]
        fitparams[1]=fitdatay[0]-fitdatay[-1]
        fitparams[1]=fitdatay[0]-fitdatay[-1]
        fitparams[2]=fitdatax[0]
        fitparams[3]=(fitdatax[-1]-fitdatax[0])/5.
    p1 = fitgeneral(fitdatax,fitdatay,expfunc,fitparams,domain=None,showfit=showfit,showstartfit=showstartfit,label=label)
    return p1

def fitpulse_err(xdata, ydata, fitparams=None, domain=None, showfit=False, showstartfit=False, label=""):
    """
    Fit pulse error decay (p[0]+p[1]*(1-p[2])^x). Uses pulse_errfunc
    :param xdata: x-data
    :param ydata: y-data
    :param fitparams: [offset, amplitude, ?]
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :return: Optimal fitresult.
    """
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata
    if fitparams is None:
        fitparams=[0.,0.]
        fitparams[0]=fitdatay[-1]
        fitparams[1]=fitdatay[0]-fitdatay[-1]
        fitparams[1]=fitdatay[0]-fitdatay[-1]

    p1 = fitgeneral(fitdatax,fitdatay,pulse_errfunc,fitparams,domain=None,showfit=showfit,showstartfit=showstartfit,label=label)
    return p1

def fitdecaysin(xdata, ydata, fitparams=None, domain=None, showfit=False, showstartfit=False, label=""):
    """
    Fits decaying sine wave of form: p[0]*np.sin(2.*pi*p[1]*x+p[2]*pi/180.)*np.e**(-1.*(x-p[5])/p[3])+p[4]
    :param xdata: x-data
    :param ydata: y-data
    :param fitparams: [A, f, phi (deg), tau, offset, t0]
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :return: Optimal fit parameters.
    """
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata
    if fitparams is None:
        FFT=scipy.fft(fitdatay)
        fft_freqs=scipy.fftpack.fftfreq(len(fitdatay),fitdatax[1]-fitdatax[0])
        max_ind=np.argmax(abs(FFT[4:len(fitdatay)/2.]))+4
        fft_val=FFT[max_ind]

        fitparams=[0,0,0,0,0]
        fitparams[4]=np.mean(fitdatay)
        fitparams[0]=(max(fitdatay)-min(fitdatay))/2.#2*abs(fft_val)/len(fitdatay)
        fitparams[1]=fft_freqs[max_ind]
        fitparams[2]=(cmath.phase(fft_val)-np.pi/2.)*180./np.pi
        fitparams[3]=(max(fitdatax)-min(fitdatax))

    decaysin3=lambda p,x: p[0]*np.sin(2.*np.pi*p[1]*x+p[2]*np.pi/180.)*np.e**(-1.*(x-fitdatax[0])/p[3])+p[4]
    p1 = fitgeneral(fitdatax,fitdatay,decaysin3,fitparams,domain=None,showfit=showfit,showstartfit=showstartfit,label=label)
    return p1

def fitsin(xdata, ydata, fitparams=None, domain=None, showfit=False, showstartfit=False, label=""):
    """
    Fits sin wave of form: p[0]*np.sin(2.*pi*p[1]*x+p[2]*pi/180.)+p[3].
    :param xdata: x-data
    :param ydata: y-data
    :param fitparams: [Amplitude, frequency, phase (deg), offset]
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :return: Optimal fit parameters.
    """
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata
    if fitparams is None:
        FFT=scipy.fft(fitdatay)
        fft_freqs=scipy.fftpack.fftfreq(len(fitdatay),fitdatax[1]-fitdatax[0])
        max_ind=np.argmax(abs(FFT[4:len(fitdatay)/2.]))+4
        fft_val=FFT[max_ind]

        fitparams=[0,0,0,0]
        fitparams[3]=np.mean(fitdatay)
        fitparams[0]=(max(fitdatay)-min(fitdatay))/2.
        fitparams[1]=fft_freqs[max_ind]
        fitparams[2]=(cmath.phase(fft_val)-np.pi/2.)*180./np.pi

    sin2=lambda p,x: p[0]*np.sin(2.*np.pi*p[1]*x+p[2]*np.pi/180.)+p[3]
    p1 = fitgeneral(fitdatax,fitdatay,sin2,fitparams,domain=None,showfit=showfit,showstartfit=showstartfit,label=label)
    return p1

def fitgauss(xdata, ydata, fitparams=None, no_offset=False, domain=None, showfit=False, showstartfit=False, label=""):
    """
    Fit a gaussian. You can choose to include an offset, using no_offset=True/False. Adjust fitparams accordingly:
    no_offset = True:   p[1] exp(- (x-p[2])**2/p[3]**2/2) (uses gaussfunc_nooffset)
    no_offset = False:  p[0]+p[1] exp(- (x-p[2])**2/p[3]**2/2) (uses gaussfunc)
    :param xdata: x points
    :param ydata: y points
    :param fitparams: [offset, amplitude, center, std] or [amplitude, center, std] if no_offset=True
    :param no_offset: True/False
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :return: Optimal fit parameters, if successful
    """
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata
    if fitparams is None:
        fitparams=[0,0,0,0]
        fitparams[0]=(fitdatay[0]+fitdatay[-1])/2.
        fitparams[1]=max(fitdatay)-min(fitdatay)
        fitparams[2]=fitdatax[np.argmax(fitdatay)]
        fitparams[3]=(max(fitdatax)-min(fitdatax))/3.

    if no_offset:
        fitfunc = gaussfunc_nooffset
        if len(fitparams) > 3:
            fitparams = fitparams[1:]
    else:
        fitfunc = gaussfunc

    p1 = fitgeneral(fitdatax,fitdatay,fitfunc,fitparams,domain=None,showfit=showfit,showstartfit=showstartfit,label=label)
    return p1

def fithanger(xdata, ydata, fitparams=None, domain=None, showfit=False, showstartfit=False, printresult=False,
              label="", mark_data='bo', mark_fit='r-'):
    """
    Fit Hanger Transmission (S21) data taking into account asymmetry. Uses hangerfunc.
    :param xdata: Frequency points
    :param ydata: Power in W
    :param fitparams: [f0, Qi, Qc, df, scale]
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param printresult: True/False
    :param label: String
    :param mark_data: Ex.: '.k'
    :param mark_fit: Ex.: '-r'
    :return: Optimal fit parameters [f0, Qi, Qc, df, scale] if successful.
    """
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata
    if fitparams is None:
        peakloc=np.argmin(fitdatay)
        ymax=(fitdatay[0]+fitdatay[-1])/2.
        ymin=fitdatay[peakloc]
        f0=fitdatax[peakloc]
        Q0=abs(fitdatax[peakloc]/((max(fitdatax)-min(fitdatax))/3.))
        scale= ymax
        Qi=Q0*(1.+ymax)
        Qc=Qi/(ymax)
        fitparams=[f0,abs(Qi),abs(Qc),0.,scale]
    fitresult=fitgeneral(fitdatax, fitdatay, hangerfunc, fitparams, domain=domain, showfit=showfit,
                         showstartfit=showstartfit, label=label, mark_data=mark_data, mark_fit=mark_fit)
    if printresult: print '-- Fit Result --\nf0: {0}\nQi: {1}\nQc: {2}\ndf: {3}\nScale: {4}'.format(fitresult[0],fitresult[1],fitresult[2],fitresult[3],fitresult[4])
    return fitresult

def fit_parabola(xdata, ydata, fitparams=None, domain=None, showfit=False, showstartfit=False,
            label="", debug=False, verbose=True, **kwarg):
    """
    Fit a parabola. Uses parabolafunc. Specify fitparams as [p0, p1, p2] where y = p0 + p1*(x-p2)**2
    :param xdata: x-data
    :param ydata: y-data
    :param fitparams: [p0, p1, p2] where y = p0 + p1*(x-p2)**2
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :param debug: True/False
    :param verbose: True/False, prints the fitresult
    :return: Fitresult, Fiterror
    """
    if fitparams is None:
        print "Please specify fit parameters in function input"
        return

    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata

    p1, p1err = fitbetter(fitdatax, fitdatay, parabolafunc, fitparams, domain=None, showfit=showfit,
                    showstartfit=showstartfit, label=label, show_diagnostics=True, **kwarg)

    if verbose:
        idx = 0
        print "Fit results for y = a0 + a1*(x-a2)**2 with 1 sigma confidence intervals"
        print "---------------------------------------------------------------------"
        for P, errP in zip(p1, p1err):
            print "a{} = {} +/- {}".format(idx, P, errP)
            idx+=1

    return p1, p1err

def fit_s11(xdata, ydata, mode='oneport', fitparams=None, domain=None, showfit=False, showstartfit=False,
            label="", debug=False, verbose=True, **kwarg):
    """
    Fit a S11 curve. Uses s11_mag_func_asymmetric. Note: fits the voltage signal, not a power (i.e. use this function
    to fit |S11| instead of |S11|**2. Note Qi = f0/(2*eps), Qc = f0/kr.
    :param xdata: Frequency points
    :param ydata: S11 voltage data
    :param fitparams: [f0, kr, eps, df, scale]
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :param debug: True/False
    :param verbose: True/False, prints the fitresults
    :return: Fitresult, Fiterror
    """

    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata

    if fitparams is None and mode == 'oneport':
        f0_guess = fitdatax[np.argmin(fitdatay)]
        kr_guess = (fitdatax[-1] - fitdatax[0])/5.
        eps_guess = (fitdatax[-1] - fitdatax[0])/5.
        df_guess = 0
        scale_guess = np.max(fitdatay)
        fitparams = [f0_guess, kr_guess, eps_guess, df_guess, scale_guess]
    if fitparams is None and mode == 'twoport':
        f0_guess = fitdatax[np.argmin(fitdatay)]
        Qc_guess = f0_guess/((fitdatax[-1] - fitdatax[0])/5.)
        Qi_guess = f0_guess/((fitdatax[-1] - fitdatax[0])/5.)
        df_guess = 0
        scale_guess = np.max(fitdatay)
        fitparams = [f0_guess, Qc_guess, Qi_guess, df_guess, scale_guess]

    if mode == 'oneport':
        p1, p1err = fitbetter(fitdatax, fitdatay, s11_mag_func_asymmetric, fitparams, domain=None, showfit=showfit,
                        showstartfit=showstartfit, label=label, show_diagnostics=True, **kwarg)
        names = ['f0', 'kr', 'eps', 'df', 'scale']
    else:
        p1, p1err = fitbetter(fitdatax, fitdatay, s11_mag_twoport, fitparams, domain=None, showfit=showfit,
                        showstartfit=showstartfit, label=label, show_diagnostics=True, **kwarg)
        names = ['f0', 'Qc', 'Qi', 'df', 'scale']

    if verbose:
        idx = 0
        print "Fit results for S11 func with 1 sigma confidence intervals"
        print "---------------------------------------------------------------------"
        for P, errP in zip(p1, p1err):
            print "{} = {} +/- {}".format(names[idx], P, errP)
            idx+=1

    return p1, p1err

def fit_fano(xdata, ydata, fitparams=None, domain=None, showfit=False, showstartfit=False,
             label="", debug=False, verbose=True, **kwarg):
    """
    Fit a fano lineshape. Uses fano_func.
    :param xdata: Frequency points
    :param ydata: Power in W
    :param fitparams: [w0, fwhm, q, scale]
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :param debug: True/False
    :param verbose: True/False. Prints the fitresult
    :return: Fitresult, Fiterror
    """
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata
    if fitparams is None:
        fitparams=[0,0,0,0]
        #fitparams[4]=(fitdatay[0]+fitdatay[-1])/2.
        fitparams[3]=max(fitdatay)-min(fitdatay)
        fitparams[0]=fitdatax[np.argmax(fitdatay)]
        fitparams[1]=(max(fitdatax)-min(fitdatax))/10.
        fitparams[2]=10.

    if debug==True: print fitparams

    p1, p1_errors = fitbetter(fitdatax,fitdatay,fano_func,fitparams,domain=None,showfit=showfit,
                    showstartfit=showstartfit,label=label,show_diagnostics=True,**kwarg)

    if verbose:
        parnames = ['f0', 'FWHM', 'Fano factor', 'Amplitude']
        for par, name, err in zip(p1, parnames, p1_errors):
            print "%s : %.6f +/- %.6f"%(name, par, err)

    return p1, p1_errors

def fitlor_asym(xdata, ydata, fitparams=None, domain=None, showfit=False, showstartfit=False,
                label="", debug=False, verbose=True, **kwarg):
    """
    Fit asymmetric lorentzian lineshape, derived from a capacitor in series with the LC circuit. Uses asym_lorfunc.
    See also fit_fano
    :param xdata: Frequency points
    :param ydata: S_21 Power in W
    :param fitparams: [w0, fwhm, q, scale]
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :param debug: True/False
    :param verbose: True/False. Prints the fitresult.
    :return: Fitresult, Fiterror
    """
    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata
    if fitparams is None:
        fitparams=[0,0,0,0]
        #fitparams[4]=(fitdatay[0]+fitdatay[-1])/2.
        fitparams[3]=max(fitdatay)-min(fitdatay)
        fitparams[0]=fitdatax[np.argmax(fitdatay)]
        fitparams[1]=(max(fitdatax)-min(fitdatax))/10.
        fitparams[2]=fitparams[0]/10.

    if debug==True: print fitparams

    p1, p1_errors = fitbetter(fitdatax,fitdatay,asym_lorfunc,fitparams,domain=None,showfit=showfit,
                    showstartfit=showstartfit,label=label,show_diagnostics=True,**kwarg)

    if verbose:
        parnames = ['f0', 'FWHM', 'Gamma', 'Amplitude']
        for par, name, err in zip(p1, parnames, p1_errors):
            print "%s : %.6f +/- %.6f"%(name, par, err)

    return p1, p1_errors

def fitpoly(xdata, ydata, fitparams=None, domain=None, showfit=False, showstartfit=False,
            label="", debug=False, verbose=True, **kwarg):
    """
    Fit a polynomial. Uses polyfunc_v2. Specify fitparams as [p0, p1, p2, ...] where
    y = p0 + p1*x + p2*x**2 + ...
    :param xdata: x-data
    :param ydata: y-data
    :param fitparams: [a0, a1, a2, a3, ...] where y = a0 + a1*x + a2*x**2 + ...
    :param domain: Tuple
    :param showfit: True/False
    :param showstartfit: True/False
    :param label: String
    :param debug: True/False
    :param verbose: True/False. Prints the fitresults.
    :return: Fitresult, Fiterror
    """
    if fitparams is None:
        print "Please specify fit parameters in function input"
        return

    if domain is not None:
        fitdatax,fitdatay = selectdomain(xdata,ydata,domain)
    else:
        fitdatax=xdata
        fitdatay=ydata

    p1, p1err = fitbetter(fitdatax, fitdatay, polyfunc_v2, fitparams, domain=None, showfit=showfit,
                    showstartfit=showstartfit, label=label, show_diagnostics=True, **kwarg)

    idx = 0
    if verbose:
        print "Fit results for y = a0 + a1*x + ... with 1 sigma confidence intervals"
        print "---------------------------------------------------------------------"
        for P, errP in zip(p1, p1err):
            print "a{} = {} +/- {}".format(idx, P, errP)
            idx+=1

    return p1, p1err

###########################################################
###########################################################
#################### FIT FUNCTIONS ########################
###########################################################
###########################################################

def lorfunc_better(x, offset, amplitude, center, hwhm):
    """
    Lorentzian with offset, compatible with fitbetter functionality.
    :param x: Frequency points
    :param offset: Power offset
    :param amplitude: Peak amplitude
    :param center: Frequency center
    :param hwhm: FWHM/2
    :return: offset+amplitude/(1+(x-center)**2/hwhm**2)
    """
    return offset+amplitude/(1+(x-center)**2/hwhm**2)

def lorfunc(p, x):
    """
    Lorentzian with offset, for use with fitgeneral functionality.
    :param p: [offset, peak amplitude, center, hwhm/2]
    :param x: Frequency points
    :return: p[0]+p[1]/(1+(x-p[2])**2/p[3]**2)
    """
    return p[0]+p[1]/(1+(x-p[2])**2/p[3]**2)

def kinfunc(p, x):
    """
    Function describing a resonance frequency due to kinetic inductance as function of temperature.
    :param p: [f0, alpha, Tc] or [f0, alpha]
    :param x: Temperature points
    :return: f0*(1-alpha/2.*1/(1-(x/Tc)**4))
    """
    f0 = p[0]
    alpha = p[1]

    if len(p) == 3:
        Tc = p[2]
    else:
        Tc = 1.2
        print "Assuming Tc = %.2f K"%Tc

    return f0*(1-alpha/2.*1/(1-(x/Tc)**4))

def twolorfunc(p, x):
    """
    :param p: [offset, amplitude 1, center 1, hwhm 1, amplitude 2, center 2, hwhm 2]
    :param x: Frequency points
    :return: p[0] + p[1]/(1+(x-p[2])**2/p[3]**2) + p[4]/(1+(x-p[5])**2/p[6]**2)
    """
    return p[0] + p[1]/(1+(x-p[2])**2/p[3]**2) + p[4]/(1+(x-p[5])**2/p[6]**2)

def asym_lorfunc(x, *p):
    """
    Asymmetric Lorentzian profile derived with capacitor in parallel.
    :param x: Frequency points
    :param p: [f0, fwhm, gamma, scale]
    :return: np.abs(p[3] /(1+2*1j*(x-p[0])/p[1]) + p[3] * 2*x*p[2]/p[0] / (+1j + 2*x*p[2]/p[0]))**2
    """
    return np.abs(p[3] /(1+2*1j*(x-p[0])/p[1]) + p[3] * 2*x*p[2]/p[0] / (+1j + 2*x*p[2]/p[0]))**2

def fano_func(x, *p):
    """
    Fano function. q describes the asymmetry.
    :param x: Frequency points
    :param p: [w0, fwhm, q, scale]
    :return: p[3] * (p[2]*p[1]/2. + (x-p[0]))**2/((p[1]/2.)**2 + (x-p[0])**2)
    """
    return p[3] * (p[2]*p[1]/2. + (x-p[0]))**2/((p[1]/2.)**2 + (x-p[0])**2)

def print_cavity_Q(fit):
    """
    Prints the Q values given center and HWHM
    :param fit: Optimal fitparameters found by fitlor
    :return: fit[2]/(2*fit[3])
    """
    print fit[2]/2/fit[3]
    return fit[2]/2/fit[3]

def gaussfunc(p, x):
    """
    Gaussian function, including an offset
    :param p: [offset, amplitude, center, standard deviation]
    :return: p[0]+p[1]*math.e**(-1./2.*(x-p[2])**2/p[3]**2)
    """
    return p[0]+p[1]*math.e**(-1./2.*(x-p[2])**2/p[3]**2)

def gaussfunc_nooffset(p, x):
    """
    Gaussian function, no offset
    :param p: [amplitude, center, standard deviation]
    :return: p[0]*math.e**(-1./2.*(x-p[1])**2/p[2]**2)
    """
    return p[0]*math.e**(-1./2.*(x-p[1])**2/p[2]**2)

def Ngaussfunc(p, x):
    """
    Gaussian function with N peaks, including an offset
    :param p: [offset, A1, f1, sigma1, A2, f2, sigma2, ...]
    :return: p[3*n+1]*math.e**(-1./2.*(x-p[3*n+2])**2/p[3*n+3]**2)
    """
    N = int((len(p)-1)/3.)
    Ngauss = p[0]
    for n in range(N):
        Ngauss += p[3*n+1]*math.e**(-1./2.*(x-p[3*n+2])**2/p[3*n+3]**2)
    return Ngauss

def Ngaussfunc_no_offset(p, x):
    """
    Gaussian function with N peaks, no offset
    :param p: [A1, f1, sigma1, A2, f2, sigma2, ...]
    :return: p[3*n+1]*math.e**(-1./2.*(x-p[3*n+2])**2/p[3*n+3]**2)
    """
    N = int((len(p)-1)/3.)
    Ngauss = 0
    for n in range(N):
        Ngauss += p[3*n+1]*math.e**(-1./2.*(x-p[3*n+2])**2/p[3*n+3]**2)
    return Ngauss

def expfunc(p, x):
    """
    Exponential function, including an offset
    :param p: [offset, amplitude, t0, tau]
    :param x: time
    :return: p[0]+p[1]*math.e**(-(x-p[2])/p[3])
    """
    return p[0]+p[1]*math.e**(-(x-p[2])/p[3])

def pulse_errfunc(p, x):
    """
    Pulse error function
    :param p: [offset, ?]
    :param x: x-axis
    :return: p[0]+0.5*(1-((1-p[1])**x))
    """
    return p[0]+0.5*(1-((1-p[1])**x))

def decaysin(p, x):
    """
    Exponential decaying sine function.
    :param p: [A, f, phi (deg), tau, offset, t0]
    :param x: Time
    :return: p[0]*np.sin(2.*np.pi*p[1]*x+p[2]*np.pi/180.)*np.e**(-1.*(x-p[5])/p[3])+p[4]
    """
    return p[0]*np.sin(2.*np.pi*p[1]*x+p[2]*np.pi/180.)*np.e**(-1.*(x-p[5])/p[3])+p[4]

def hangerfunc(p, x):
    """
    Hanger function
    :param p: [f0, Qi, Qc, df, scale]
    :param x: Frequency points
    :return: scale*(-2.*Q0*Qc + Qc**2. + Q0**2.*(1. + Qc**2.*(2.*a + b)**2.))/(Qc**2*(1. + 4.*Q0**2.*a**2.))
    """
    f0,Qi,Qc,df,scale = p
    a=(x-(f0+df))/(f0+df)
    b=2*df/f0
    Q0=1./(1./Qi+1./Qc)
    return scale*(-2.*Q0*Qc + Qc**2. + Q0**2.*(1. + Qc**2.*(2.*a + b)**2.))/(Qc**2*(1. + 4.*Q0**2.*a**2.))

def polynomial(p, x):
    """
    Polynomial of order 9.
    :param p: [offset (a0), linear (a1), quadratic (a2), ..., a9, center]
    :param x: x-axis
    :return: a0 + a1*(x-center) + a2*(x-center)**2 + ... + a9*(x-center)**9
    """
    return p[0]+p[1]*(x-p[-1])+p[2]*(x-p[-1])**2+p[3]*(x-p[-1])**3+p[4]*(x-p[-1])**4+p[5]*(x-p[-1])**5+\
           p[6]*(x-p[-1])**6+p[7]*(x-p[-1])**7+p[8]*(x-p[-1])**8+p[9]*(x-p[-1])**9

def s11_mag_func(x, *p):
    """
    Symmetric S11 magnitude function (reflection from resonator) in voltage.
    :param x: Frequency points
    :param p: [w0, Qi, Qc]
    :return: np.abs(((p[2]-p[1])/p[2] + 2*1j*(x-p[0])*p[1]/p[0])/((p[1]+p[2])/p[2] + 2*1j*(x-p[0])*p[1]/p[0]))
    """
    return np.abs(((p[2]-p[1])/p[2] + 2*1j*(x-p[0])*p[1]/p[0])/((p[1]+p[2])/p[2] + 2*1j*(x-p[0])*p[1]/p[0]))

def s11_phase_func(x, *p):
    """
    Symmetric S11 phase function (reflection from resonator) in radians.
    :param x: Frequency points
    :param p: [w0, Qi, Qc]
    :return: common.get_phase(((p[2]-p[1])/p[2] + 2*1j*(x-p[0])*p[1]/p[0])/((p[1]+p[2])/p[2] + 2*1j*(x-p[0])*p[1]/p[0]))
    """
    return get_phase(((p[2]-p[1])/p[2] + 2*1j*(x-p[0])*p[1]/p[0])/((p[1]+p[2])/p[2] + 2*1j*(x-p[0])*p[1]/p[0]))

def s11_mag_func_asymmetric(x, *p):
    """
    Asymmetric S11 magnitude function (reflection from 1 port resonator), in voltage!
    :param x: Frequency points
    :param p: [f0, kr, eps, df, scale]
    :return: p[4]*np.abs((1j*(x-p[0]) + (p[2]-p[1]/2.))/(1j*(x-p[0]) + 1j*p[3] + (p[2]+p[1]/2.)))
    """
    return p[4]*np.abs((1j*(x-p[0]) + (p[2]-p[1]/2.))/(1j*(x-p[0]) + 1j*p[3] + (p[2]+p[1]/2.)))

def s11_phase_func_asymmetric(x, *p):
    """
    Asymmetric S11 phase function (reflection from 1 port resonator)
    :param x: Frequency points
    :param p: [f0, kr, eps, df, scale]
    :return: common.get_phase((1j*(x-p[0]) + (p[2]-p[1]/2.))/(1j*(x-p[0]) + 1j*p[3] + (p[2]+p[1]/2.)))
    """
    return get_phase((1j*(x-p[0]) + (p[2]-p[1]/2.))/(1j*(x-p[0]) + 1j*p[3] + (p[2]+p[1]/2.)))

def s11_mag_twoport(x, *p):
    """
    Reflection off a 2 port resonator
    :param x: fpoints
    :param p: [f0, Qc, Qi, df, scale]
    :return: scale*(-1j*dw + 1j*ki - eps)/(1j*dw + kr + eps)
    """
    f0, Qc, Qi, df, scale = p
    dw = x-f0
    kr = f0/Qc
    eps = f0/Qi
    ki = df
    return scale*np.abs((-1j*dw + 1j*ki - eps)/(1j*dw + kr + eps))

def s11_phase_twoport(x, *p):
    """
    Reflection off a 2 port resonator
    :param x: fpoints
    :param p:  [f0, Qc, Qi, df, scale]
    :return: common.get_phase((-1j*dw + 1j*ki - eps)/(1j*dw + kr + eps))
    """
    f0, Qc, Qi, df, scale = p
    dw = x-f0
    kr = f0/Qc
    eps = f0/Qi
    ki = df
    return get_phase((-1j*dw + 1j*ki - eps)/(1j*dw + kr + eps))

def parabolafunc(x, *p):
    """
    Parabola function
    :param x: x-data
    :param p: [a0, a1, a2] where y = a0 + a1 * (x-a2)**2
    :return: p[0] + p[1]*(x-p[2])**2
    """
    return p[0] + p[1]*(x-p[2])**2

def polyfunc(p, x):
    """
    Polynomial of arbitrary order. Order is specified by the length of p
    :param p: [a0, a1, a2, a3, ...] where y = a0 + a1*x + a2*x**2 + ...
    :param x: x-data
    :return: p[0] + p[1]*x + p[2]*x**2 + ...
    """
    y = 0
    for n,P in enumerate(p):
        y += P * x**n
    return y

def polyfunc_v2(x, *p):
    """
    Polynomial of arbitrary order. Order is specified by the length of p
    :param x: x-data
    :param p: [a0, a1, a2, a3, ...] where y = a0 + a1*x + a2*x**2 + ...
    :return: p[0] + p[1]*x + p[2]*x**2 + ...
    """
    y = 0
    for n,P in enumerate(p):
        y += P * x**n
    return y

if __name__ =='__main__':
    pass