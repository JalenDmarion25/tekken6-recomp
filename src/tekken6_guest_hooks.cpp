#include <rex/ppc/context.h>

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <thread>

// Codegen emits this declaration with a mutable reference; the hook itself
// deliberately leaves the register untouched.
void Tekken6StartupWait(PPCRegister& spin) {
  static const bool sleep = std::getenv("TEKKEN6_SLEEP_STARTUP_SPIN") != nullptr;
  static const bool yield = std::getenv("TEKKEN6_YIELD_STARTUP_SPIN") != nullptr;
  if (spin.s32 > 0) {
    if (sleep) {
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    } else if (yield) {
      std::this_thread::yield();
    }
  }
  // The guest producer writes this queue flag from another host thread. Keep
  // each iteration's load even when the optional scheduler yield is disabled.
  std::atomic_signal_fence(std::memory_order_seq_cst);
}
