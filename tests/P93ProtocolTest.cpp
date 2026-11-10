#include "../src/P93Protocol.h"
#include "../src/P93Signals.h"
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
    // Persistent signals: different categories have distinct A/B colors.
    const std::vector<std::size_t> groupA{0,3};
    const std::vector<std::size_t> groupB{1,2,4,5,6,7};
    const auto errorA = P93Signals::Frame(P93Signals::Event::Error, false, groupA, groupB);
    const auto errorB = P93Signals::Frame(P93Signals::Event::Error, true, groupA, groupB);
    const auto alertA = P93Signals::Frame(P93Signals::Event::Alert, false, groupA, groupB);
    const auto alertB = P93Signals::Frame(P93Signals::Event::Alert, true, groupA, groupB);
    const auto successA = P93Signals::Frame(P93Signals::Event::Success, false, groupA, groupB);
    const auto noticeB = P93Signals::Frame(P93Signals::Event::Notice, true, groupA, groupB);

    assert(errorA[0] == (Color{210,15,20}));
    assert(errorA[3] == (Color{210,15,20}));
    assert(errorA[1] == (Color{0,0,0}));
    assert(errorB[1] == (Color{245,170,0})); // Red/yellow
    assert(alertA[0] == (Color{205,15,25}));
    assert(alertB[1] == (Color{30,95,245})); // Red/blue
    assert(successA[3] == (Color{20,200,75})); // Green/white
    assert(noticeB[7] == (Color{235,175,0})); // Green/yellow
    for(const auto& frame : {errorA, errorB, alertA, alertB, successA, noticeB})
        for(std::size_t i=PhysicalLedCount; i<SlotCount; ++i)
            assert(frame[i] == (Color{0,0,0}));
    assert(P93Signals::CurrentNotificationIndex(0,2) == 0);
    assert(P93Signals::CurrentNotificationIndex(3,2) == 0);
    assert(P93Signals::CurrentNotificationIndex(4,2) == 1);
    assert(P93Signals::CurrentNotificationIndex(8,2) == 0);
    P93Signals::Event kind{};
    assert(P93Signals::FromName("ERROR",kind) && kind == P93Signals::Event::Error);
    assert(P93Signals::FromName("SUCCESS",kind) && kind == P93Signals::Event::Success);
    assert(!P93Signals::FromName("UNSUPPORTED",kind));

    // Idle animation: no all-black frame, eight nonblack positions, full 8-step rotation.
    for(std::size_t step=0; step<16; ++step)
    {
        const auto idle = P93Signals::IdleRainbow(step);
        std::size_t active=0;
        for(std::size_t i=0;i<PhysicalLedCount;++i)
            if(idle[i][0] || idle[i][1] || idle[i][2])
                ++active;
        assert(active == 8);
        for(std::size_t i=PhysicalLedCount;i<SlotCount;++i)
            assert(idle[i] == (Color{0,0,0}));
        assert(idle[0] == P93Signals::IdleRainbow(step+8)[0]);
    }

    std::cout << "P93 persistent alert palettes, queued cycles and idle rainbow: PASS" << std::endl;
    std::cout << "P93 eight physical LEDs, customizable beacon colors: PASS" << std::endl;
    return 0;
}
