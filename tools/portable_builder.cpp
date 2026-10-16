#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <commctrl.h>
#include <commdlg.h>
#include <shlobj.h>

#include <algorithm>
#include <string>
#include <utility>
#include <vector>

namespace {

enum : int {
  kIsoEdit = 1001,
  kIsoBrowse,
  kOutputEdit,
  kOutputBrowse,
  kD3d12Check,
  kVulkanFsiCheck,
  kVulkanFboCheck,
  kBuildButton,
  kActivity,
  kProgress,
  kLog,
};

HWND g_window = nullptr;
HWND g_iso_edit = nullptr;
HWND g_output_edit = nullptr;
HWND g_d3d12_check = nullptr;
HWND g_vulkan_fsi_check = nullptr;
HWND g_vulkan_fbo_check = nullptr;
HWND g_build_button = nullptr;
HWND g_activity = nullptr;
HWND g_progress = nullptr;
HWND g_log = nullptr;
HANDLE g_process = nullptr;
HANDLE g_pipe_read = nullptr;
std::string g_pending_output;
bool g_building = false;
bool g_build_finished = false;
unsigned g_activity_frame = 0;

std::wstring ModulePath() {
  std::vector<wchar_t> buffer(32768);
  const DWORD length = GetModuleFileNameW(nullptr, buffer.data(),
                                          static_cast<DWORD>(buffer.size()));
  if (!length || length >= buffer.size()) return {};
  return std::wstring(buffer.data(), length);
}

std::wstring ParentPath(const std::wstring& path) {
  const size_t split = path.find_last_of(L"\\/");
  return split == std::wstring::npos ? L"." : path.substr(0, split);
}

std::wstring Join(const std::wstring& left, const wchar_t* right) {
  return left + L"\\" + right;
}

std::wstring ReadText(HWND control) {
  const int length = GetWindowTextLengthW(control);
  std::wstring value(static_cast<size_t>(length) + 1, L'\0');
  if (length) GetWindowTextW(control, value.data(), length + 1);
  value.resize(static_cast<size_t>(length));
  return value;
}

std::wstring Quote(const std::wstring& value) {
  std::wstring result = L"\"";
  size_t slashes = 0;
  for (wchar_t character : value) {
    if (character == L'\\') {
      ++slashes;
    } else if (character == L'\"') {
      result.append(slashes * 2 + 1, L'\\');
      result.push_back(character);
      slashes = 0;
    } else {
      result.append(slashes, L'\\');
      slashes = 0;
      result.push_back(character);
    }
  }
  result.append(slashes * 2, L'\\');
  result.push_back(L'\"');
  return result;
}

HWND AddControl(const wchar_t* class_name, const wchar_t* text, DWORD style,
                int x, int y, int width, int height, int id) {
  HWND control = CreateWindowExW(
      0, class_name, text, WS_CHILD | WS_VISIBLE | style, x, y, width, height,
      g_window, reinterpret_cast<HMENU>(static_cast<INT_PTR>(id)),
      GetModuleHandleW(nullptr), nullptr);
  SendMessageW(control, WM_SETFONT,
               reinterpret_cast<WPARAM>(GetStockObject(DEFAULT_GUI_FONT)), TRUE);
  return control;
}

void SetBuildControlsEnabled(bool enabled) {
  EnableWindow(g_iso_edit, enabled);
  EnableWindow(GetDlgItem(g_window, kIsoBrowse), enabled);
  EnableWindow(g_output_edit, enabled);
  EnableWindow(GetDlgItem(g_window, kOutputBrowse), enabled);
  EnableWindow(g_d3d12_check, enabled);
  EnableWindow(g_vulkan_fsi_check, enabled);
  EnableWindow(g_vulkan_fbo_check, enabled);
  EnableWindow(g_build_button, enabled);
}

void DrawActivity(const DRAWITEMSTRUCT& item) {
  FillRect(item.hDC, &item.rcItem, GetSysColorBrush(COLOR_BTNFACE));
  if (!g_building) return;
  constexpr POINT positions[] = {
      {0, -8}, {6, -6}, {8, 0}, {6, 6},
      {0, 8}, {-6, 6}, {-8, 0}, {-6, -6},
  };
  const int center_x = (item.rcItem.left + item.rcItem.right) / 2;
  const int center_y = (item.rcItem.top + item.rcItem.bottom) / 2;
  const COLORREF foreground = GetSysColor(COLOR_HIGHLIGHT);
  const COLORREF background = GetSysColor(COLOR_BTNFACE);
  for (unsigned index = 0; index < ARRAYSIZE(positions); ++index) {
    const unsigned strength = 8 - ((index + 8 - g_activity_frame) % 8);
    const auto blend = [strength](unsigned front, unsigned back) {
      return static_cast<BYTE>((front * strength + back * (8 - strength)) / 8);
    };
    HBRUSH brush = CreateSolidBrush(RGB(
        blend(GetRValue(foreground), GetRValue(background)),
        blend(GetGValue(foreground), GetGValue(background)),
        blend(GetBValue(foreground), GetBValue(background))));
    HGDIOBJ old_brush = SelectObject(item.hDC, brush);
    HGDIOBJ old_pen = SelectObject(item.hDC, GetStockObject(NULL_PEN));
    const int x = center_x + positions[index].x;
    const int y = center_y + positions[index].y;
    Ellipse(item.hDC, x - 2, y - 2, x + 3, y + 3);
    SelectObject(item.hDC, old_pen);
    SelectObject(item.hDC, old_brush);
    DeleteObject(brush);
  }
}

void AppendLog(const std::wstring& line) {
  const int length = GetWindowTextLengthW(g_log);
  SendMessageW(g_log, EM_SETSEL, length, length);
  SendMessageW(g_log, EM_REPLACESEL, FALSE,
               reinterpret_cast<LPARAM>((line + L"\r\n").c_str()));
  SendMessageW(g_log, EM_SCROLLCARET, 0, 0);
}

void AppendUtf8Line(const std::string& text) {
  if (text.empty()) return;
  const int required = MultiByteToWideChar(CP_UTF8, 0, text.data(),
      static_cast<int>(text.size()), nullptr, 0);
  if (required <= 0) {
    std::wstring fallback(text.begin(), text.end());
    AppendLog(fallback);
    return;
  }
  std::wstring wide(static_cast<size_t>(required), L'\0');
  MultiByteToWideChar(CP_UTF8, 0, text.data(), static_cast<int>(text.size()),
                      wide.data(), required);
  std::wstring line = std::move(wide);
  if (!line.empty() && line.back() == L'\r') line.pop_back();
  if (line.rfind(L"PROGRESS ", 0) == 0) {
    try {
      const int progress = std::clamp(std::stoi(line.substr(9)), 0, 100);
      SendMessageW(g_progress, PBM_SETPOS, progress, 0);
    } catch (...) {
    }
  } else {
    AppendLog(line);
  }
}

bool ReadAvailableOutput() {
  if (!g_pipe_read) return true;
  for (;;) {
    DWORD available = 0;
    if (!PeekNamedPipe(g_pipe_read, nullptr, 0, nullptr, &available, nullptr)) {
      return false;
    }
    if (!available) return true;
    char buffer[4096];
    DWORD read = 0;
    if (!ReadFile(g_pipe_read, buffer,
                  std::min<DWORD>(available, sizeof(buffer)), &read, nullptr)) {
      return false;
    }
    if (!read) return true;
    g_pending_output.append(buffer, read);
    size_t newline = 0;
    while ((newline = g_pending_output.find('\n')) != std::string::npos) {
      AppendUtf8Line(g_pending_output.substr(0, newline));
      g_pending_output.erase(0, newline + 1);
    }
  }
}

bool Exists(const std::wstring& path) {
  return GetFileAttributesW(path.c_str()) != INVALID_FILE_ATTRIBUTES;
}

void ShowError(const std::wstring& message) {
  MessageBoxW(g_window, message.c_str(), L"Tekken 6 Builder",
              MB_OK | MB_ICONERROR);
}

void BrowseIso() {
  wchar_t path[MAX_PATH] = {};
  OPENFILENAMEW dialog{};
  dialog.lStructSize = sizeof(dialog);
  dialog.hwndOwner = g_window;
  dialog.lpstrFilter = L"Xbox 360 ISO images (*.iso)\0*.iso\0All files (*.*)\0*.*\0\0";
  dialog.lpstrFile = path;
  dialog.nMaxFile = ARRAYSIZE(path);
  dialog.lpstrTitle = L"Select your Tekken 6 Xbox 360 ISO";
  dialog.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST | OFN_NOCHANGEDIR;
  if (GetOpenFileNameW(&dialog)) SetWindowTextW(g_iso_edit, path);
}

void BrowseOutput() {
  BROWSEINFOW dialog{};
  dialog.hwndOwner = g_window;
  dialog.lpszTitle = L"Choose where to save the built game";
  dialog.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE;
  PIDLIST_ABSOLUTE item = SHBrowseForFolderW(&dialog);
  if (!item) return;
  wchar_t path[MAX_PATH] = {};
  if (SHGetPathFromIDListW(item, path)) SetWindowTextW(g_output_edit, path);
  CoTaskMemFree(item);
}

bool StartBuild() {
  if (g_building || g_build_finished) return false;
  const std::wstring iso = ReadText(g_iso_edit);
  std::wstring output = ReadText(g_output_edit);
  if (iso.empty() || !Exists(iso)) {
    ShowError(L"Choose your Tekken 6 ISO file first.");
    return false;
  }
  const DWORD iso_attributes = GetFileAttributesW(iso.c_str());
  if (iso_attributes == INVALID_FILE_ATTRIBUTES ||
      (iso_attributes & FILE_ATTRIBUTE_DIRECTORY)) {
    ShowError(L"Select an ISO file, not a folder.");
    return false;
  }
  if (output.empty()) {
    ShowError(L"Choose a folder for the built game first.");
    return false;
  }
  const bool d3d12 = SendMessageW(g_d3d12_check, BM_GETCHECK, 0, 0) == BST_CHECKED;
  const bool vulkan_fsi = SendMessageW(g_vulkan_fsi_check, BM_GETCHECK, 0, 0) == BST_CHECKED;
  const bool vulkan_fbo = SendMessageW(g_vulkan_fbo_check, BM_GETCHECK, 0, 0) == BST_CHECKED;
  if (!d3d12 && !vulkan_fsi && !vulkan_fbo) {
    ShowError(L"Select at least one renderer to build.");
    return false;
  }

  const std::wstring app_root = ParentPath(ModulePath());
  const std::wstring builder = Join(app_root, L"builder");
  const std::wstring python = Join(Join(builder, L"python"), L"python.exe");
  const std::wstring script = Join(builder, L"build_from_iso.py");
  const std::wstring project_archive = Join(builder, L"project.zip");

  std::wstring command = Quote(python) + L" -X utf8 -I " + Quote(script) +
      L" --iso " + Quote(iso) + L" --output " + Quote(output) +
      L" --builder-root " + Quote(builder) + L" --project " + Quote(project_archive);
  if (d3d12) command += L" --d3d12-rov";
  if (vulkan_fsi) command += L" --vulkan-fsi";
  if (vulkan_fbo) command += L" --vulkan-fbo";

  SECURITY_ATTRIBUTES security{sizeof(SECURITY_ATTRIBUTES), nullptr, TRUE};
  HANDLE pipe_write = nullptr;
  if (!CreatePipe(&g_pipe_read, &pipe_write, &security, 0)) {
    ShowError(L"Could not start the build log.");
    return false;
  }
  SetHandleInformation(g_pipe_read, HANDLE_FLAG_INHERIT, 0);

  STARTUPINFOW startup{};
  startup.cb = sizeof(startup);
  startup.dwFlags = STARTF_USESTDHANDLES;
  startup.hStdOutput = pipe_write;
  startup.hStdError = pipe_write;
  HANDLE null_input = CreateFileW(L"NUL", GENERIC_READ,
      FILE_SHARE_READ | FILE_SHARE_WRITE, &security, OPEN_EXISTING,
      FILE_ATTRIBUTE_NORMAL, nullptr);
  if (null_input == INVALID_HANDLE_VALUE) {
    CloseHandle(pipe_write);
    CloseHandle(g_pipe_read);
    g_pipe_read = nullptr;
    ShowError(L"Could not prepare the build process.");
    return false;
  }
  startup.hStdInput = null_input;
  PROCESS_INFORMATION process{};
  std::vector<wchar_t> mutable_command(command.begin(), command.end());
  mutable_command.push_back(L'\0');
  const BOOL launched = CreateProcessW(
      python.c_str(), mutable_command.data(), nullptr, nullptr, TRUE,
      CREATE_NO_WINDOW, nullptr, builder.c_str(), &startup, &process);
  const DWORD error = GetLastError();
  CloseHandle(null_input);
  CloseHandle(pipe_write);
  if (!launched) {
    CloseHandle(g_pipe_read);
    g_pipe_read = nullptr;
    ShowError(L"Could not start the build. Windows error " + std::to_wstring(error) + L".");
    return false;
  }
  CloseHandle(process.hThread);
  g_process = process.hProcess;
  g_building = true;
  g_activity_frame = 0;
  InvalidateRect(g_activity, nullptr, FALSE);
  g_pending_output.clear();
  SendMessageW(g_progress, PBM_SETPOS, 0, 0);
  SetBuildControlsEnabled(false);
  AppendLog(L"Build started. The first build can take several minutes.");
  SetTimer(g_window, 1, 150, nullptr);
  return true;
}

void PollBuild() {
  ReadAvailableOutput();
  if (!g_process || WaitForSingleObject(g_process, 0) != WAIT_OBJECT_0) return;
  ReadAvailableOutput();
  if (!g_pending_output.empty()) {
    AppendUtf8Line(g_pending_output);
    g_pending_output.clear();
  }
  DWORD exit_code = 1;
  GetExitCodeProcess(g_process, &exit_code);
  CloseHandle(g_process);
  g_process = nullptr;
  if (g_pipe_read) CloseHandle(g_pipe_read);
  g_pipe_read = nullptr;
  KillTimer(g_window, 1);
  g_building = false;
  g_build_finished = exit_code == 0;
  InvalidateRect(g_activity, nullptr, FALSE);
  if (exit_code == 0) {
    SetBuildControlsEnabled(false);
    SetWindowTextW(g_build_button, L"Finished");
    SendMessageW(g_progress, PBM_SETPOS, 100, 0);
    AppendLog(L"Build finished. Open the selected output folder to play.");
  } else {
    SetBuildControlsEnabled(true);
    AppendLog(L"Build failed. The full details are in builder\\build.log.");
  }
}

void CreateUi() {
  AddControl(L"STATIC", L"Build a Windows game package from your own Xbox 360 ISO.",
             0, 18, 16, 510, 22, 0);
  AddControl(L"STATIC", L"ISO file:", 0, 18, 50, 90, 22, 0);
  g_iso_edit = AddControl(L"EDIT", L"", WS_BORDER | ES_AUTOHSCROLL,
                          18, 74, 410, 25, kIsoEdit);
  AddControl(L"BUTTON", L"Browse...", BS_PUSHBUTTON,
             438, 73, 90, 27, kIsoBrowse);
  AddControl(L"STATIC",
      L"Example: Tekken 6 (Europe) (En,Ja,Fr,De,Es,It,Ko,Ru).iso",
      0, 18, 103, 515, 22, 0);

  AddControl(L"STATIC", L"Output folder:", 0, 18, 140, 110, 22, 0);
  g_output_edit = AddControl(L"EDIT", L"", WS_BORDER | ES_AUTOHSCROLL,
                             18, 164, 410, 25, kOutputEdit);
  AddControl(L"BUTTON", L"Browse...", BS_PUSHBUTTON,
             438, 163, 90, 27, kOutputBrowse);

  AddControl(L"STATIC", L"Build versions:", 0, 18, 207, 150, 22, 0);
  g_d3d12_check = AddControl(L"BUTTON", L"D3D12 ROV (widest compatibility)",
      BS_AUTOCHECKBOX | WS_TABSTOP, 22, 232, 450, 24, kD3d12Check);
  SendMessageW(g_d3d12_check, BM_SETCHECK, BST_CHECKED, 0);
  g_vulkan_fsi_check = AddControl(L"BUTTON",
      L"Vulkan FSI (requires fragment shader interlock)",
      BS_AUTOCHECKBOX | WS_TABSTOP, 22, 260, 480, 24, kVulkanFsiCheck);
  g_vulkan_fbo_check = AddControl(L"BUTTON", L"Vulkan FBO (experimental)",
      BS_AUTOCHECKBOX | WS_TABSTOP, 22, 288, 450, 24, kVulkanFboCheck);

  g_build_button = AddControl(L"BUTTON", L"Build", BS_DEFPUSHBUTTON | WS_TABSTOP,
                              18, 328, 110, 32, kBuildButton);
  g_activity = AddControl(L"STATIC", L"", SS_OWNERDRAW,
                          136, 333, 24, 24, kActivity);
  g_progress = AddControl(PROGRESS_CLASSW, L"", 0, 172, 333, 356, 24, kProgress);
  SendMessageW(g_progress, PBM_SETRANGE32, 0, 100);
  g_log = AddControl(L"EDIT", L"", WS_BORDER | ES_MULTILINE | ES_AUTOVSCROLL |
                     ES_READONLY | WS_VSCROLL, 18, 374, 510, 145, kLog);
  SendMessageW(g_log, EM_SETLIMITTEXT, 1024 * 1024, 0);
}

LRESULT CALLBACK WindowProc(HWND window, UINT message, WPARAM wparam,
                            LPARAM lparam) {
  switch (message) {
    case WM_CREATE:
      g_window = window;
      CreateUi();
      return 0;
    case WM_COMMAND:
      switch (LOWORD(wparam)) {
        case kIsoBrowse: BrowseIso(); return 0;
        case kOutputBrowse: BrowseOutput(); return 0;
        case kBuildButton: StartBuild(); return 0;
      }
      break;
    case WM_TIMER:
      if (wparam == 1) {
        g_activity_frame = (g_activity_frame + 1) % 8;
        InvalidateRect(g_activity, nullptr, FALSE);
        PollBuild();
      }
      return 0;
    case WM_DRAWITEM:
      if (wparam == kActivity) {
        DrawActivity(*reinterpret_cast<const DRAWITEMSTRUCT*>(lparam));
        return TRUE;
      }
      break;
    case WM_CLOSE:
      if (g_building) {
        if (MessageBoxW(window,
                L"A build is still running. Close the builder and stop it?",
                L"Tekken 6 Builder", MB_YESNO | MB_ICONQUESTION) != IDYES) {
          return 0;
        }
        if (g_process) TerminateProcess(g_process, 1);
      }
      DestroyWindow(window);
      return 0;
    case WM_DESTROY:
      if (g_process) CloseHandle(g_process);
      if (g_pipe_read) CloseHandle(g_pipe_read);
      PostQuitMessage(0);
      return 0;
  }
  return DefWindowProcW(window, message, wparam, lparam);
}

}  // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int show_command) {
  INITCOMMONCONTROLSEX controls{sizeof(controls), ICC_PROGRESS_CLASS};
  InitCommonControlsEx(&controls);

  WNDCLASSW window_class{};
  window_class.lpfnWndProc = WindowProc;
  window_class.hInstance = instance;
  window_class.hCursor = LoadCursorW(nullptr, MAKEINTRESOURCEW(32512));
  window_class.hIcon = LoadIconW(nullptr, MAKEINTRESOURCEW(32512));
  window_class.hbrBackground = GetSysColorBrush(COLOR_BTNFACE);
  window_class.lpszClassName = L"Tekken6PortableBuilderWindow";
  if (!RegisterClassW(&window_class)) return 1;

  HWND window = CreateWindowExW(0, window_class.lpszClassName,
      L"Tekken 6 Builder", WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU |
      WS_MINIMIZEBOX, CW_USEDEFAULT, CW_USEDEFAULT, 562, 568,
      nullptr, nullptr, instance, nullptr);
  if (!window) return 1;
  ShowWindow(window, show_command);
  UpdateWindow(window);
  MSG message{};
  while (GetMessageW(&message, nullptr, 0, 0) > 0) {
    TranslateMessage(&message);
    DispatchMessageW(&message);
  }
  return static_cast<int>(message.wParam);
}
