# FrackMatrix
Led Matrix Controller with Touch UI created in Python with Kivy. The target system is a Raspberry Pi 4. It is used in combination with an Arduino Uno which is hooked up with a bunch of WS2812B (or similar) LEDs as a matrix. Commands can be sent from the Pi to the Arduino through serial over USB.

## Features

- **Animations** Show signales as on a oszilloscope (sinde, saw)
- **Music** Sample audio through an USB Audio Interface and plot the peak of the music on the matrix. A selection of three effects is available
- **Text** Enter text to send to the matrix, scrolling, scaled or just steady.
- **Image** loading from disk
- **Paint** on touchscreen to the matrix

## Setup

1. Clone repository

2. Create python virtual environment
   ```shell
   python3 -m venv .venv
   ```

3. Activate venv
   ```shell
   source venv/bin/activate
   ```

4. Install libraries
   ```shell
   pip install -r requirements.txt
   ```

5. Run application

   ```shell
   ./run.sh
   ```

   

## Home

On the home screen, the serial port can be selected. Opening the spinner with the ports triggers a refresh of available ports.

![Home Screen](./assets/home-screen.png)

## Music



![Music Screen](./assets/music-screen.png)

## Text

- <kbd>Enter</kbd>: Send text to matrix
- <kbd>Esc</kbd>: Clear the selected text box

<img src="./assets/text-screen.png" alt="Text Screen" style="zoom: 67%;" />

## Paint

Paint screen allows to draw inside a frame representing the matrix. Color can be changed with the shortcuts or more detailed with color picker. The image is sent to the matrix by pressing "Save". A "Live" mode plots the image to the matrix 10 times per second.

![CleanShot 2024-05-21 at 08.06.58](./assets/paint-screen.png)
