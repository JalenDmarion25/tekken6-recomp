#!/usr/bin/env python3
"""Add an opt-in, single-slot input capture test to the control-toggle experiment."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--remove',action='store_true');a=p.parse_args();f=a.root/'src/tekken6_guest_hooks.cpp';s=f.read_text(encoding='utf-8-sig')
b='  // BEGIN RECORD CAPTURE TEST V1\n';e='  // END RECORD CAPTURE TEST V1\n';old='const bool heldCombo=(held.u32 & 0x4020u)==0x4020u;';new='const bool heldCombo=(held.u32 & 0x8020u)==0x8020u;';anchor='  // END OPPONENT TOGGLE INPUT V1\n'
block='''  // BEGIN RECORD CAPTURE TEST V1
  // One temporary in-memory slot; no playback or persistence in this test.
  if (enabled && std::strcmp(enabled,"1")==0 && practice) {
    static uint32_t samples[1800];
    static unsigned count=0;
    static bool recording=false, wasRecordCombo=false;
    static std::chrono::steady_clock::time_point started;
    const bool combo=(held.u32 & 0x4020u)==0x4020u;
    const bool activeControl=opponentToggleTest.load(std::memory_order_relaxed);
    auto save=[&](const char *reason) {
      if (std::FILE *f=std::fopen("recording-first-test.txt","w")) {
        const auto ms=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-started).count();
        std::fprintf(f,"reason=%s samples=%u elapsed_ms=%lld\\n",reason,count,static_cast<long long>(ms));
        for(unsigned i=0;i<count;++i) std::fprintf(f,"%u %08X\\n",i,samples[i]);
        std::fclose(f);
      }
      recording=false;
    };
    if(recording && !activeControl) save("control-ended");
    if(activeControl && combo && !wasRecordCombo) {
      if(recording) save("manual-stop");
      else {count=0;started=std::chrono::steady_clock::now();recording=true;}
    }
    wasRecordCombo=combo;
    if(recording) {
      if(std::chrono::steady_clock::now()-started>=std::chrono::seconds(30)) save("time-limit");
      else if(count>=1800) save("sample-limit");
      else samples[count++]=(held.u32 & 0x20u)?0:held.u32;
    }
  }
  // END RECORD CAPTURE TEST V1
'''
if a.remove:
 if s.count(b)!=1 or s.count(e)!=1 or s.count(new)!=1:raise SystemExit('Missing or inconsistent test; no changes made.')
 i=s.index(b);out=(s[:i]+s[s.index(e,i)+len(e):]).replace(new,old,1)
else:
 if b in s or e in s:raise SystemExit('Already or partially installed; no changes made.')
 if s.count(anchor)!=1 or s.count(old)!=1 or 'BEGIN NATIVE DUMMY CONTROL TEST V1' not in s:raise SystemExit('Working toggle/native tests required; no changes made.')
 out=s.replace(old,new,1).replace(anchor,anchor+block,1)
backup=f.with_name(f.name+'.before-record-capture-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));shutil.copy2(f,backup);f.write_text(out,encoding='utf-8',newline='\n');print('Updated:',f);print('Backup:',backup);print('Build and package.')
