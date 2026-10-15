// LLVM-MinGW's libc++ build does not currently expose the C++20 chrono
// clock_cast customization point. ReXGlue already carries the same fallback
// for Apple libc++; keep this compatibility layer private to the cross-build.
#pragma once

#include <chrono>

namespace std {
namespace chrono {
template <class, class>
struct clock_time_conversion {};

template <class DestClock, class SourceClock, class Duration>
auto clock_cast(const std::chrono::time_point<SourceClock, Duration>& t)
    -> decltype(clock_time_conversion<DestClock, SourceClock>{}(t)) {
  return clock_time_conversion<DestClock, SourceClock>{}(t);
}
}  // namespace chrono
}  // namespace std
