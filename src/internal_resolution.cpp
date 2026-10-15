#include <cstdint>
#include <cstdlib>
#include <cstring>

#include <rex/ppc/context.h>

namespace {

struct InternalResolution {
  uint32_t width;
  uint32_t height;
};

InternalResolution GetSelectedResolution() {
  const char* value = std::getenv("TEKKEN6_INTERNAL_RESOLUTION");
  if (value == nullptr) {
    return {1024, 576};
  }
  if (std::strcmp(value, "640x360") == 0) {
    return {640, 360};
  }
  if (std::strcmp(value, "768x432") == 0) {
    return {768, 432};
  }
  return {1024, 576};
}

}  // namespace

// Invoked by generated mid-assembly hooks immediately before the guest stores
// its internal render dimensions. Unrecognized or absent values keep the
// retail 1024x576 mode.
void ApplyTekkenInternalResolution(PPCRegister& width, PPCRegister& height) {
  static const InternalResolution resolution = GetSelectedResolution();
  width.u32 = resolution.width;
  height.u32 = resolution.height;
}
