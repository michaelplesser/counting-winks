#!/usr/bin/env python3

#import av  # This module is only needed if processing the video data.
            # It can be a pain in the ass to get its dependencies working.
            # For the analysis, just use the data/*.npy files, no av needed!

import os
import sys
import scipy
import argparse
import scipy.stats
import numpy as np
import matplotlib.pyplot as plt

class load_data:
    def __init__(self):
        self.times          = np.load('data/times.npy')
        self.light1_data    = np.load('data/Light1_data.npy')
        self.light2_data    = np.load('data/Light2_data.npy')

def input_args():
    parser = argparse.ArgumentParser(description="counting-winks.py is a program to analyze the frequency of two blinking lights on the Boston skyline as viewed from Mission Hill.\
                                                  To run, use 'python3 counting-winks.py'. For further options, try 'python3 counting-winks.py -h', or '--help'.")

    parser.add_argument('-b', action='store_true', help='Supress graphics, display no plots')
    parser.add_argument('-t', action='store', type=float, help='How many seconds to analyze')

    args = parser.parse_args()

    return args


def process_video():
    ''' 
        Process the video file into managable data arrays.

        Takes in a .mp4 and then extracts the time of each frame,
        and the normalized R(GB) pixel value for each of the two lights.
        
        These data arrays are saved as .npy files because the processing is
        somewhat time consuming, so this way it can be done just once.

        This is the only section that requires the 'av' library, which can be
        difficult to install due to dependancy issues, so if you have the data
        files (IE from git) don't bother installing 'av' unless you really want to.
    '''

    print('Processing video...')

    intensity_L1 = []   # Light 1 data array
    intensity_L2 = []   # Light 2 data array
    times        = []
    vid_file = 'video_data.mp4'
    vid = av.open(vid_file)
    for frame in vid.decode(video=0):
        print('\tCurrent time being processed: %02d:%05.2f:'% (int(frame.time//60), frame.time%60), end='\r') 
        times.append(frame.time)
        arr = np.asarray(frame.to_image())  # Generate an RGB array for each pixel in the frame
        pix_val_L1 = arr[420,713][0]/255.   # Pixel RGB value (only take R, it's a red light) of light 1, and normalize to max RGB value (255)
        pix_val_L2 = arr[360,473][0]/255.   # Pixel RGB value (only take R, it's a red light) of light 2, and normalize to max RGB value (255)
        intensity_L1.append(pix_val_L1)
        intensity_L2.append(pix_val_L2)

    ### Save data files under ./data as .npy files 
    if not os.path.exists('./data'): os.mkdir('./data')
    np.save('data/times',times)
    np.save('data/Light1_data',intensity_L1)
    np.save('data/Light2_data',intensity_L2)

def FFT(x, y):
    ''' 
        Perform the Fast Fourier Transform
    '''

    ft    = np.abs(np.fft.fft(y))                                   # Perform the FFT
    freqs = np.linspace(0, 1/(x[1]-x[0]), len(x))                   # Generate the frequency data (transformed x-values)

    ## This is a rather subtle point related to fourier transforms
    ## Since the input is real-valued, only half of the output is actual info.
    ft    = ft[   :len(freqs)//2]
    freqs = freqs[:len(freqs)//2]

    return freqs, ft


def find_fundamental_frequency(freqs,amps,args):
    '''
        This function finds the fundamental frequency (first harmonic) of a transform.
        We could just use the first non-trivial peak's frequency, but because the lights
        are so close in frequency this isn't the best we can do. Indeed we care more about
        the higher harmonics because they are more sensitive. 

        To find the fund. freq. we first identify all peaks corresponding to a square wave.
        A useful piece of information is that a pure square wave has only odd harmonics.
        The even harmonics in our distrbution are ignored (but maybe I'll use them later).*** (not quite true!)

        Since the peaks should come in integer multiples of the fundamental frequency,
        a linear fitting of the frequency value vs. harmonic number is what we want.
        
        The slope of the linear fit is a better estimate of the fundamental frequency.
    '''

    print('\tAnalyzing light data...')

    peaks = find_peaks(freqs, amps)                                                 # Function defined below
    try:
        peak_fs, peak_as = zip(*peaks)                                              # Unzip [(x1,y1),(x2,y2),...] -> [x1, x2, ...], [y1, y2, ...]
    except ValueError:
        sys.exit("\nNot enough data given, no peaks found :( \nTry a longer -t\nBye bye!\n")
     
    harmonics = [i/peak_fs[0] for i in peak_fs]                                 # Harmonics are integer multiples of your fundamental frequency
    slope, intercept, r, p, stderr = scipy.stats.linregress(harmonics, peak_fs) # Apply a linear fit (maybe unnecessary? To be investigated...)
    line = slope*np.array(harmonics)+intercept

    print('\t\tPlotting frequency spectrum with "found" peaks')
    plt.plot(freqs, amps)                                                       # Plot spectrum
    plt.plot(peak_fs, peak_as, 'ro')                                            # Plot peaks as points
    if not args.b : plt.show()
    
    print('\t\tPlotting frequency vs harmonic number\n')
    plt.plot(harmonics, peak_fs, 'o', harmonics, line)
    if not args.b : plt.show()
    
    return peaks, slope 

def find_peaks(x,y):
    '''
        A basic peak-finding algorithm.
        Search for samples with amplitude above some threshold which are the largest sample in some range
    '''
    peaks = []
    for i, d in enumerate(zip(x, y)):
        ### These two parameters help define the peak search.
        ### They're manually tuned, but auto-tuning is TBD in the future
        buf = 50                                           # A given y must be the largest in +-(buf) samples to be a "peak" 
        threshold = 100                                     # It also must be above a threshold value
        if i<buf or i>(len(x)-buf): continue                # Avoid index out of bound errors, we don't mind ignoring these regions in the peak hunt
        if d[1] == max(y[i-buf:i+buf]) and d[1]>threshold:  # Peak-finding logic
            peaks.append([d[0], d[1]])                      # Add the point as a peak
    return peaks

def main():
    
    args = input_args()

    print('Beginning analysis...\n')

    ### Load the data produced in process_video()
    try: 
        data = load_data()
    except FileNotFoundError:
        print('\tData files not found. Running process_video()')
        process_video()                                         # Process the video file to obtain pixel data, times, etc...
        data = load_data()                                      # Load the data

    ### As a fun way to play with time-frequency uncertainty, the -t <int> flag shortens the amount of data transformed (and gives worse results!)
    if args.t:
        data.times = [ti for ti in data.times if ti<args.t]
        data.light1_data = data.light1_data[:len(data.times)]
        data.light2_data = data.light2_data[:len(data.times)]

    ### Plot 10 seconds of light1's waveform for reference.
    print('\tPlotting 10 seconds of light1 waveform\n')
    plt.plot(data.times, data.light1_data)                      # Plot the waveform in the time domain
    plt.gca().set_xlim([0,10])                                  # Set an axis range for 0,10 seconds on the x-axis
    if not args.b:  plt.show()
    
    ### Perform the fourier transform
    freqs_1, ft_1 = FFT(data.times, data.light1_data)
    freqs_2, ft_2 = FFT(data.times, data.light2_data)

    ### Analyze the data to find the fundamental frequency
    peaks_1, f0_1 = find_fundamental_frequency(freqs_1, ft_1, args)
    peaks_2, f0_2 = find_fundamental_frequency(freqs_2, ft_2, args)

    #print(f0_1, f0_2)
    period = 1. / abs(f0_1 - f0_2) / 60.  # Beat period (in minutes)

    print('Analysis complete\n')
    print('\tLight 1 was found to have a frequency of {0:.4f} Hz and Light 2 had a frequency of {1:.4f} Hz'.format(f0_1,f0_2))
    print('\tThe beat period (time for a full phase-cycle) is {0:2.2f} minutes.\n'.format(period))

    return


if __name__=="__main__":
    main()
