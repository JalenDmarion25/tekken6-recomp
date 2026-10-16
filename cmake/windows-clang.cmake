# Cross-build with an extracted LLVM-MinGW distribution (MSVCRT or UCRT).
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR x86_64)
set(LLVM_MINGW_ROOT "$ENV{LLVM_MINGW_ROOT}" CACHE PATH "LLVM-MinGW installation")
list(APPEND CMAKE_TRY_COMPILE_PLATFORM_VARIABLES LLVM_MINGW_ROOT)
if(CMAKE_HOST_WIN32)
    set(LLVM_MINGW_EXECUTABLE_SUFFIX ".exe")
else()
    set(LLVM_MINGW_EXECUTABLE_SUFFIX "")
endif()
if(NOT EXISTS "${LLVM_MINGW_ROOT}/bin/x86_64-w64-mingw32-clang++${LLVM_MINGW_EXECUTABLE_SUFFIX}")
    message(FATAL_ERROR "Set LLVM_MINGW_ROOT to an extracted LLVM-MinGW distribution")
endif()
set(CMAKE_C_COMPILER "${LLVM_MINGW_ROOT}/bin/x86_64-w64-mingw32-clang${LLVM_MINGW_EXECUTABLE_SUFFIX}")
set(CMAKE_CXX_COMPILER "${LLVM_MINGW_ROOT}/bin/x86_64-w64-mingw32-clang++${LLVM_MINGW_EXECUTABLE_SUFFIX}")
set(CMAKE_RC_COMPILER "${LLVM_MINGW_ROOT}/bin/x86_64-w64-mingw32-windres${LLVM_MINGW_EXECUTABLE_SUFFIX}")
set(CMAKE_AR "${LLVM_MINGW_ROOT}/bin/x86_64-w64-mingw32-llvm-ar${LLVM_MINGW_EXECUTABLE_SUFFIX}")
set(CMAKE_RANLIB "${LLVM_MINGW_ROOT}/bin/x86_64-w64-mingw32-llvm-ranlib${LLVM_MINGW_EXECUTABLE_SUFFIX}")
set(CMAKE_FIND_ROOT_PATH
    "${LLVM_MINGW_ROOT}"
    "${LLVM_MINGW_ROOT}/x86_64-w64-mingw32")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
set(CMAKE_C_FLAGS_INIT "-DWINVER=0x0602 -D_WIN32_WINNT=0x0602")
if(NOT CMAKE_HOST_WIN32)
    # Linux filesystems are case-sensitive; these wrappers bridge Windows
    # header spellings. On Windows they shadow the real headers by case.
    string(APPEND CMAKE_C_FLAGS_INIT
        " -isystem \"${CMAKE_CURRENT_LIST_DIR}/windows-include\"")
endif()
string(APPEND CMAKE_C_FLAGS_INIT
    " -isystem \"${CMAKE_CURRENT_LIST_DIR}/mingw-include\"")
set(CMAKE_CXX_FLAGS_INIT "${CMAKE_C_FLAGS_INIT} -mssse3 -fms-extensions -include \"${CMAKE_CURRENT_LIST_DIR}/windows-include/chrono_compat.hpp\"")
