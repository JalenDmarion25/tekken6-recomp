#include <rex/ppc/context.h>

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <thread>
#include <cstdio>
#include <cstdint>
#include <map>
#include <mutex>

thread_local bool redirectPracticePlacement = false;
thread_local bool rightSideCameraRequested = false;
thread_local bool insidePracticeCameraReset = false;
thread_local unsigned cameraUpdatesToTrace = 0;
thread_local std::map<uint32_t, uint32_t> practiceCameraChoices;

// Codegen emits this declaration with a mutable reference; the hook itself
// deliberately leaves the register untouched.
void Tekken6StartupWait(PPCRegister &spin)
{
  static const bool sleep = std::getenv("TEKKEN6_SLEEP_STARTUP_SPIN") != nullptr;
  static const bool yield = std::getenv("TEKKEN6_YIELD_STARTUP_SPIN") != nullptr;
  if (spin.s32 > 0)
  {
    if (sleep)
    {
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    else if (yield)
    {
      std::this_thread::yield();
    }
  }
  // The guest producer writes this queue flag from another host thread. Keep
  // each iteration's load even when the optional scheduler yield is disabled.
  std::atomic_signal_fence(std::memory_order_seq_cst);
}

void TraceTekkenButtons(PPCRegister &object, PPCRegister &buttons)
{
  static const char *path = std::getenv("TEKKEN6_INPUT_TRACE");
  if (!path || !*path)
    return;

  static std::mutex mutex;
  std::lock_guard<std::mutex> lock(mutex);

  static std::FILE *log = std::fopen(path, "w");
  if (!log)
    return;

  static std::map<uint32_t, uint32_t> previous;
  const uint32_t address = object.u32;
  const uint32_t current = buttons.u32;

  auto entry = previous.emplace(address, current);
  if (!entry.second && entry.first->second == current)
    return;

  std::fprintf(log, "object=%08X held=%08X pressed=%08X released=%08X\n",
               static_cast<unsigned>(address),
               static_cast<unsigned>(current),
               static_cast<unsigned>(current & ~entry.first->second),
               static_cast<unsigned>(entry.first->second & ~current));
  entry.first->second = current;
  std::fflush(log);
}

void TraceTekkenStateCommand(PPCRegister &caller, PPCRegister &command)
{
  static const char *path = std::getenv("TEKKEN6_RESET_TRACE");
  if (!path || !*path)
    return;

  static std::mutex mutex;
  std::lock_guard<std::mutex> lock(mutex);
  static std::FILE *log = std::fopen(path, "w");
  if (!log)
    return;

  std::fprintf(log, "caller=%08X command=%u\n",
               static_cast<unsigned>(caller.u32),
               static_cast<unsigned>(command.u32));
  std::fflush(log);
}

namespace
{
  std::atomic<uint32_t> practiceHeld{0};
  std::atomic<bool> pendingRightSideReset{false};

  thread_local bool applyRightSideReset = false;
  thread_local uint32_t practicePlayerOne = 0;
}

void LogPracticeSide(
    const char *stage, uint32_t first, uint32_t second)
{
  static std::mutex mutex;
  std::lock_guard<std::mutex> lock(mutex);
  static std::FILE *log = std::fopen("reset-side-debug.txt", "w");
  if (!log)
    return;

  std::fprintf(log,
               "%s first=%08X second=%08X p1=%08X apply=%u redirect=%u\n",
               stage,
               static_cast<unsigned>(first),
               static_cast<unsigned>(second),
               static_cast<unsigned>(practicePlayerOne),
               static_cast<unsigned>(applyRightSideReset),
               static_cast<unsigned>(redirectPracticePlacement));
  std::fflush(log);
}

void CapturePracticeHeld(PPCRegister &held)
{
  practiceHeld.store(held.u32, std::memory_order_relaxed);
}

void CapturePracticeResetPress(PPCRegister &pressed)
{
  constexpr uint32_t down = 0x00000002;
  constexpr uint32_t resetModifier = 0x00000020;
  constexpr uint32_t resetButton = 0x00001000;

  const uint32_t held =
      practiceHeld.load(std::memory_order_relaxed);

  if ((held & resetModifier) && (pressed.u32 & resetButton))
  {
    // Latch the direction now so releasing during the reset delay is OK.
    pendingRightSideReset.store(
        (held & down) != 0, std::memory_order_relaxed);
  }
}

void RememberPracticePlayerOne(PPCRegister &playerOne)
{
  practicePlayerOne = playerOne.u32;
}

void BeginPracticeSideReset(PPCRegister &command)
{
  applyRightSideReset =
      pendingRightSideReset.exchange(false, std::memory_order_relaxed) && command.u32 == 13;

  practicePlayerOne = 0;
  redirectPracticePlacement = false;
  LogPracticeSide("begin", command.u32, 0);

  rightSideCameraRequested = false;
  insidePracticeCameraReset = false;
  practiceCameraChoices.clear();
}

void ApplyPracticeResetSide(
    PPCRegister &first, PPCRegister &second, PPCRegister &command)
{
  redirectPracticePlacement = false;

  if (command.u32 != 13 || !applyRightSideReset)
    return;
  applyRightSideReset = false;

  if (!practicePlayerOne || !first.u32 || !second.u32 || first.u32 == second.u32)
  {
    return;
  }

  // Leave the references unchanged during placement calculations.
  redirectPracticePlacement = first.u32 == practicePlayerOne;
  rightSideCameraRequested = redirectPracticePlacement;
}

void RedirectPracticeFirstPlacement(
    PPCRegister &target, PPCRegister &other)
{
  LogPracticeSide("first-before", target.u32, other.u32);

  if (redirectPracticePlacement)
  {
    target = other;
  }

  LogPracticeSide("first-after", target.u32, other.u32);
}

void RedirectPracticeSecondPlacement(
    PPCRegister &target, PPCRegister &other)
{
  LogPracticeSide("second-before", target.u32, other.u32);

  if (redirectPracticePlacement)
  {
    target = other;
  }

  LogPracticeSide("second-after", target.u32, other.u32);
  redirectPracticePlacement = false;
}

void BeginPracticeCameraReset(PPCRegister &command)
{
  if (command.u32 != 13)
  {
    practiceCameraChoices.clear();
  }

  insidePracticeCameraReset =
      command.u32 == 13 && rightSideCameraRequested;

  cameraUpdatesToTrace = insidePracticeCameraReset ? 24u : 0u;

  LogPracticeSide("camera-begin", command.u32,
                  insidePracticeCameraReset ? 1u : 0u);
}

void SelectPracticeResetCamera(
    PPCRegister &selection, PPCRegister &cameraOutput)
{
  const uint32_t original = selection.u32;
  const uint32_t camera = cameraOutput.u32;

  if (insidePracticeCameraReset && original <= 1)
  {
    // Remember the opposite choice for this reset's camera objects.
    const uint32_t desired = original ^ 1u;
    practiceCameraChoices[camera] = desired;
    selection.u64 = desired;
  }
  else if (original <= 1)
  {
    // Later explicit selections must retain the requested reset side.
    const auto entry = practiceCameraChoices.find(camera);
    if (entry != practiceCameraChoices.end())
    {
      selection.u64 = entry->second;
    }
  }

  // Mode 2 remains automatic, allowing normal camera side transitions.
  if (cameraUpdatesToTrace)
  {
    LogPracticeSide(
        insidePracticeCameraReset
            ? "camera-reset-choice"
            : "camera-followup-choice",
        original, selection.u32);
    --cameraUpdatesToTrace;
  }
}

void EndPracticeCameraReset(PPCRegister &command)
{
  LogPracticeSide("camera-end", command.u32, 0);
  insidePracticeCameraReset = false;
  rightSideCameraRequested = false;
}