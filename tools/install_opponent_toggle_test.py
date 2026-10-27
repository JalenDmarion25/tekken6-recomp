#!/usr/bin/env python3
"""Make the existing opt-in opponent-control test toggleable in practice."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--remove',action='store_true');a=p.parse_args();f=a.root/'src/tekken6_guest_hooks.cpp';s=f.read_text(encoding='utf-8-sig')
b='// BEGIN OPPONENT TOGGLE TEST V1\n';e='// END OPPONENT TOGGLE TEST V1\n';bs='  // BEGIN OPPONENT TOGGLE INPUT V1\n';es='  // END OPPONENT TOGGLE INPUT V1\n'
old1='if (!enabled || std::strcmp(enabled, "1") != 0) return;';new1='if (!enabled || std::strcmp(enabled, "1") != 0 || !opponentToggleTest.load(std::memory_order_relaxed)) return;'
old2='if (!enabled || std::strcmp(enabled,"1") != 0) return;';new2='if (!enabled || std::strcmp(enabled,"1") != 0 || !opponentToggleTest.load(std::memory_order_relaxed)) return;'
def strip(x,start,end):
 if x.count(start)!=1 or x.count(end)!=1:raise SystemExit('Missing or inconsistent markers; no changes made.')
 i=x.index(start);return x[:i]+x[x.index(end,i)+len(end):]
if a.remove:
 if s.count(new1)!=1 or s.count(new2)!=1:raise SystemExit('Cannot find both modified guards; no changes made.')
 out=strip(strip(s,bs,es),b,e).replace(new1,old1,1).replace(new2,old2,1)
else:
 if b in s or bs in s:raise SystemExit('Already installed or partial installation; no changes made.')
 anchor='void CapturePracticeHeld(PPCRegister &held)\n{\n  practiceHeld.store(held.u32, std::memory_order_relaxed);\n'
 if s.count(anchor)!=1 or s.count(old1)!=1 or s.count(old2)!=1 or 'BEGIN NATIVE DUMMY CONTROL TEST V1' not in s:raise SystemExit('Expected native and opponent control tests not found; no changes made.')
 decl=b+'std::atomic<bool> opponentToggleTest{false};\n'+e
 block='''  // BEGIN OPPONENT TOGGLE INPUT V1
  const char *enabled=std::getenv("TEKKEN6_TEST_OPPONENT_CONTROL");
  const bool practice=practiceRageOwner.load(std::memory_order_acquire)!=0;
  static bool wasHeld=false;
  if (!enabled || std::strcmp(enabled,"1")!=0 || !practice) {
    wasHeld=false;
    opponentToggleTest.store(false,std::memory_order_relaxed);
  } else {
    const bool heldCombo=(held.u32 & 0x4020u)==0x4020u;
    if (heldCombo && !wasHeld) {
      const bool next=!opponentToggleTest.load(std::memory_order_relaxed);
      opponentToggleTest.store(next,std::memory_order_relaxed);
      static std::FILE *f=std::fopen("opponent-toggle-test.txt","w");
      if(f){std::fprintf(f,"toggle=%s held=%08X\\n",next?"on":"off",held.u32);std::fflush(f);}
    }
    wasHeld=heldCombo;
  }
  // END OPPONENT TOGGLE INPUT V1
'''
 out=s.replace(anchor,decl+anchor+block,1).replace(old1,new1,1).replace(old2,new2,1)
backup=f.with_name(f.name+'.before-opponent-toggle-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));shutil.copy2(f,backup);f.write_text(out,encoding='utf-8',newline='\n');print('Updated:',f);print('Backup:',backup);print('Build and package before testing.')
