#include "../src/P93Protocol.h"
#include <cassert>
#include <cstdint>
#include <iostream>

int main()
{
    const auto mode = P93Protocol::RgbMode();
    const auto init = P93Protocol::DirectInit();
    assert(mode.size() == 64 && mode[0] == 7 && mode[1] == 3 && mode[2] == 6 && mode[3] == 1);
    assert(init.size() == 64 && init[0] == 7 && init[1] == 3 && init[2] == 6 && init[3] == 0 && init[8] == 1);

    const auto purple = P93Protocol::StaticColor(160, 0, 255);
    for(std::size_t i = 0; i < P93Protocol::SlotCount; ++i)
    {
        assert(purple[8+3*i] == 160);
        assert(purple[9+3*i] == 0);
        assert(purple[10+3*i] == 255);
    }

    P93Protocol::Slots slots{};
    slots[0] = {255, 210, 0};
    slots[14] = {0, 100, 255};
    const auto custom = P93Protocol::ColorSlots(slots);
    assert(custom[8] == 255 && custom[9] == 210 && custom[10] == 0);
    assert(custom[50] == 0 && custom[51] == 100 && custom[52] == 255);
    for(std::size_t i=4;i<8;++i) assert(custom[i] == 0);
    for(std::size_t i=53;i<64;++i) assert(custom[i] == 0);

    const auto a = P93Protocol::SplitBeacon(true);
    const auto b = P93Protocol::SplitBeacon(false);
    for(std::size_t i=0;i<P93Protocol::SlotCount;++i)
    {
        const bool first = i < 7;
        assert((a[i][0] == 255) == first);
        assert((b[i][0] == 255) != first);
    }
    std::cout << "P93 64-byte HID packet and beacon tests passed" << std::endl;
    return 0;
}
