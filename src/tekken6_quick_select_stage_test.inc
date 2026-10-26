// Experimental one-time redirect at the shared native stage-request entry.
#pragma once
#include <rex/runtime.h>
#include <rex/ppc/context.h>
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <mutex>

namespace quick_select_stage_test_detail {
std::atomic<bool> armed{false};
std::atomic<bool> consumed{false};
std::mutex mutex;
bool span(uint32_t a, uint32_t size) {
  return size <= 0x3E000000u && a >= 0x82000000u &&
         a <= 0xC0000000u - size && !(a & 3);
}
uint32_t read(const uint8_t* base, uint32_t a) {
  const uint8_t* p = base + a;
  return uint32_t(p[0]) << 24 | uint32_t(p[1]) << 16 |
         uint32_t(p[2]) << 8 | uint32_t(p[3]);
}
void log(const char* event, uint32_t manager, uint32_t context,
         uint32_t request, uint32_t stored, uint32_t result) {
  std::lock_guard<std::mutex> lock(mutex);
  static unsigned events = 0;
  if (events >= 512) return;
  static std::FILE* file = std::fopen("quick-select-stage-test.txt", "w");
  if (!file) return;
  if (!events) std::fputs("QUICK SELECT STAGE TEST v2\n", file);
  std::fprintf(file, "%u %s manager=%08X context=%08X request=%u stored=%u result=%u armed=%u consumed=%u\n",
      ++events, event, manager, context, request, stored, result,
      unsigned(armed.load()), unsigned(consumed.load()));
  std::fflush(file);
}
uint32_t activeContext(const uint8_t* base) {
  constexpr uint32_t registry = 0x82735C70u;
  const uint32_t root = read(base, registry + 16);
  if (!span(root, 912) || read(base, root + 12) != read(base, registry + 20)) return 0;
  const uint32_t mask = read(base, 0x82007560u);
  if (!(read(base, root + 60) & mask)) return 0;
  const uint32_t modes = read(base, root + 908);
  if (!span(modes, 320)) return 0;
  const uint32_t context = read(base, modes + 312);
  if (!span(context, 356) || read(base, context + 12) != read(base, modes + 316) ||
      !(read(base, context + 60) & mask)) return 0;
  return context;
}
}

void ArmQuickSelectStageTest(uint32_t row, uint32_t action, uint32_t practiceOwner) {
  using namespace quick_select_stage_test_detail;
  if (row != 346 || action != 1 || !practiceOwner || consumed.load()) return;
  if (!armed.exchange(true))
    log("armed-from-practice-character-select", 0, practiceOwner, 8, 8, 9);
}

void ApplyQuickSelectStageRequest(PPCRegister& manager, PPCRegister& selectedStage) {
  using namespace quick_select_stage_test_detail;
  auto* runtime = rex::Runtime::instance();
  uint8_t* base = runtime ? runtime->virtual_membase() : nullptr;
  if (!base) {
    log("request-without-runtime-memory", manager.u32, 0, selectedStage.u32, 0xFFFFFFFFu, selectedStage.u32);
    return;
  }
  const uint32_t context = activeContext(base);
  const uint32_t stored = context ? read(base, context + 352) : 0xFFFFFFFFu;
  log("shared-stage-request", manager.u32, context, selectedStage.u32, stored, selectedStage.u32);
  if (!armed.load() || consumed.load()) return;
  // Ignore intermediate/sentinel requests without discarding the armed test.
  if (!context || !span(manager.u32, 280) || selectedStage.u32 != 8 || stored != 8) {
    log("skipped-context-or-selection", manager.u32, context, selectedStage.u32, stored, selectedStage.u32);
    return;
  }
  if (consumed.exchange(true)) return;
  uint8_t* p = base + context + 352;
  p[0] = 0; p[1] = 0; p[2] = 0; p[3] = 9;
  selectedStage.u64 = 9;
  armed.store(false);
  log("redirected-native-stage-request", manager.u32, context, 8, stored, 9);
}
