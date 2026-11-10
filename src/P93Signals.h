#pragma once

#include "P93Protocol.h"
#include <algorithm>
#include <string_view>
#include <vector>

namespace P93Signals
{
enum class Event { Alert, Error, Success, Notice };

inline std::string_view Name(Event event)
{
    switch(event)
    {
        case Event::Alert:   return "ALERT";
        case Event::Error:   return "ERROR";
        case Event::Success: return "SUCCESS";
        case Event::Notice:  return "NOTICE";
    }
    return "NOTICE";
}

inline bool FromName(std::string_view s, Event& event)
{
    if(s == "ALERT")   { event = Event::Alert; return true; }
    if(s == "ERROR")   { event = Event::Error; return true; }
    if(s == "SUCCESS") { event = Event::Success; return true; }
    if(s == "NOTICE")  { event = Event::Notice; return true; }
    return false;
}

struct Palette
{
    P93Protocol::Color a;
    P93Protocol::Color b;
};

inline Palette Colors(Event event)
{
    // Bright enough for the P93 case lights, slower than a rapid-strobe effect.
    switch(event)
    {
        case Event::Error:   return {{210, 15, 20}, {245, 170, 0}};  // Red / yellow
        case Event::Alert:   return {{205, 15, 25}, {30, 95, 245}}; // Red / blue
        case Event::Success: return {{20, 200, 75}, {170, 170, 170}}; // Green / white
        case Event::Notice:  return {{30, 180, 60}, {235, 175, 0}}; // Green / yellow
    }
    return {{30, 180, 60}, {235, 175, 0}};
}

inline P93Protocol::Slots Frame(Event event, bool phaseB,
                                const std::vector<std::size_t>& groupA,
                                const std::vector<std::size_t>& groupB)
{
    P93Protocol::Slots frame{};
    const auto colors = Colors(event);
    for(std::size_t index : phaseB ? groupB : groupA)
    {
        if(index < P93Protocol::PhysicalLedCount)
            frame[index] = phaseB ? colors.b : colors.a;
    }
    return frame;
}

inline P93Protocol::Slots IdleRainbow(std::size_t step)
{
    // Rotate a static eight-color palette around all eight LEDs.
    // No all-black frame; colors are distinct but intentionally dimmed.
    constexpr std::array<P93Protocol::Color, P93Protocol::PhysicalLedCount> colors{{
        {{155, 24, 145}}, {{155, 30, 50}}, {{165, 80, 20}}, {{170, 135, 25}},
        {{35, 145, 65}}, {{30, 140, 155}}, {{35, 75, 170}}, {{90, 35, 165}}
    }};
    P93Protocol::Slots frame{};
    for(std::size_t i=0; i<P93Protocol::PhysicalLedCount; ++i)
        frame[i] = colors[(i + step) % P93Protocol::PhysicalLedCount];
    return frame;
}

// Two complete A/B cycles per notification before showing the next category.
inline std::size_t CurrentNotificationIndex(std::size_t frameTick, std::size_t count)
{
    return count == 0 ? 0 : (frameTick / 4) % count;
}
}
