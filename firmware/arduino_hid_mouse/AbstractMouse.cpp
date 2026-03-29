#include "AbstractMouse.h"

const int16_t& limit_xy(int const& xy)
{
    if     (xy < -32767) return -32767;
    else if(xy > 32767)  return 32767;
    else                 return xy;
}

AbstractMouse::AbstractMouse() : _buttons(0) {}

void AbstractMouse::click(const uint8_t& b)
{
    _buttons = b;
    move(0,0);
    _buttons = 0;
    move(0,0);
}

void AbstractMouse::move(const int& x, const int& y)
{

    int16_t limited_x = limit_xy(x);
    int16_t limited_y = limit_xy(y);
    sendRawReport(makeReport(limited_x, limited_y));
}

void AbstractMouse::buttons(const uint8_t& b)
{
    if (b != _buttons)
    {
        _buttons = b;
        move(0,0);
    }
}

void AbstractMouse::press(const uint8_t& b) 
{
    buttons(_buttons | b);
}

void AbstractMouse::release(const uint8_t& b)
{
    buttons(_buttons & ~b);
}

bool AbstractMouse::isPressed(const uint8_t& b)
{
    if ((b & _buttons) > 0) 
        return true;
    return false;
}
