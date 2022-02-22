
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
            dfft = np.abs(10.*np.log10(abs(np.fft.rfft(data))))
        except queue.Empty:
            break
        shift = len(dfft)
        plotdata = np.roll(plotdata, -shift, axis=0)
        plotdata[-shift:, :] = dfft
    for column, line in enumerate(lines):
        line.set_ydata(plotdata[:, column])
    return lines

def visualizer():
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
