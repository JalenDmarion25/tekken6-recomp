// Portable Windows launcher. The ReXGlue host and plugins live in bin/.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <commctrl.h>

#include <string>
#include <vector>

static int Fail(const std::wstring& message, DWORD error = GetLastError()) {
  const auto text = message + L"\n\nWindows error: " + std::to_wstring(error);
  MessageBoxW(nullptr, text.c_str(), L"Tekken 6", MB_OK | MB_ICONERROR);
  return 1;
}

static bool Directory(const std::wstring& path) {
  return CreateDirectoryW(path.c_str(), nullptr) || GetLastError() == ERROR_ALREADY_EXISTS;
}

static bool ChooseRenderingOptions(const wchar_t*& resolution,
                                   const wchar_t*& offscreen_resolution) {
  enum : int { k640x360 = 101, k768x432 = 102, k1024x576 = 103 };
  const TASKDIALOG_BUTTON choices[] = {
      {k640x360, L"640 × 360  (lightest GPU workload)"},
      {k768x432, L"768 × 432  (medium GPU workload)"},
      {k1024x576, L"1024 × 576  (heaviest GPU workload; original)"},
  };

  TASKDIALOGCONFIG dialog{};
  dialog.cbSize = sizeof(dialog);
  dialog.dwFlags = TDF_ALLOW_DIALOG_CANCELLATION | TDF_SIZE_TO_CONTENT |
                   TDF_VERIFICATION_FLAG_CHECKED;
  dialog.dwCommonButtons = TDCBF_OK_BUTTON | TDCBF_CANCEL_BUTTON;
  dialog.pszWindowTitle = L"Tekken 6";
  dialog.pszMainInstruction = L"Choose the internal 3D resolution";
  dialog.pszContent =
      L"Select a rendering workload. The game window keeps its normal size. "
      L"You can change this choice each time you launch.";
  dialog.cRadioButtons = ARRAYSIZE(choices);
  dialog.pRadioButtons = choices;
  dialog.nDefaultRadioButton = k640x360;
  dialog.pszFooter = L"Lower resolution reduces the number of 3D pixels rendered.";
  dialog.pszVerificationText =
      L"Reduce the 1024 × 1024 offscreen target to 512 × 512 (lighter GPU workload; may soften shadows)";

  int button = IDCANCEL;
  int choice = k640x360;
  BOOL reduce_offscreen = TRUE;
  if (FAILED(TaskDialogIndirect(&dialog, &button, &choice, &reduce_offscreen))) {
    MessageBoxW(nullptr, L"Could not open the resolution chooser.", L"Tekken 6",
                MB_OK | MB_ICONERROR);
    return false;
  }
  if (button != IDOK) return false;
  offscreen_resolution = reduce_offscreen ? L"512x512" : L"1024x1024";

  switch (choice) {
    case k640x360: resolution = L"640x360"; return true;
    case k768x432: resolution = L"768x432"; return true;
    case k1024x576: resolution = L"1024x576"; return true;
    default: return false;
  }
}

int WINAPI wWinMain(HINSTANCE, HINSTANCE, PWSTR arguments, int) {
  std::vector<wchar_t> module(32768);
  const DWORD length = GetModuleFileNameW(nullptr, module.data(), DWORD(module.size()));
  if (!length || length >= module.size()) return Fail(L"Cannot locate the game folder.");
  const std::wstring executable(module.data(), length);
  const auto root = executable.substr(0, executable.find_last_of(L"\\/"));
  const auto host = root + L"\\bin\\tekken6.exe";
  const auto game = root + L"\\game";
  if (GetFileAttributesW(host.c_str()) == INVALID_FILE_ATTRIBUTES ||
      GetFileAttributesW((game + L"\\default.xex").c_str()) == INVALID_FILE_ATTRIBUTES) {
    return Fail(L"Game or runtime files are missing. Copy the entire Windows package folder.",
                ERROR_FILE_NOT_FOUND);
  }

  const wchar_t* internal_resolution = nullptr;
  const wchar_t* offscreen_resolution = nullptr;
  if (!ChooseRenderingOptions(internal_resolution, offscreen_resolution)) return 0;

  SYSTEMTIME now;
  GetLocalTime(&now);
  wchar_t run_name[96];
  swprintf_s(run_name, L"%04u-%02u-%02u_%02u-%02u-%02u_%lu", now.wYear, now.wMonth,
             now.wDay, now.wHour, now.wMinute, now.wSecond, GetCurrentProcessId());
  const auto crashes = root + L"\\crashes";
  const auto crash_dir = crashes + L"\\" + run_name;
  if (!Directory(crashes) || !Directory(crash_dir) || !Directory(root + L"\\user") ||
      !Directory(root + L"\\cache")) {
    return Fail(L"Cannot prepare the game package directories.");
  }
#if defined(TEKKEN6_LATE_DEPTH)
  if (!Directory(root + L"\\cache\\late-depth")) return Fail(L"Cannot create the late-depth cache.");
#elif defined(TEKKEN6_FUSED_RESOLVE)
  if (!Directory(root + L"\\cache\\fused-resolve")) return Fail(L"Cannot create the fused-resolve cache.");
#endif

  const struct { const wchar_t* name; const wchar_t* value; } settings[] = {
      {L"TEKKEN6_YIELD_STARTUP_SPIN", L"1"},
      {L"TEKKEN6_FRAME_PROBE_ATTEMPTS", L"0"},
      {L"REX_FULLSCREEN", L"0"},
      {L"REX_LOG_LEVEL", L"off"},
      {L"TEKKEN6_CRASH_DIR", crash_dir.c_str()},
      {L"TEKKEN6_INTERNAL_RESOLUTION", internal_resolution},
      {L"TEKKEN6_OFFSCREEN_RESOLUTION", offscreen_resolution},
  };
  for (const auto& setting : settings) {
    if (!SetEnvironmentVariableW(setting.name, setting.value)) {
      return Fail(L"Cannot configure the game process.");
    }
  }
  const wchar_t* disabled_settings[] = {
      L"TEKKEN6_CAPTURE_ALL", L"TEKKEN6_CAPTURE_CONTINUOUS", L"TEKKEN6_TRACE_IO",
      L"TEKKEN6_TRACE_QUEUE", L"TEKKEN6_TRACE_MOVIE", L"TEKKEN6_TRACE_TITLE_STATE",
      L"TEKKEN6_TRACE_STARTUP_GATE", L"TEKKEN6_TRACE_OUTPUT",
      L"TEKKEN6_TRACE_RENDERING", L"TEKKEN6_TRACE_RENDERING_DETAIL",
      L"TEKKEN6_TRACE_RENDERING_DETAIL_INTERVAL",
  };
  for (const auto* setting : disabled_settings) {
    if (!SetEnvironmentVariableW(setting, nullptr)) {
      return Fail(L"Cannot disable diagnostic tracing.");
    }
  }

  auto command = L"\"" + host + L"\" --game_data_root=\"" + game +
      L"\" --user_data_root=\"" + root + L"\\user\" --cache_root=\"" + root +
#if defined(TEKKEN6_LATE_DEPTH)
      L"\\cache\\late-depth\" --fullscreen=false --log_file=NUL --log_level=off";
#elif defined(TEKKEN6_FUSED_RESOLVE)
      L"\\cache\\fused-resolve\" --fullscreen=false --log_file=NUL --log_level=off";
#else
      L"\\cache\" --fullscreen=false --log_file=NUL --log_level=off";
#endif
#if defined(TEKKEN6_LATE_DEPTH)
  command += L" --gpu_backend=d3d12 --async_shader_compilation=true"
             L" --render_target_path_d3d12=rov --anisotropic_override=0"
             L" --d3d12_rov_late_depth=true";
#elif defined(TEKKEN6_FUSED_RESOLVE)
  command += L" --gpu_backend=d3d12 --async_shader_compilation=true"
             L" --render_target_path_d3d12=rov --anisotropic_override=0"
             L" --d3d12_fused_resolve=true";
#elif defined(TEKKEN6_VULKAN_FBO)
  command += L" --gpu_backend=vulkan --render_target_path_vulkan=fbo"
             L" --async_shader_compilation=false --anisotropic_override=0";
#elif defined(TEKKEN6_VULKAN)
  command += L" --gpu_backend=vulkan --render_target_path_vulkan=fsi"
             L" --async_shader_compilation=false --anisotropic_override=0";
#else
  command += L" --gpu_backend=d3d12 --async_shader_compilation=true"
             L" --render_target_path_d3d12=rov --anisotropic_override=0";
#endif
  if (arguments && *arguments) command += std::wstring(L" ") + arguments;
  std::vector<wchar_t> command_buffer(command.begin(), command.end());
  command_buffer.push_back(0);

  SECURITY_ATTRIBUTES security{sizeof(SECURITY_ATTRIBUTES), nullptr, TRUE};
  HANDLE null_device = CreateFileW(L"NUL", GENERIC_READ | GENERIC_WRITE,
      FILE_SHARE_READ | FILE_SHARE_WRITE, &security, OPEN_EXISTING,
      FILE_ATTRIBUTE_NORMAL, nullptr);
  if (null_device == INVALID_HANDLE_VALUE) return Fail(L"Cannot initialize the game process.");
  STARTUPINFOW startup{};
  startup.cb = sizeof(startup);
  startup.dwFlags = STARTF_USESTDHANDLES;
  startup.hStdInput = null_device;
  startup.hStdOutput = startup.hStdError = null_device;
  PROCESS_INFORMATION process{};
  const BOOL launched = CreateProcessW(host.c_str(), command_buffer.data(), nullptr, nullptr,
      TRUE, 0, nullptr, root.c_str(), &startup, &process);
  const DWORD launch_error = GetLastError();
  CloseHandle(null_device);
  if (!launched) return Fail(L"Cannot start Tekken 6.", launch_error);
  CloseHandle(process.hThread);
  WaitForSingleObject(process.hProcess, INFINITE);
  DWORD result = 0;
  GetExitCodeProcess(process.hProcess, &result);
  CloseHandle(process.hProcess);

  if (result) {
    const auto crash_report = crash_dir + L"\\crash.txt";
#if defined(TEKKEN6_VULKAN) && !defined(TEKKEN6_VULKAN_FBO)
    if (GetFileAttributesW(crash_report.c_str()) == INVALID_FILE_ATTRIBUTES) {
      return Fail(L"Vulkan FSI failed. The selected device may not expose fragment shader interlock.",
                  result);
    }
#endif
    if (GetFileAttributesW(crash_report.c_str()) != INVALID_FILE_ATTRIBUTES) {
      return Fail(L"Tekken 6 crashed. Crash report: " + crash_report, result);
    }
    return Fail(L"Tekken 6 exited with an error.", result);
  }
  return 0;
}
