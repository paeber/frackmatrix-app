#include "FastLED.h"

//You must include a reference to the FastLED library to use this code. http://fastled.io/

// Matrix Configuration
const int width = 16; 
const int height = 16;
const int DATA_PIN = 6;


const int NUM_LEDS = width * height;
int drawIndex = 0;
int x;
int y;
byte pixelType = 0;
char drawIn[5];
char frameIn[NUM_LEDS * 3];


// Define the array of leds
CRGB leds[NUM_LEDS];

int xy_to_snake(int x, int y, int width) {
    if (y % 2 == 1) {
        return y * width + x;
    } else {
        return y * width + (width - x - 1);
    }
}

void setup() {

  FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);

  for (int i = 0; i < NUM_LEDS; i++)
  {
    leds[i] = CRGB::Black;
  }
  FastLED.show();

  Serial.begin(1000000);

}

void loop() {}

void serialEvent() {
  pixelType = Serial.read();

  switch (pixelType) {
    case 0:
      //draw mode
      Serial.readBytes(drawIn, 5);
      x = (int)drawIn[0];
      y = (int)drawIn[1];
      drawIndex = (int)(y * width) + x;
      drawIndex = xy_to_snake(x, y, width);

      leds[drawIndex] = CRGB((byte)drawIn[2], (byte)drawIn[3], (byte)drawIn[4]);
      FastLED.show();
      break;

    case 1:
      //clear mode
      for (int i = 0; i < NUM_LEDS; i++)
      {
        leds[i] = CRGB::Black;
      }

      FastLED.show();
      break;

    case 2:
      //frame in mode
      Serial.readBytes((char*)frameIn, NUM_LEDS * 3);
      for(int i = 0; i < NUM_LEDS; i++){
        int snake_index = xy_to_snake(i % width, i / width, width);
        leds[snake_index] = CRGB((byte)frameIn[i * 3], (byte)frameIn[i * 3 + 1], (byte)frameIn[i * 3 + 2]);
      }
      FastLED.show();
      break;

    case 10:
      Serial.flush();
      break;

    case 11:
      Serial.write(width);
      Serial.write(height);
      break;
  }

  Serial.write(16);
}
