// Two practice-origin character-choice redirects before native asset requests.
#pragma once
#include <rex/runtime.h>
#include <rex/ppc/context.h>
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <mutex>

namespace quick_select_character_test_detail {
std::atomic<bool> armed{false};
std::atomic<unsigned> completed{0};
std::mutex mutex;
bool span(uint32_t a, uint32_t n) {
  return n <= 0x3E000000u && a >= 0x82000000u && a <= 0xC0000000u - n && !(a & 3);
}
uint32_t read(const uint8_t* b, uint32_t a) {
  const uint8_t* p = b + a;
  return uint32_t(p[0]) << 24 | uint32_t(p[1]) << 16 | uint32_t(p[2]) << 8 | uint32_t(p[3]);
}
void write(uint8_t* b, uint32_t a, uint32_t v) {
  for (int i = 3; i >= 0; --i) { b[a + i] = uint8_t(v); v >>= 8; }
}
constexpr uint32_t choices = 0x82744AA8u;
constexpr uint32_t invalid = 0xFFFFFFFFu;
uint32_t id(const uint8_t* b, uint32_t index) {
  return index < 102 ? read(b, choices + index * 108) : invalid;
}
uint32_t variant(const uint8_t* b, uint32_t index) {
  return index < 102 ? read(b, choices + index * 108 + 4) : invalid;
}
uint32_t find(const uint8_t* b, uint32_t character, uint32_t costume) {
  if (costume > 1) return invalid;
  for (uint32_t i = 0; i < 102; ++i)
    if (id(b, i) == character && variant(b, i) == costume) return i;
  return invalid;
}
uint32_t context(const uint8_t* b) {
  constexpr uint32_t registry = 0x82735C70u;
  const uint32_t root = read(b, registry + 16), mask = read(b, 0x82007560u);
  if (!span(root, 912) || read(b, root + 12) != read(b, registry + 20) || !(read(b, root + 60) & mask)) return 0;
  const uint32_t modes = read(b, root + 908);
  if (!span(modes, 320)) return 0;
  const uint32_t c = read(b, modes + 312);
  if (!span(c, 364) || read(b, c + 12) != read(b, modes + 316) || !(read(b, c + 60) & mask)) return 0;
  return c;
}
void log(const char* event, uint32_t object, uint32_t player, uint32_t before,
         uint32_t after, uint32_t charId, uint32_t costume, uint32_t stage) {
  std::lock_guard<std::mutex> lock(mutex);
  static unsigned count = 0;
  if (count >= 2048) return;
  static std::FILE* file = std::fopen("quick-select-character-test.txt", "w");
  if (!file) return;
  if (!count) std::fputs("QUICK SELECT CHARACTER TEST v1\n", file);
  std::fprintf(file, "%u %s object=%08X player=%u before=%u after=%u character=%u variant=%u stage=%u armed=%u completed=%u\n",
      ++count, event, object, player, before, after, charId, costume, stage,
      unsigned(armed.load()), completed.load());
  if (count == 2048) std::fputs("TRACE LIMIT REACHED\n", file);
  std::fflush(file);
}
}

void ArmQuickSelectCharacterTest(uint32_t row, uint32_t action, uint32_t owner) {
  using namespace quick_select_character_test_detail;
  if (row != 346 || action != 1 || !owner || completed.load() >= 2) return;
  if (!armed.exchange(true)) log("armed-from-practice", owner, completed.load(), 0, 0, 0, 0, invalid);
}

void ApplyQuickSelectCharacterRequest(PPCRegister& mode, PPCRegister& player, PPCRegister& selection) {
  using namespace quick_select_character_test_detail;
  auto* runtime = rex::Runtime::instance();
  uint8_t* b = runtime ? runtime->virtual_membase() : nullptr;
  if (!b) return;
  const uint32_t c = context(b);
  const uint32_t stage = c ? read(b, c + 352) : invalid;
  log("native-character-choice", mode.u32, player.u32, selection.u32, selection.u32,
      id(b, selection.u32), variant(b, selection.u32), stage);
  if (!armed.load() || completed.load() >= 2) return;
  const unsigned phase = completed.load();
  if (player.u32 != phase || !c || selection.u32 >= 102) return;
  const uint32_t p1 = read(b, c + 356), p2 = read(b, c + 360);
  const bool pair = phase == 0 ? (id(b, p1) == 6 && id(b, p2) == 9)
                               : (id(b, p1) == 40 && id(b, p2) == 9);
  if (!pair || read(b, c + 356 + phase * 4) != selection.u32) {
    log("skipped-pair-or-context", c, phase, selection.u32, selection.u32,
        id(b, selection.u32), variant(b, selection.u32), stage);
    return;
  }
  const uint32_t desired = phase == 0 ? 40u : 14u;
  const uint32_t next = find(b, desired, variant(b, selection.u32));
  if (next == invalid) {
    log("skipped-unsupported-variant", c, phase, selection.u32, selection.u32,
        desired, variant(b, selection.u32), stage);
    return;
  }
  bool expected = true;
  if (!armed.compare_exchange_strong(expected, false)) return;
  const uint32_t before = selection.u32;
  write(b, c + 356 + phase * 4, next);
  selection.u64 = next;
  completed.fetch_add(1);
  log("redirected-character-choice", c, phase, before, next, desired, variant(b, next), stage);
}

void TraceQuickSelectCharacterAsset(PPCRegister& asset, PPCRegister& character, PPCRegister& costume) {
  using namespace quick_select_character_test_detail;
  // Observe the lower asset entry without modifying its arguments.
  log("asset-request", asset.u32, invalid, invalid, invalid, character.u32, costume.u32, invalid);
}
