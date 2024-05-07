import pyaudio
import numpy as np
import matplotlib.pyplot as plt

# Set up PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

# Set up the plot
fig, ax = plt.subplots()

while True:
    # Read the audio data
    data = np.frombuffer(stream.read(1024), dtype=np.int16)

    # Compute and display the spectrogram
    Pxx, freqs, bins, im = ax.specgram(data, NFFT=1024, Fs=44100, noverlap=900)
    plt.pause(0.01)

# Close the stream
stream.stop_stream()
stream.close()
p.terminate()