#pragma once
#include <cstdint>
#include "P93Protocol.h"
#include <mutex>
#include <string>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#endif

class P93Hid
{
public:
    ~P93Hid();
    bool Connect(std::string& error);
    bool SetColor(uint8_t red, uint8_t green, uint8_t blue);
    bool SetSlots(const P93Protocol::Slots& slot_colors);
    void Close();
    bool Connected() const;
private:
    bool Send(const uint8_t data[64]);
    mutable std::mutex mutex_;
#ifdef _WIN32
    HANDLE handle_ = INVALID_HANDLE_VALUE;
#endif
    bool direct_mode_ = false;
};
