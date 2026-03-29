#include "ImprovedMouse.h"

#if defined(_USING_HID)

static const uint8_t _hidReportDescriptor[] PROGMEM = {
    0x05, 0x01,
    0x09, 0x02,
    0xa1, 0x01,
    0x09, 0x01,
    0xa1, 0x00,
    0x85, 0x01,
    0x05, 0x09,
    0x19, 0x01,
    0x29, 0x03,
    0x15, 0x00,
    0x25, 0x01,
    0x95, 0x03,
    0x75, 0x01,
    0x81, 0x02,
    0x95, 0x01,
    0x75, 0x05,
    0x81, 0x03,
    0x05, 0x01,
    0x09, 0x30,
    0x09, 0x31,
    0x16, 0x01, 0x80,
    0x26, 0xff, 0x7f,
    0x75, 0x10,
    0x95, 0x02,
    0x81, 0x06,
    0xc0,
    0xc0,
};

#define LOW_BYTE(x) ((uint8_t)(x & 0xFF))
#define HIGH_BYTE(x) ((uint8_t)((x >> 8) & 0xFF))

ImprovedMouse_::ImprovedMouse_()
{
  static HIDSubDescriptor node(_hidReportDescriptor, sizeof(_hidReportDescriptor));
  HID().AppendDescriptor(&node);
}

void ImprovedMouse_::begin() 
{
}

void ImprovedMouse_::end() 
{
}

uint8_t* ImprovedMouse_::makeReport(const int16_t& x, const int16_t& y)
{
  uint8_t reportData[MOUSE_DATA_SIZE];
  reportData[0] = _buttons;
  reportData[1] = LOW_BYTE(x);
  reportData[2] = HIGH_BYTE(x);
  reportData[3] = LOW_BYTE(y);
  reportData[4] = HIGH_BYTE(y);
  return reportData;
}

void ImprovedMouse_::sendRawReport(const uint8_t* reportData)
{
  _buttons = reportData[0];
  HID().SendReport(1,reportData,MOUSE_DATA_SIZE);
}

ImprovedMouse_ ImprovedMouse;

#endif
