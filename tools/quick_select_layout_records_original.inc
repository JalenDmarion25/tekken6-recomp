// Native menu-layout prototype. Loading/applying these selections is not wired.
#pragma once
#include <cstdint>
#include <cstring>

namespace quick_select_menu_detail {
constexpr uint32_t quickRow = 502;
constexpr uint32_t playerRow = 503;
constexpr uint32_t opponentRow = 508;
constexpr uint32_t stageRow = 513;
constexpr uint32_t totalCount = 516;
constexpr uint32_t recordSize = 96;
constexpr uint32_t textSize = 40;
uint32_t read(const uint8_t* base, uint32_t a) {
  const uint8_t* p = base + a;
  return uint32_t(p[0]) << 24 | uint32_t(p[1]) << 16 |
         uint32_t(p[2]) << 8 | uint32_t(p[3]);
}
void write(uint8_t* base, uint32_t a, uint32_t value) {
  for (int i = 3; i >= 0; --i) { base[a + i] = uint8_t(value); value >>= 8; }
}
}

void InstallPracticeQuickSelectRecords(uint8_t* base, uint32_t records,
                                       uint32_t texts, uint32_t& strings) {
  using namespace quick_select_menu_detail;
  auto text = [&](const char* value) {
    const uint32_t address = strings;
    const size_t size = std::strlen(value) + 1;
    std::memcpy(base + strings, value, size);
    strings += static_cast<uint32_t>(size);
    return address;
  };
  const uint32_t minusOne = text("-1");
  auto node = [&](uint32_t id, uint32_t source, const char* label,
                  uint32_t parent, uint32_t children, uint32_t first,
                  uint32_t previous, uint32_t next) {
    const uint32_t record = records + id * recordSize;
    const uint32_t entry = texts + id * textSize;
    std::memcpy(base + record, base + records + source * recordSize, recordSize);
    std::memcpy(base + entry, base + texts + source * textSize, textSize);
    std::memset(base + record + 48, 0, recordSize - 48);
    write(base, record, id);
    write(base, record + 4, parent);
    write(base, record + 8, children);
    write(base, record + 16, first);
    write(base, record + 20, previous);
    write(base, record + 24, next);
    write(base, record + 28, id * 10);
    write(base, entry, text(label));
    for (uint32_t field = 1; field <= 4; ++field)
      write(base, entry + field * 4, minusOne);
  };
  // Clone Mode Select's submenu role, with a separate parent and child list.
  node(quickRow, 297, "Quick Select", 297, 3, playerRow, 299, 0);
  node(playerRow, 323, "Player", quickRow, 4, 504, 0, opponentRow);
  node(opponentRow, 323, "Opponent", quickRow, 4, 509, playerRow, stageRow);
  node(stageRow, 323, "Stage", quickRow, 2, 514, opponentRow, 0);
  const char* characters[] = {"Hwoarang", "Lars Alexanderson", "Jin Kazama", "Kazuya Mishima"};
  for (uint32_t i = 0; i < 4; ++i) {
    node(504 + i, 324, characters[i], playerRow, 0, 0,
         i ? 503 + i : 0, i < 3 ? 505 + i : 0);
    node(509 + i, 324, characters[i], opponentRow, 0, 0,
         i ? 508 + i : 0, i < 3 ? 510 + i : 0);
  }
  node(514, 324, "Noh Theater", stageRow, 0, 0, 0, 515);
  node(515, 324, "Fallen Colony", stageRow, 0, 0, 514, 0);
  // Layout defaults only. No claim that these are the active match selections.
  write(base, records + opponentRow * recordSize + 80, 2);
  write(base, records + 297 * recordSize + 8, 3);
  write(base, records + 299 * recordSize + 24, quickRow);
}
