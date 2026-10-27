#!/usr/bin/env python3
"""Add a reversible diagnostic to compare practice input updates and fighter state."""
import argparse,shutil
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--remove',action='store_true');a=p.parse_args();f=a.root/'src/tekken6_guest_hooks.cpp';s=f.read_text(encoding='utf-8-sig')
begin='  // BEGIN RECORD FRAME TRACE V1\n';end='  // END RECORD FRAME TRACE V1\n'
needle='  practiceHeld.store(held.u32, std::memory_order_relaxed);\n'
block='''  // BEGIN RECORD FRAME TRACE V1
  if (const char *path=std::getenv("TEKKEN6_RECORD_FRAME_TRACE")) {
    if (*path && practiceRageOwner.load(std::memory_order_acquire)) {
      auto *runtime=rex::Runtime::instance();
      uint8_t *base=runtime ? runtime->virtual_membase() : nullptr;
      static std::mutex traceMutex;
      std::lock_guard<std::mutex> lock(traceMutex);
      static std::FILE *f=std::fopen(path,"w");
      static unsigned count=0;
      if (base && f && count<10000) {
        auto readbe=[&](uint32_t a) {return (uint32_t(base[a])<<24)|(uint32_t(base[a+1])<<16)|(uint32_t(base[a+2])<<8)|base[a+3];};
        const auto us=std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
        std::fprintf(f,"%u %lld %08X %08X %08X %08X %08X\\n",++count,
          static_cast<long long>(us),held.u32,readbe(0x82900C00u+0xC4),readbe(0x82901840u+0xC4),readbe(0x82900C00u+0xC8),readbe(0x82901840u+0xC8));
        if(count%120==0)std::fflush(f);
      }
    }
  }
  // END RECORD FRAME TRACE V1
'''
if a.remove:
 if s.count(begin)!=1 or s.count(end)!=1:raise SystemExit('Trace markers missing; no changes made.')
 i=s.index(begin);out=s[:i]+s[s.index(end,i)+len(end):]
else:
 if begin in s or end in s:raise SystemExit('Diagnostic exists or partial install; no changes made.')
 if s.count(needle)!=1 or 'practiceRageOwner' not in s:raise SystemExit('Unexpected source; no changes made.')
 out=s.replace(needle,needle+block,1)
backup=f.with_name(f.name+'.before-frame-trace-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));shutil.copy2(f,backup);f.write_text(out,encoding='utf-8',newline='\n');print('Updated:',f);print('Backup:',backup);print('Build and package before testing.')
