/* LLVM-MinGW ships its own CRT headers and does not provide the MSVC-only
   crtversion.h expected by this FFmpeg configuration. MinGW's MSVCRT target is
   compatible with the modern CRT path, so disable FFmpeg's pre-VC14 linker
   fallback. */
#pragma once
#define _VC_CRT_MAJOR_VERSION 14
