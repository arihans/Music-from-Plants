import argparse
import queue
import sys
import time
import threading
import subprocess
import asyncio

from scipy.signal import butter, filtfilt
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd
import pyautogui


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    'channels', type=int, default=[1], nargs='*', metavar='CHANNEL',
    help='input channels to plot (default: the first)')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-w', '--window', type=float, default=200, metavar='DURATION',
    help='visible time slot (default: %(default)s ms)')
parser.add_argument(
    '-i', '--interval', type=float, default=30,
    help='minimum time between plot updates (default: %(default)s ms)')
parser.add_argument(
    '-b', '--blocksize', type=int, help='block size (in samples)')
parser.add_argument(
    '-r', '--samplerate', type=float, default=2000, help='sampling rate of audio device')
parser.add_argument(
    '-n', '--downsample', type=int, default=10, metavar='N',
    help='display every Nth sample (default: %(default)s)')
parser.add_argument(
    '-c', '--cutoff', type=float, default=0.03, help='Cutoff frequency')
args = parser.parse_args(remaining)
if any(c < 1 for c in args.channels):
    parser.error('argument CHANNEL: must be >= 1')
mapping = [c - 1 for c in args.channels]  # Channel numbers start with 1
#---------------------------------------------

q = queue.Queue()
max_variance = 0
intervals = None


def lowpassFFT(data):
    """Lowpass a signal using FFT/iFFT"""
    fft = np.fft.fft(data)
    fftfreq = np.fft.fftfreq(len(data), 1/args.samplerate)
    for i, freq in enumerate(fftfreq):
        if abs(data) >= args.cutoff:
            fft[i] = 0
    data = np.fft.ifft(fft)
    return data

#Define the filter
#  def butter_filter(data, fs, lowcut, highcut, order):
#      nyq = 0.5 * fs
#      low = lowcut / nyq
#      high = highcut / nyq
#      
#      print(data)
#      b, a = butter(order, [high, low], 'bandpass', analog=False)
#      y = filtfilt(b, a, data, axis=0)
#  
#      return yserver


def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    # Fancy indexing with mapping creates a (necessary!) copy:
    q.put(indata[::args.downsample, mapping])

def initial_checks(fs):
    global max_variance, intervals
    """Check if theres any signal and measure highest and lowest peak"""
    print("Is it connected to something (Y | N)")
    if (input().lower() != 'y'):
        print('So.. Umm.. connect it please')
        exit()
    duration = 3
    data = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    #  zero_count = np.count_nonzero(data==0)
    #  if zero_count/data.size-zero_count >= 0:
    #      print("No Signal")
    #      return
    sorted_data = np.sort(data)
    data_interval = sorted_data[-1]/8
    intervals = [data_interval*i for i in range(8)]
    max_variance = np.var(data)
    return intervals

def get_data():
    global max_variance
    data = []
    variance = max_value = 0
    while True:
        try:
            data = q.get_nowait()
            variance = np.var(data)
            if variance > max_variance:
                max_variance = variance
            max_value = np.amax(data)
        except queue.Empty:
            return max_value, variance
        return max_value, variance

def keypress(key):
    pyautogui.keyDown(key)
    print("keypress")
    #  asyncio.sleep(duration)
    pyautogui.keyUp(key)


def play_music():
    threading.Timer(2, play_music).start()
    global intervals
    value, variance = get_data()
    duration = variance/max_variance * 5
    #  print("value={}, variance={}, intervals={}, duration={}".format(value, variance, intervals, duration))
    note = 0

    # Select Window
    subprocess.run(["wmctrl", "-a", "Piano"])

    key = ''
    if intervals[0]/10< value <= intervals[0]:
        key = 'a'
    elif value <= intervals[1]:
        key = 's'
    elif value <= intervals[2]:
        key = 'd'
    elif value <= intervals[3]:
        key = 'f'
    elif value <= intervals[4]:
        key = 'j'
    elif value <= intervals[5]:
        key = 'k'
    elif value <= intervals[6]:
        key = 'k'
    else:
        key = 'l'
    
    keypress(key)


def update_plot(frame):
    """This is called by matplotlib for each plot update.

    Typically, audio callbacks happen more frequently than plot updates,
    therefore the queue tends to contain multiple blocks of audio data.

    """
    global plotdata
    while True:
        try:
            #  data = butter_filter(q.get_nowait(), args.samplerate, 20, 50, 4)
            #  if (q.qsize() > 100):
            data = q.get_nowait()
            # Fast Fourier Transform, 10*log10(abs) is to scale it to dB
            # and make sure it's not imaginary
            #  dfft = np.abs(10.*np.log10(abs(np.fft.rfft(data))))
        except queue.Empty:
            break
        shift = len(data)
        plotdata = np.roll(plotdata, -shift, axis=0)
        plotdata[-shift:, :] = data
    for column, line in enumerate(lines):
        line.set_ydata(plotdata[:, column])
    return lines


try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        args.samplerate = device_info['default_samplerate']

    init_check = initial_checks(args.samplerate)

    if init_check is not None:
        length = int(args.window * args.samplerate / (1000 * args.downsample))
        plotdata = np.zeros((length, len(args.channels)))

        fig, ax = plt.subplots()
        lines = ax.plot(plotdata)
        if len(args.channels) > 1:
            ax.legend(['channel {}'.format(c) for c in args.channels],
                      loc='lower left', ncol=len(args.channels))
        ax.axis((0, len(plotdata), -1, 1))
        ax.set_yticks([0])
        ax.yaxis.grid(True)
        ax.tick_params(bottom=False, top=False, labelbottom=False,
                       right=False, left=False, labelleft=False)
        fig.tight_layout(pad=0)

        stream = sd.InputStream(
            device=args.device, channels=max(args.channels),
            samplerate=args.samplerate, callback=audio_callback)
        ani = FuncAnimation(fig, update_plot, interval=args.interval, blit=True)

        with stream:
            #  asyncio.run(play_music())
            play_music()
            plt.show()

except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))

