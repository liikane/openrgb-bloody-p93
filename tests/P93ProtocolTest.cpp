#include "../src/P93Protocol.h"
#include <cassert>
#include <cstdint>
#include <iostream>

int main()
{
    using namespace P93Protocol;
    static_assert(SlotCount == 15, "P93 vendor HID packet has 15 triple positions");
    static_assert(PhysicalLedCount == 8, "P93 mouse has 8 physical LEDs");

    const auto mode = RgbMode();
    const auto init = DirectInit();
    assert(mode.size() == 64 && mode[0] == 7 && mode[1] == 3 && mode[2] == 6 && mode[3] == 1);
    assert(init.size() == 64 && init[0] == 7 && init[1] == 3 && init[2] == 6 && init[3] == 0 && init[8] == 1);

    const auto purple = StaticColor(160, 0, 255);
    for(std::size_t i = 0; i < SlotCount; ++i)
    {
        assert(purple[8+3*i] == 160);
        assert(purple[9+3*i] == 0);
        assert(purple[10+3*i] == 255);
    }

    Slots colors{};
    for(std::size_t i = 0; i < PhysicalLedCount; ++i)
        colors[i] = {static_cast<std::uint8_t>(i+1), 210, 0};
    const auto report = ColorSlots(colors);
    for(std::size_t i=0;i<PhysicalLedCount;++i)
    {
        assert(report[8+3*i] == i+1);
        assert(report[9+3*i] == 210);
        assert(report[10+3*i] == 0);
    }
    for(std::size_t i=PhysicalLedCount;i<SlotCount;++i)
    {
        assert(report[8+3*i] == 0);
        assert(report[9+3*i] == 0);
        assert(report[10+3*i] == 0);
    }
    for(std::size_t i=53;i<64;++i) assert(report[i] == 0);

    const auto a = SplitBeacon(true);
    const auto b = SplitBeacon(false);
    for(std::size_t i=0;i<SlotCount;++i)
    {
        const bool isA = i==0 || i==3;
        const bool isVisible = i<PhysicalLedCount;
        assert((a[i][0] == 255) == (isVisible && isA));
        assert((b[i][0] == 255) == (isVisible && !isA));
        assert(a[i][1] == (isVisible && isA ? 210 : 0));
        assert(b[i][1] == (isVisible && !isA ? 210 : 0));
    }
    const auto customA = SplitBeacon(true, Color{255,0,0}, Color{0,0,255});
    const auto customB = SplitBeacon(false, Color{255,0,0}, Color{0,0,255});
    assert(customA[0] == (Color{255,0,0}));
    assert(customA[3] == (Color{255,0,0}));
    assert(customA[1] == (Color{0,0,0}));
    assert(customB[1] == (Color{0,0,255}));
    assert(customB[7] == (Color{0,0,255}));
    assert(customB[0] == (Color{0,0,0}));
    for(std::size_t i=PhysicalLedCount;i<SlotCount;++i)
    {
        assert(customA[i] == (Color{0,0,0}));
        assert(customB[i] == (Color{0,0,0}));
    }
    std::cout << "P93 eight physical LEDs, customizable beacon colors: PASS" << std::endl;
    return 0;
}
