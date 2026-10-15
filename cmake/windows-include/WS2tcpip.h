// Windows headers are case-insensitive; the Linux cross-build filesystem is not.
// Keep this forwarding shim outside the project sources.
#pragma once
#include <ws2tcpip.h>
