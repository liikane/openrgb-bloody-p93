#include "P93Hid.h"
#include "P93Protocol.h"
#include <array>
#include <algorithm>

#ifdef _WIN32
#include <setupapi.h>
#include <hidsdi.h>
#include <hidpi.h>
#include <cwctype>
#include <vector>
#include <string>

namespace {
constexpr unsigned short VENDOR_PAGE = 0xFF32;
constexpr unsigned short VENDOR_USAGE = 0x0218;
constexpr unsigned short REPORT_SIZE = 64;
constexpr unsigned char REPORT_ID = 0x07;

bool IsTarget(const wchar_t* path)
{
    std::wstring name(path);
    std::transform(name.begin(), name.end(), name.begin(), [](wchar_t c) { return std::towlower(c); });
    return name.find(L"vid_09da&pid_31de") != std::wstring::npos
        && name.find(L"col04") != std::wstring::npos;
}

bool ValidateHandle(HANDLE fd)
{
    PHIDP_PREPARSED_DATA preparsed = nullptr;
    if(!HidD_GetPreparsedData(fd, &preparsed))
    {
        return false;
    }

    HIDP_CAPS caps{};
    NTSTATUS status = HidP_GetCaps(preparsed, &caps);
    HidD_FreePreparsedData(preparsed);

    if(status < 0 || caps.UsagePage != VENDOR_PAGE ||
       caps.Usage != VENDOR_USAGE || caps.FeatureReportByteLength != REPORT_SIZE)
    {
        return false;
    }

    std::array<unsigned char, REPORT_SIZE> answer{};
    answer[0] = REPORT_ID;
    if(!HidD_GetFeature(fd, answer.data(), REPORT_SIZE))
    {
        return false;
    }

    return answer[0] == 7 && answer[1] == 3 && answer[2] == 6;
}
}
#endif

P93Hid::~P93Hid()
{
    Close();
}

bool P93Hid::Connect(std::string& error)
{
    std::lock_guard<std::mutex> lock(mutex_);
#ifdef _WIN32
    if(handle_ != INVALID_HANDLE_VALUE)
    {
        return true;
    }

    GUID hid_guid;
    HidD_GetHidGuid(&hid_guid);
    HDEVINFO info = SetupDiGetClassDevsW(&hid_guid, nullptr, nullptr, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);
    if(info == INVALID_HANDLE_VALUE)
    {
        error = "Could not enumerate Windows HID interfaces";
        return false;
    }

    HANDLE found = INVALID_HANDLE_VALUE;
    SP_DEVICE_INTERFACE_DATA iface{};
    iface.cbSize = sizeof(iface);

    for(DWORD n = 0; SetupDiEnumDeviceInterfaces(info, nullptr, &hid_guid, n, &iface); ++n)
    {
        DWORD bytes_needed = 0;
        SetupDiGetDeviceInterfaceDetailW(info, &iface, nullptr, 0, &bytes_needed, nullptr);
        if(bytes_needed < sizeof(SP_DEVICE_INTERFACE_DETAIL_DATA_W))
        {
            continue;
        }

        std::vector<unsigned char> buffer(bytes_needed);
        auto* detail = reinterpret_cast<PSP_DEVICE_INTERFACE_DETAIL_DATA_W>(buffer.data());
        detail->cbSize = sizeof(SP_DEVICE_INTERFACE_DETAIL_DATA_W);
        if(!SetupDiGetDeviceInterfaceDetailW(info, &iface, detail, bytes_needed, nullptr, nullptr) ||
           !IsTarget(detail->DevicePath))
        {
            continue;
        }

        HANDLE candidate = CreateFileW(detail->DevicePath, GENERIC_READ | GENERIC_WRITE,
                                       FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr,
                                       OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
        if(candidate == INVALID_HANDLE_VALUE)
        {
            error = "Bloody P93 HID found, but access was denied or device is busy";
            continue;
        }

        if(ValidateHandle(candidate))
        {
            found = candidate;
            break;
        }

        CloseHandle(candidate);
        error = "Bloody P93 HID reports do not match the verified protocol";
    }

    SetupDiDestroyDeviceInfoList(info);
    if(found == INVALID_HANDLE_VALUE)
    {
        if(error.empty())
        {
            error = "Bloody P93 (09DA:31DE / COL04) is not connected";
        }
        return false;
    }

    handle_ = found;
    direct_mode_ = false;
    return true;
#else
    error = "Experimental version currently supports Windows only";
    return false;
#endif
}

bool P93Hid::Send(const uint8_t data[64])
{
#ifdef _WIN32
    return handle_ != INVALID_HANDLE_VALUE && HidD_SetFeature(handle_, (PVOID)data, 64);
#else
    (void)data;
    return false;
#endif
}

bool P93Hid::SetColor(uint8_t red, uint8_t green, uint8_t blue)
{
    P93Protocol::Slots slot_colors{};
    slot_colors.fill({red, green, blue});
    return SetSlots(slot_colors);
}

bool P93Hid::SetSlots(const P93Protocol::Slots& slot_colors)
{
    std::lock_guard<std::mutex> lock(mutex_);
#ifdef _WIN32
    if(handle_ == INVALID_HANDLE_VALUE)
        return false;

    if(!direct_mode_)
    {
        const auto mode1 = P93Protocol::RgbMode();
        const auto mode2 = P93Protocol::DirectInit();
        if(!Send(mode1.data()) || !Send(mode2.data()))
            return false;
        direct_mode_ = true;
    }

    const auto colors = P93Protocol::ColorSlots(slot_colors);
    return Send(colors.data());
#else
    (void)slot_colors;
    return false;
#endif
}

void P93Hid::Close()
{
    std::lock_guard<std::mutex> lock(mutex_);
#ifdef _WIN32
    if(handle_ != INVALID_HANDLE_VALUE)
    {
        CloseHandle(handle_);
        handle_ = INVALID_HANDLE_VALUE;
    }
#endif
    direct_mode_ = false;
}

bool P93Hid::Connected() const
{
    std::lock_guard<std::mutex> lock(mutex_);
#ifdef _WIN32
    return handle_ != INVALID_HANDLE_VALUE;
#else
    return false;
#endif
}
