// Host test: c++ -std=c++17 -Iinclude test/test_cutoff.cpp -o /tmp/t && /tmp/t
#include <cassert>
#include <cstdio>
#include "cutoff.h"
using namespace cutoff;

int main() {
    {   Cutoff c; bool hb = false;
        for (uint32_t t = 0; t < 10000; t += 100) { hb = !hb; assert(c.update(t, 20.0f, hb)); } }
    {   Cutoff c; assert(c.update(0, 20, false)); assert(!c.update(100, 43, true));
        assert(c.reason() == Reason::OverTemp); assert(!c.update(200, 20, false)); }  // latched
    {   Cutoff c; assert(c.update(0, 20, false)); assert(!c.update(3500, 20, false));
        assert(c.reason() == Reason::HeartbeatLost); }
    {   Cutoff c; assert(!c.update(0, -999, false)); assert(c.reason() == Reason::SensorFault); }
    {   float t = ntc_celsius(2048); assert(t > 24 && t < 26); assert(ntc_celsius(0) < -900); }
    std::puts("cutoff host tests passed");
}
