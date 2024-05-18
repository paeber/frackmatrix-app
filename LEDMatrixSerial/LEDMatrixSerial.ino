#include "FastLED.h"

//You must include a reference to the FastLED library to use this code. http://fastled.io/

#define BRIGHTNESS 255

// Matrix Configuration
const int width = 50; 
const int height = 20;
const int panel_width = 50;
const int panel_height = 10;
const int DATA_PIN_UPPER = 6;
const int DATA_PIN_LOWER = 5;


const int NUM_LEDS = width * height;
const int NUM_LEDS_2 = width * height / 2;
int drawIndex = 0;
int x;
int y;
byte pixelType = 0;
char drawIn[5];
char frameIn[NUM_LEDS * 3];


// Define the array of leds
//CRGB leds[NUM_LEDS];
CRGB leds_upper[NUM_LEDS_2];
CRGB leds_lower[NUM_LEDS_2];

int xy_to_snake_topright(int x, int y, int width) {
    if (y % 2 == 1) {
        return y * width + x;
    } else {
        return y * width + (width - x - 1);
    }
}

int xy_to_snake(int x, int y, int width) {
    // Flip the y coordinate
    y = height - 1 - y;

    // Flip the x coordinate on every other row
    if (y % 2 == 1) {
        x = width - 1 - x;
    }

    return y * width + x;
}

void setup() {

  //FastLED.addLeds<WS2812B, DATA_PIN_UPPER, RGB>(leds, NUM_LEDS);
  FastLED.addLeds<WS2812B, DATA_PIN_UPPER, RGB>(leds_upper, NUM_LEDS_2);
  FastLED.addLeds<WS2812B, DATA_PIN_LOWER, RGB>(leds_lower, NUM_LEDS_2);
  FastLED.setBrightness(BRIGHTNESS);

  for (int i = 0; i < NUM_LEDS_2; i++)
  {
    //leds[i] = CRGB::Black;
    leds_upper[i] = CRGB::Black;
    leds_lower[i] = CRGB::Black;
  }
  FastLED.show();

  Serial.begin(1000000);

  
  /*for (int i = 0; i < NUM_LEDS_2; i++)
  {
    leds_upper[i] = CRGB::Red;
    leds_lower[i] = CRGB::Red;
    FastLED.show();
    delay(20);
  }*/
  /*
  for (int i = 0; i < NUM_LEDS; i++)
  {
    leds[i] = CRGB::Green;
    FastLED.show();
    delay(20);
  }
  for (int i = 0; i < NUM_LEDS; i++)
  {
    leds[i] = CRGB::White;
    FastLED.show();
    delay(20);
  }
  */
  

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

      //leds[drawIndex] = CRGB((byte)drawIn[2], (byte)drawIn[3], (byte)drawIn[4]);
      if(drawIndex < 500){
        leds_upper[drawIndex % 500] = CRGB((byte)drawIn[2], (byte)drawIn[3], (byte)drawIn[4]);
      } else {
        leds_lower[drawIndex % 500] = CRGB((byte)drawIn[2], (byte)drawIn[3], (byte)drawIn[4]);
      }
      FastLED.show();
      break;

    case 1:
      //clear mode
      for (int i = 0; i < NUM_LEDS_2; i++)
      {
        //leds[i] = CRGB::Black;
        leds_upper[i] = CRGB::Black;
        leds_lower[i] = CRGB::Black;
      }

      FastLED.show();
      break;

    case 2:
      //frame in mode
      Serial.readBytes((char*)frameIn, NUM_LEDS * 3);
      for(int i = 0; i < NUM_LEDS_2; i++){  
        int i2 = 500 + i;
        int snake_index = xy_to_snake(i % width, i / width, width);
        int snake_index_2 = xy_to_snake(i2 % width, i2 / width, width) -500 ;
        //leds[snake_index] = CRGB((byte)frameIn[i * 3], (byte)frameIn[i * 3 + 1], (byte)frameIn[i * 3 + 2]);
        leds_upper[snake_index] = CRGB((byte)frameIn[i * 3], (byte)frameIn[i * 3 + 1], (byte)frameIn[i * 3 + 2]);
        leds_lower[snake_index_2] = CRGB((byte)frameIn[i2 * 3], (byte)frameIn[i2 * 3 + 1], (byte)frameIn[i2 * 3 + 2]);
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
