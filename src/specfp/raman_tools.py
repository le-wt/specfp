import itertools
import numpy as np
from scipy.signal import find_peaks, savgol_filter


# Cosmic Ray removal


def consecutive_indices(X, n=1, criteria=True):
    '''
        Retrieve consecutive array indices with value = criteria

        Usage
        ------
        cons_idx = consecutive_indices(X, n, criteria=True)

        Input arguments
        ----------------
        X           --> [NDARRAY].
        n
        criteria    --> criteria to which compare the array values

        Outputs
        -------
        cons_idx    --> [list] consecutive indices with a value = criteria
    '''
    cons_idx = []
    for group in itertools.groupby(iter(range(len(X))), lambda x: X[x]):
        xi = list(group[1])
        if group[0] == criteria and len(xi) > n:
            for i in xi:
                cons_idx.append(i)
    return cons_idx


def removeCR(spectrum, crwidth=3, stdfactor=3, debug=False):
    '''
        Automatic removal of Cosmic Ray (CR) from a spectrum.

        Usage
        ------
        spectrum_ = removeCR(spectrum, stdfactor=3)

        Input arguments
        ----------------
        spectrum    --> [NDARRAY] a spectrum.

        stdfactor   --> [float] the standard deviation factor to use for the
                        CR detection threshold.
                        LOWER stdfactor -> MORE SENSITIVE.
                    Default - 3

        Outputs
        -------
        spectrum_   --> [NDARRAY] the spectrum after CRs have been removed.
    '''
    # normalize spectrum
    scale = spectrum.max()
    spectrum = spectrum / scale
    # find cosmic rays
    # second derivative of spectrum
    d1 = np.diff(spectrum)
    d2 = np.diff(d1)
    threshold = d2.mean() + stdfactor * d2.std()
    cosmic_ray = np.array([False for i in range(len(spectrum))])
    cosmic_ray[1:-1] = np.abs(d2) > threshold  # boolean vector (true if CR)

    # keep only cosmic rays that are smaller than crwidth pixel wide
    cosmic_ray[consecutive_indices(cosmic_ray, n=crwidth)] = False

    # include nearest neighbors
    for i in np.where(cosmic_ray)[0]:
        cosmic_ray[i - 1] = True
        cosmic_ray[i + 1] = True
    # removes cosmic rays with linear interpolation
    x = np.arange(len(spectrum))
    xp = x[~cosmic_ray]
    yp = spectrum[~cosmic_ray]
    spectrum_ = np.interp(x, xp, yp)
    # undo normalization
    spectrum_ = scale * spectrum_
    return spectrum_


def cosmic_rays_removal(spectrum, stdfactor=3, debug=False):
    '''
        Automatic removal of Cosmic Ray (CR) from a spectrum.

        Usage
        ------
        spectrum_ = removeCR(spectrum, stdfactor=3)

        Input arguments
        ----------------
        spectrum    --> [NDARRAY] a spectrum.

        stdfactor   --> [float] the standard deviation factor to use for the
                        CR detection threshold.
                        LOWER stdfactor -> MORE SENSITIVE.
                    Default - 3

        Outputs
        -------
        spectrum_   --> [NDARRAY] the spectrum after CRs have been removed.
    '''
    # normalize spectrum
    scale = spectrum.max()
    spectrum = spectrum / scale
    # find cosmic rays
    # second derivative of spectrum
    d1 = np.diff(spectrum)
    d2 = np.diff(d1)
    threshold = d2.mean() + stdfactor * d2.std()
    cosmic_ray = np.array([False for i in range(len(spectrum))])
    cosmic_ray[1:-1] = np.abs(d2) > threshold  # boolean vector (true if CR)
    # keep only cosmic rays that are one pixel wide
    #cosmic_ray[consecutive_indices(cosmic_ray)] = False
    # include nearest neighbors
    for i in np.where(cosmic_ray)[0]:
        if i > 320 and i < 340:
            cosmic_ray[i] = False
            continue
        if i > 365 and i < 385:
            cosmic_ray[i] = False
            continue
        cosmic_ray[i - 1] = True
        cosmic_ray[i + 1] = True
    # removes cosmic rays with linear interpolation
    x = np.arange(len(spectrum))
    xp = x[~cosmic_ray]
    yp = spectrum[~cosmic_ray]
    spectrum_ = np.interp(x, xp, yp)
    # undo normalization
    spectrum_ = scale * spectrum_
    return spectrum_


# NIST correction


nist_coefficients = [9.71937e-02, 2.28325e-04,
                     -5.86762e-08, 2.16023e-10,
                     -9.77171e-14, 1.15596e-17]


def getCorrectionCurve(measuredNIST, xaxis=None):
    '''
        getCorrectionCurve computes a system correction curve from a measured
        NIST raman spectrum.

        Usage
        ------
            correction_ = getCorrectionCurve(measuredNIST, xaxis=None)

        Input arguments
        ----------------
            measuredNIST [NDARRAY]:
                Measured NIST standard spectrum

            xaxis=None [NDARRAY]:
                xaxis of the system in cm-1 (should match size of
                measuredNIST). If None, the computation will be made in camera
                pixels and will not be accurate as the NIST coefficients are
                given in cm-1 units.

        Outputs
        -------
            correction_  --> The resulting system correction curve
    '''

    # NIST coefficients
    c = nist_coefficients

    # computing theoretical NIST response
    if xaxis is None:
        x = np.array(range(0, len(measuredNIST)))
    else:
        x = xaxis
    n0 = c[0]
    n1 = c[1] * x
    n2 = c[2] * x**2
    n3 = c[3] * x**3
    n4 = c[4] * x**4
    n5 = c[5] * x**5
    nist_theoretical = n0 + n1 + n2 + n3 + n4 + n5

    # Computing correction curve
    correction_ = measuredNIST / nist_theoretical
    correction_ = correction_ / np.max(correction_)

    return correction_

# Baseline Removal tools


def imodpoly(raw_intensity, poly_order=6, precision=0.005,
             max_iter=1000, imod=True):
    '''
        Baseline removal tool using a polynomial fit based on the IModPoly
        (or ModPoly) algorithm.

        Algorithm is presented in the article;
        'Automated Autofluorescence Background Subtraction Algorithm for
        Biomedical Raman Spectroscopy'
        DOI : 10.1366/000370207782597003

        Usage
        ------
        (raman, baseline) = imodpoly(raw_intensity,
                                       poly_order=6,
                                       precision=0.005,
                                       max_iter=1000,
                                       imod=True)

        Input arguments
        ----------------
        raw_intensity --> 1D array containing the intensity values to be fitted

        poly_order  --> order of the fitting polynomial
                    Default - 11

        precision   --> requirred precision, iterations will stop once this
                        value is reached.
                    Default - 0.005

        max_iter    --> maximum number of iterations, iterations will stop once
                        this value is reached.
                    Default - 1000

        imod        --> if imod == TRUE, algorith will use IModPoly (instead of
                        ModPoly)
                    Defaul - TRUE

        Outputs
        -------
        raman          --> The resulting raman spectra (without baseline)

        baseline       --> The removed baseline
    '''

    i = 1
    converged = False
    raman_data = np.array(raw_intensity)
    X = np.array(range(0, raman_data.shape[0]))
    std_dev = 0
    while not converged and i < max_iter:
        polyFit = np.polyval(np.polyfit(X, raman_data, poly_order), X)
        residual = raman_data - polyFit
        previous_std_dev = std_dev
        std_dev = np.std(residual)

        # if first iteration -> peak removal
        if imod:
            # IModPoly
            if i == 1:
                ind = np.where(raman_data > polyFit + std_dev)[0]
                raman_data[ind] = polyFit[ind] + std_dev

            ind = np.where(raman_data > polyFit + std_dev)[0]
            raman_data[ind] = polyFit[ind] + std_dev

        else:
            # ModPoly
            if i == 1:
                ind = np.where(raman_data > polyFit)[0]
                raman_data[ind] = polyFit[ind]

            ind = np.where(raman_data > polyFit)[0]
            raman_data[ind] = polyFit[ind]

        converged = np.abs((std_dev - previous_std_dev) / std_dev) < precision
        i = i + 1

    baseline = polyFit
    raman = raw_intensity - baseline
    return raman, baseline


# BubbleFill


def grow_bubble(x, x0, x2, bpos, bwidth, s):
    '''
        Grows a bubble bwidth wide centered in bpos until it touches the
        spectrum s.

        This function is not intended to be used as is, but is a subfunction
        of the bubblefill funtion.

        Usage
        ------
        bubble, x1 = grow_bubble(x, x0, x2, bpos, bwidth, s)
    '''
    A = (bwidth / 2)**2 - (x - bpos)**2
    A[A < 0] = 0
    bubble = np.sqrt(A) - bwidth  # create bubble
    x1 = x0 + (s[x0:x2 + 1] - bubble[x0:x2 + 1]
               ).argmin()  # find new intersection

    # grow bubble until touching
    bubble = bubble + (s[x0:x2 + 1] - bubble[x0:x2 + 1]).min()

    return bubble, x1


def keep_largest(x0, x2, baseline, bubble):
    '''
        Updates the values in baseline with a new bubble where
        bubble > Baseline in the [x0, x2] range.


        This function is not intended to be used as is, but is a subfunction
        of the bubblefill funtion.

        Usage
        ------
        baseline = keep_largest(x0, x2, baseline, bubble)
    '''
    for j in range(x0, x2 + 1):
        if baseline[j] < bubble[j]:
            baseline[j] = bubble[j]
    return baseline


def bubbleloop(bubblewidths, x, s, baseline):
    '''
        Computes the bubble growth of the bubblefill baseline removal
        algorithm.

        This function is not intended to be used as is, but is a subfunction
        of the bubblefill funtion.

        This is the bulk of the bubblefill algorithm and the *original* work of
        Guillaume Sheehy

        Usage
        ------
        baseline = bubbleloop(bubblewidths, x, s, baseline)

        Input arguments
        ----------------
        bubblewidths    --> [NDARRAY], [list] or [int] is the *minimal*
                            width allowed for bubbles. Provided by bubblefill

        x               --> [NDARRAY], np.arange(len(s)) provided by bubblefill

        s               --> [NDARRAY], rescaled and *pre-processed* spectrum
                            provided by bubblefill

        baseline        --> [NDARRAY], np.zeros(len(s)) provided by bubblefill

        Outputs
        -------

        baseline    --> [NDARRAY] the removed baseline needs to be smoothed
                        and rescaled.
    '''

    # initial range is always 0 -> len(s). aka the whole spectrum
    # bubblecue is a list of bubble regions as
    # [[x0, x2]_0, [x0, x2]_1, ... [x0, x2]_n]
    # additional bubble regions are added as the algo runs.
    bubblecue = [[0, len(s) - 1]]

    i = 0
    while i < len(bubblecue):

        # Bubble parameter from bubblecue
        x0, x2 = bubblecue[i]
        i += 1

        if x0 == x2:
            continue

        if type(bubblewidths) is not int:
            bubblewidth = bubblewidths[(x0 + x2) // 2]
        else:
            bubblewidth = bubblewidths

        if x0 == 0 and x2 != len(s) - 1:
            # half bubble right
            bwidth = 2 * (x2 - x0)
            bpos = x0
        elif x0 != 0 and x2 == len(s) - 1:
            # half bubble left
            bwidth = 2 * (x2 - x0)
            bpos = x2
        else:
            if (x2 - x0) < bubblewidth:
                continue
            # centered bubble
            bwidth = (x2 - x0)
            bpos = (x0 + x2) / 2

        # new bubble
        bubble, x1 = grow_bubble(x, x0, x2, bpos, bwidth, s)

        # add bubble to baseline by keeping largest value
        baseline = keep_largest(x0, x2, baseline, bubble)

        # Add new bubble(s) to bubblecue
        if x1 == x0:
            bubblecue.append([x1 + 1, x2])
        elif x1 == x2:
            bubblecue.append([x0, x1 - 1])
        else:
            bubblecue.append([x0, x1])
            bubblecue.append([x1, x2])

    return baseline


def bubblefill(spectrum, bubblewidths=40, fitorder=1, do_smoothing=True):
    '''
        Compute the raman and baseline from a spectrum using the Bubblefill
        algorithm.

        Usage
        ------
        raman, baseline = bubblefill(spectrum, bubblewidths=50, fitorder=1)

        Input arguments
        ----------------
        spectrum        --> [NDARRAY] a spectrum.

        bubblewidths    --> [NDARRAY], [list] or [int] is the *minimal*
                            width allowed for bubbles. Smaller values will
                            allow bubbles to further penetrate peaks resulting
                            in a more *aggressive* baseline removal. Larger
                            values are more *concervative* and might
                            underestimate baseline.

                            use [NDARRAY] or [list] to specify a width that
                            depends on the x position of the bubble. If doing
                            this, make sure len(bubblewidths) = len(spectrum).
                            Otherwise if bubblewidths [int], the same width
                            will be used everywhere.

        fitorder        --> [int] the order of the polynomial fit used to
                            remove the *overall* baseline slope.
                            Recommendend value is 1 (for linear slope). Higher
                            order will result in Runge's phenomena and
                            potentially undesirable and unpredictable effects.

                            fitorder = 0 is the same as not removing the
                            *overall* baseline slope

        Outputs
        -------
        raman       --> [NDARRAY] the remaining raman spectrum after baseline
                        removal.

        baseline    --> [NDARRAY] the removed baseline.

        Guillaume Sheehy 2021-01
    '''
    s = spectrum
    x = np.arange(len(s))

    # Remove general slope
    slope = np.poly1d(np.polyfit(x, spectrum, fitorder))(x)
    s = s - slope
    smin = s.min()  # value needed to return to the original scaling
    s = s - smin  # bring min of s to 0
    scale = (s.max() / len(s))
    s = s / scale  # Rescale spectrum to X:Y=1:1

    baseline = np.zeros(s.shape)

    # Bubble loop (this is the bulk of the algorithm)
    baseline = bubbleloop(bubblewidths, x, s, baseline)

    # Bringing baseline back in original scale
    baseline = baseline * scale + slope + smin

    # Final smoothing of baseline (only if bubblewidth is not a list!!!)
    if type(bubblewidths) is int and do_smoothing:
        baseline = savgol_filter(baseline, 2 * (bubblewidths // 4) + 1, 3)

    raman = spectrum - baseline

    return raman


# SNR tools


def ramanSNR(rawRaman, rawBG, instr_corr, exposure_time, laser_power,
             camera_gain=1):
    '''
        ramanSNR computes an SNR spectrum for a Raman acquisition (of n
        spectrum)

        Usage
        ------
        snr_ = ramanSNR(rawRaman, rawBG, instr_corr, exposure_time,
                        laser_power, camera_gain=1)

        Input arguments
        ----------------
        rawRaman    --> a (mxn) numpy array containing m raw raman spectrum of
                        width n.CA

        rawBG       --> a (1xn) numpy array containing the acquisition raw
                        background spectrum.

        instr_corr  --> a (1xn) numpy array containing the system's correction
                        curve.

        exposure_time   --> the acquisition's exposure time [ms]

        laser_power     --> the acquisition's laser power [mW]

        camera_gain     --> the acquisition's used camera gain (1).

        Outputs
        -------
        snr_        --> The resulting acquisition snr spectrum.
    '''
    # Conversions to np.array
    rawRaman = np.array(rawRaman)
    rawBG = np.array(rawBG)
    instr_corr = np.array(instr_corr)
    # Empirical constant
    C = 2.23
    # Gain of the camera
    G = camera_gain
    # Exposure time
    t = exposure_time
    # Laser power
    P = laser_power
    # normalized system response
    R = instr_corr / max(instr_corr)
    # number of spectra
    n = rawRaman.shape[0]

    # Raman + fluo spectrum normalized to exposure time, laser power, gain and
    # system response
    ramanAF = (rawRaman - rawBG) / (G * t * P * R)
    raman_ = np.zeros(rawRaman.shape)
    baseline = np.zeros(rawRaman.shape)
    for i in range(n):
        r, f = imodpoly(ramanAF[i, :])
        raman_[i, :] = r
        baseline[i, :] = f
    raman_ = raman_.mean(axis=0)
    baseline = baseline.mean(axis=0)

    # Background signal (ambient light) normalized to exposure time, laser
    # power, gain and system response
    BG = rawBG / (G * t * R)

    # SNR
    snr_ = C * np.sqrt(n * t * P * R) * raman_ \
        / np.sqrt(raman_ + baseline + 2 * BG / P)
    # SNR formula for j spectral band
    # Eq.1 of "Mean Raman SNR IP description"
    # return : raman, AF, background, SNR
    return snr_


def SNV(array) -> np.ndarray:
    """Standard Normal Variate
    
    Data normalization centering the data around 0 and with a unit
    (0) standard deviation.
    
    Parameters
    ----------
    array: (2, s)
        An array where the first axis is of size equal to 2 and it
        is assumed that array[0] contains the wavelengths and the
        array[1] contains the spectrum to be normalized.
        
    Returns
    -------
    array
        The normalized array
        
    Example
    -------
    wavelenghts = range(600, 1600, 100)
    spectrum = np.random.rand(len(wavelenghts))
    normalized = SNV([wavelenghts, spectrum])
    """
    array = np.array(array, dtype=float)  # convert and copy
    if array.ndim == 2:
        array[..., 1:, :] -= array[..., 1:, :].mean(axis=sans_penultimate(array))
        array[..., 1:, :] /= array[..., 1:, :].std(axis=sans_penultimate(array))
    else:
        array -= array.mean()
        array /= array.std()
    return array
