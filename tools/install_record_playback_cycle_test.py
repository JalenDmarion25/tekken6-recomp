#!/usr/bin/env python3
"""Install a reversible opt-in record/playback cycle over the first playback test."""
from pathlib import Path
from datetime import datetime
import argparse, base64, shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--remove',action='store_true');a=p.parse_args()
f=a.root/'src/tekken6_guest_hooks.cpp';s=f.read_text(encoding='utf-8-sig')
begin='  // BEGIN RECORD PLAYBACK CYCLE V1\n';end='  // END RECORD PLAYBACK CYCLE V1\n'; save='  // CYCLE ORIGINAL BASE64: '
if a.remove:
 if s.count(begin)!=1 or s.count(end)!=1 or s.count(save)!=1:raise SystemExit('Cycle markers missing; no changes made.')
 i=s.index(begin);j=s.index(end,i)+len(end); line=s[s.index(save)+len(save):].split('\n',1)[0]
 try: original=base64.b64decode(line,validate=True).decode('utf-8')
 except Exception: raise SystemExit('Invalid backup marker; no changes made.')
 out=s[:i]+original+s[j:]
else:
 if begin in s:raise SystemExit('Already installed; no changes made.')
 a1='  // BEGIN RECORD CAPTURE TEST V1\n';a2='  // END FIRST PLAYBACK TICK V1\n'
 if s.count(a1)!=1 or s.count(a2)!=1 or 'BEGIN FIRST PLAYBACK GLOBALS V1' not in s:raise SystemExit('First playback test must be installed; no changes made.')
 i=s.index(a1);j=s.index(a2,i)+len(a2);original=s[i:j]
 cycle=r'''  // BEGIN RECORD PLAYBACK CYCLE V1
  if (const char *cycle=std::getenv("TEKKEN6_TEST_RECORD_CYCLE"); cycle && std::strcmp(cycle,"1")==0) {
    static bool recording=false, previousCombo=false;
    static std::chrono::steady_clock::time_point started;
    const bool valid=enabled && std::strcmp(enabled,"1")==0 && practice;
    const bool combo=valid && (held.u32 & 0x4020u)==0x4020u;
    const bool edge=combo && !previousCombo;
    auto log=[](const char *event, unsigned count) {
      if (std::FILE *f=std::fopen("record-cycle-test.txt","a")) {
        std::fprintf(f,"%s samples=%u reads=%u\n",event,count,firstPlaybackReads.load()); std::fclose(f);
      }
    };
    auto finish=[&](const char *reason) {
      recording=false;
      // Retain the native Controller setting until the menu is opened again.
      opponentToggleTest.store(false,std::memory_order_relaxed);
      log(reason,firstPlaybackCount);
    };
    if (!valid) {
      if (recording) finish("practice-ended");
      firstPlaybackState.store(0,std::memory_order_release);
      previousCombo=false;
    } else {
      if (recording && !opponentToggleTest.load(std::memory_order_relaxed)) finish("control-ended");
      if (edge && firstPlaybackState.load(std::memory_order_acquire)!=1) {
        if (recording) finish("record-stop");
        else if (opponentToggleTest.load(std::memory_order_relaxed)) {
          firstPlaybackState.store(0,std::memory_order_release);
          firstPlaybackCount=0; firstPlaybackPosition=0; recording=true;
          started=std::chrono::steady_clock::now(); log("record-start",0);
        } else if (firstPlaybackCount) {
          firstPlaybackPosition=0; firstPlaybackReads.store(0);
          firstPlaybackCurrent.store(0); firstPlaybackState.store(1,std::memory_order_release);
          log("play-start",firstPlaybackCount);
        } else log("no-recording",0);
      }
      previousCombo=combo;
      if (recording) {
        if (std::chrono::steady_clock::now()-started>=std::chrono::seconds(30)) finish("time-limit");
        else if (firstPlaybackCount>=1800) finish("sample-limit");
        else firstPlaybackSamples[firstPlaybackCount++]=(held.u32 & 0x20u)?0:held.u32;
      }
      if (firstPlaybackState.load(std::memory_order_acquire)==1) {
        if (opponentToggleTest.load(std::memory_order_relaxed)) {
          firstPlaybackState.store(0,std::memory_order_release); log("play-cancelled",firstPlaybackPosition);
        } else if (firstPlaybackPosition<firstPlaybackCount) {
          firstPlaybackCurrent.store(firstPlaybackSamples[firstPlaybackPosition++],std::memory_order_relaxed);
        } else {
          firstPlaybackState.store(2,std::memory_order_release); log("play-complete",firstPlaybackPosition);
        }
      }
    }
  } else {
'''
 block=cycle+original+'  }\n'+save+base64.b64encode(original.encode()).decode()+'\n'+end
 out=s[:i]+block+s[j:]
backup=f.with_name(f.name+'.before-record-cycle-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));shutil.copy2(f,backup);f.write_text(out,encoding='utf-8',newline='\n');print('Updated:',f);print('Backup:',backup);print('Build and package.')
