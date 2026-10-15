#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <dbghelp.h>

#include <atomic>
#include <cstdarg>
#include <cstdio>
#include <cwchar>

#include <rex/ppc/context.h>
#include <rex/system/thread_state.h>

namespace {
wchar_t crash_directory[32768]{};
std::atomic_flag reporting = ATOMIC_FLAG_INIT;

void WriteLine(HANDLE file, const char* format, ...) {
  char buffer[2048];
  va_list args;
  va_start(args, format);
  const int count = vsnprintf(buffer, sizeof(buffer), format, args);
  va_end(args);
  if (count > 0) {
    DWORD written;
    WriteFile(file, buffer, DWORD(count < int(sizeof(buffer)) ? count : sizeof(buffer) - 1),
              &written, nullptr);
  }
}

void WriteAddress(HANDLE file, unsigned frame, DWORD64 address) {
  MEMORY_BASIC_INFORMATION region{};
  if (VirtualQuery(reinterpret_cast<void*>(address), &region, sizeof(region))) {
    wchar_t module[MAX_PATH]{};
    GetModuleFileNameW(static_cast<HMODULE>(region.AllocationBase), module, MAX_PATH);
    const wchar_t* name = wcsrchr(module, L'\\');
    WriteLine(file, "frame %u: %016llX module=%ls base=%016llX RVA=%llX\r\n",
              frame, address, name ? name + 1 : module,
              reinterpret_cast<unsigned long long>(region.AllocationBase),
              address - reinterpret_cast<unsigned long long>(region.AllocationBase));
  } else {
    WriteLine(file, "frame %u: %016llX module=unknown\r\n", frame, address);
  }
}

const char* ExceptionName(DWORD code) {
  switch (code) {
    case EXCEPTION_ACCESS_VIOLATION: return "ACCESS_VIOLATION";
    case EXCEPTION_ILLEGAL_INSTRUCTION: return "ILLEGAL_INSTRUCTION";
    case EXCEPTION_INT_DIVIDE_BY_ZERO: return "INTEGER_DIVIDE_BY_ZERO";
    case EXCEPTION_STACK_OVERFLOW: return "STACK_OVERFLOW";
    case EXCEPTION_BREAKPOINT: return "BREAKPOINT";
    case EXCEPTION_IN_PAGE_ERROR: return "IN_PAGE_ERROR";
    case EXCEPTION_ARRAY_BOUNDS_EXCEEDED: return "ARRAY_BOUNDS_EXCEEDED";
    case EXCEPTION_DATATYPE_MISALIGNMENT: return "DATATYPE_MISALIGNMENT";
    default: return "OTHER";
  }
}

void WriteInstructionBytes(HANDLE file, const char* label, DWORD64 address) {
  uint8_t bytes[16]{};
  SIZE_T read = 0;
  if (!ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<const void*>(address),
                         bytes, sizeof(bytes), &read) || !read) {
    WriteLine(file, "%s=unreadable at %016llX\r\n", label, address);
    return;
  }
  char text[sizeof(bytes) * 3 + 1]{};
  size_t used = 0;
  for (SIZE_T i = 0; i < read && used + 4 < sizeof(text); ++i) {
    const int count = snprintf(text + used, sizeof(text) - used, "%s%02X",
                               i ? " " : "", bytes[i]);
    if (count <= 0) break;
    used += size_t(count);
  }
  WriteLine(file, "%s=%s\r\n", label, text);
}

LONG WINAPI ReportCrash(EXCEPTION_POINTERS* pointers) {
  if (!pointers || reporting.test_and_set()) return EXCEPTION_CONTINUE_SEARCH;
  wchar_t path[32768];
  swprintf(path, 32768, L"%ls\\crash.txt", crash_directory);
  HANDLE file = CreateFileW(path, GENERIC_WRITE, FILE_SHARE_READ, nullptr,
                            CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
  if (file != INVALID_HANDLE_VALUE) {
    const auto& host = *pointers->ContextRecord;
    const auto* record = pointers->ExceptionRecord;
    const DWORD64 exception_address = reinterpret_cast<DWORD64>(record->ExceptionAddress);
    WriteLine(file, "Tekken 6 unhandled Windows exception\r\n"
                    "exception_name=%s code=%08lX flags=%08lX thread=%lu\r\n"
                    "exception_address=%016llX host_RIP=%016llX host_RSP=%016llX\r\n",
              ExceptionName(record->ExceptionCode), record->ExceptionCode,
              record->ExceptionFlags, GetCurrentThreadId(), exception_address,
              host.Rip, host.Rsp);
    WriteAddress(file, 0, exception_address);
    if (record->ExceptionCode == EXCEPTION_ACCESS_VIOLATION && record->NumberParameters >= 2) {
      const char* access = record->ExceptionInformation[0] == 0 ? "read" :
                           record->ExceptionInformation[0] == 1 ? "write" :
                           record->ExceptionInformation[0] == 8 ? "execute" : "unknown";
      WriteLine(file, "access_type=%s access_address=%016llX\r\n", access,
                record->ExceptionInformation[1]);
    }
    if (record->ExceptionCode == EXCEPTION_ILLEGAL_INSTRUCTION) {
      WriteInstructionBytes(file, "illegal_instruction_bytes", exception_address);
    } else if (record->ExceptionCode == EXCEPTION_ACCESS_VIOLATION) {
      WriteInstructionBytes(file, "faulting_instruction_bytes", host.Rip);
    }
    for (DWORD i = 0; i < record->NumberParameters; ++i) {
      WriteLine(file, "exception_parameter[%lu]=%016llX\r\n", i,
                record->ExceptionInformation[i]);
    }
    const DWORD64 registers[] = {host.Rax, host.Rcx, host.Rdx, host.Rbx, host.Rsp, host.Rbp,
                                host.Rsi, host.Rdi, host.R8, host.R9, host.R10, host.R11,
                                host.R12, host.R13, host.R14, host.R15};
    for (unsigned i = 0; i < 16; ++i) WriteLine(file, "host_reg[%u]=%016llX\r\n", i, registers[i]);
    if (auto* thread = rex::runtime::ThreadState::Get()) {
      const auto* ctx = thread->context();
      WriteLine(file,
                "guest_thread=%08X lr=%016llX ctr=%016llX last_indirect=%08X "
                "last_indirect_lr=%08X\r\n",
                thread->thread_id(), ctx->lr, ctx->ctr.u64, ctx->last_indirect_target,
                ctx->last_indirect_lr);
      // PPCContext stores r3 first, so do not walk it as a contiguous r0..r31 array.
      const PPCRegister* gprs[] = {&ctx->r0, &ctx->r1, &ctx->r2, &ctx->r3, &ctx->r4,
          &ctx->r5, &ctx->r6, &ctx->r7, &ctx->r8, &ctx->r9, &ctx->r10, &ctx->r11,
          &ctx->r12, &ctx->r13, &ctx->r14, &ctx->r15, &ctx->r16, &ctx->r17,
          &ctx->r18, &ctx->r19, &ctx->r20, &ctx->r21, &ctx->r22, &ctx->r23,
          &ctx->r24, &ctx->r25, &ctx->r26, &ctx->r27, &ctx->r28, &ctx->r29,
          &ctx->r30, &ctx->r31};
      for (unsigned i = 0; i < 32; ++i) WriteLine(file, "r%u=%016llX\r\n", i, gprs[i]->u64);
    } else {
      WriteLine(file, "No guest context on the faulting host thread.\r\n");
    }
    // Walk from the actual fault context, without needing symbols or PDB files.
    CONTEXT walk = host;
    for (unsigned i = 0; i < 64 && walk.Rip; ++i) {
      WriteAddress(file, i, walk.Rip);
      DWORD64 image_base = 0;
      auto* entry = RtlLookupFunctionEntry(walk.Rip, &image_base, nullptr);
      const DWORD64 previous_rsp = walk.Rsp;
      if (entry) {
        PVOID handler_data = nullptr;
        DWORD64 establisher_frame = 0;
        RtlVirtualUnwind(UNW_FLAG_NHANDLER, image_base, walk.Rip, entry, &walk,
                         &handler_data, &establisher_frame, nullptr);
      } else {
        SIZE_T read = 0;
        if (!ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<void*>(walk.Rsp),
                               &walk.Rip, sizeof(walk.Rip), &read) || read != sizeof(walk.Rip)) break;
        walk.Rsp += sizeof(DWORD64);
      }
      if (walk.Rsp <= previous_rsp) break;
    }
    FlushFileBuffers(file);
    CloseHandle(file);
  }
  swprintf(path, 32768, L"%ls\\crash.dmp", crash_directory);
  HANDLE dump = CreateFileW(path, GENERIC_WRITE, FILE_SHARE_READ, nullptr,
                            CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
  if (dump != INVALID_HANDLE_VALUE) {
    MINIDUMP_EXCEPTION_INFORMATION exception{GetCurrentThreadId(), pointers, FALSE};
    // Keep the dump small; never dump the full 4 GB guest arena.
    MiniDumpWriteDump(GetCurrentProcess(), GetCurrentProcessId(), dump,
        MINIDUMP_TYPE(MiniDumpNormal | MiniDumpWithThreadInfo), &exception, nullptr, nullptr);
    CloseHandle(dump);
  }
  return EXCEPTION_EXECUTE_HANDLER;
}
}  // namespace

void InstallTekken6CrashReport() {
  const DWORD length = GetEnvironmentVariableW(L"TEKKEN6_CRASH_DIR", crash_directory, 32768);
  if (length && length < 32768) SetUnhandledExceptionFilter(ReportCrash);
}
