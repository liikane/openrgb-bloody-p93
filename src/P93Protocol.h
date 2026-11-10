#pragma once
#include <array>
#include <cstdint>
#include <cstddef>

namespace P93Protocol
{
constexpr std::size_t SlotCount = 15;
using Report = std::array<std::uint8_t, 64>;
using Color = std::array<std::uint8_t, 3>;
using Slots = std::array<Color, SlotCount>;

inline Report RgbMode()
{
    Report report{};
    report[0] = 7; report[1] = 3; report[2] = 6; report[3] = 1;
    return report;
}

inline Report DirectInit()
{
    Report report{};
    report[0] = 7; report[1] = 3; report[2] = 6; report[3] = 0;
    report[8] = 1;
    return report;
}

inline Report ColorSlots(const Slots& slot_colors)
{
    Report report{};
    report[0] = 7; report[1] = 3; report[2] = 6; report[3] = 2;
    for(std::size_t i = 0; i < SlotCount; ++i)
    {
        report[8 + 3*i] = slot_colors[i][0];
        report[9 + 3*i] = slot_colors[i][1];
        report[10 + 3*i] = slot_colors[i][2];
    }
    return report;
}

inline Report StaticColor(std::uint8_t red, std::uint8_t green, std::uint8_t blue)
{
    Slots slot_colors{};
    slot_colors.fill({red,green,blue});
    return ColorSlots(slot_colors);
}

// A first hypothesis, not a verified physical left/right map.
// Users should identify the physical meaning of every slot.
inline Slots SplitBeacon(bool firstGroupLit, Color activeColor = {255, 210, 0})
{
    Slots slot_colors{};
    for(std::size_t i = 0; i < SlotCount; ++i)
    {
        const bool firstGroup = i < 7;
        if(firstGroup == firstGroupLit)
            slot_colors[i] = activeColor;
    }
    return slot_colors;
}
}
