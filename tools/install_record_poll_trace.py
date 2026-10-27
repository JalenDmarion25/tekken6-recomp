#!/usr/bin/env python3
"""Install or remove opt-in, bounded controller poll diagnostics."""
import argparse
from pathlib import Path
import shutil
from datetime import datetime
p=argparse.ArgumentParser(); p.add_argument('--remove',action='store_true');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent); a=p.parse_args()
path=a.root/'src/tekken6_guest_hooks.cpp';s=path.read_text(encoding='utf-8-sig')
start='  // BEGIN RECORD POLL TRACE V1\n';end='  // END RECORD POLL TRACE V1\n'
needle='void TraceTekkenButtons(PPCRegister &object, PPCRegister &buttons)\n{\n'
block='''  // BEGIN RECORD POLL TRACE V1
  // Diagnostic only: capture every update for the two observed input objects.
  // These addresses are used only to filter logging, never to alter input.
  if (const char *tracePath = std::getenv("TEKKEN6_RECORD_POLL_TRACE")) {
    if (*tracePath && (object.u32 == 0x82CDEB3Cu || object.u32 == 0x82CDECCCu)) {
      static std::mutex traceMutex;
      std::lock_guard<std::mutex> traceLock(traceMutex);
      static std::FILE *traceFile = std::fopen(tracePath, "w");
      static unsigned traceCount = 0;
      if (traceFile && traceCount < 20000) {
        const auto now = std::chrono::steady_clock::now().time_since_epoch();
        const auto micros = std::chrono::duration_cast<std::chrono::microseconds>(now).count();
        std::fprintf(traceFile, "%u %lld %08X %08X\\n", ++traceCount,
                     static_cast<long long>(micros), object.u32, buttons.u32);
        if ((traceCount % 120) == 0) std::fflush(traceFile);
        if (traceCount == 20000) std::fflush(traceFile);
      }
    }
  }
  // END RECORD POLL TRACE V1
'''
if a.remove:
 if start not in s or end not in s: raise SystemExit('Diagnostic block not found; no changes made.')
 i=s.index(start);j=s.index(end,i)+len(end);out=s[:i]+s[j:]
else:
 if start in s and end in s: print('Diagnostic already installed.');raise SystemExit(0)
 if start in s or end in s or s.count(needle)!=1: raise SystemExit('Unexpected source layout; no changes made.')
 if not all(x in s for x in ['#include <chrono>','#include <mutex>','#include <cstdio>']): raise SystemExit('Missing expected includes; no changes made.')
 out=s.replace(needle,needle+block,1)
backup=path.with_name(path.name+'.before-record-poll-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));shutil.copy2(path,backup);path.write_text(out,encoding='utf-8',newline='\n');print('Updated:',path);print('Backup:',backup);print('Build and package before testing.')
