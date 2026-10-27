#!/usr/bin/env python3
"""Temporarily test the observed opponent control fields in the existing experiment."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--remove',action='store_true');a=p.parse_args();f=a.root/'src/tekken6_guest_hooks.cpp';s=f.read_text(encoding='utf-8-sig')
begin='  // BEGIN AUTO DUMMY TEST V1\n';end='  // END AUTO DUMMY TEST V1\n'
needle='  else if (fighter.u32 == 0x82901840u && index.u32 == 9) index.u64 = 8;\n'
block='''  // BEGIN AUTO DUMMY TEST V1
  else if (fighter.u32 == 0x82901840u && index.u32 == 9) {
    // Values observed when native Training Dummy 1 is set to Controller.
    // This experiment only runs inside the existing opt-in practice guard.
    write(b, fighter.u32 + 0x290, 1);
    write(b, fighter.u32 + 0x294, 0);
    index.u64 = 8;
  }
  // END AUTO DUMMY TEST V1
'''
if a.remove:
 if s.count(begin)!=1 or s.count(end)!=1:raise SystemExit('Experiment markers missing; no changes made.')
 i=s.index(begin);j=s.index(end,i)+len(end);out=s[:i]+needle+s[j:]
else:
 if begin in s or end in s:raise SystemExit('Already installed or partial experiment; no changes made.')
 if s.count(needle)!=1 or 'BEGIN OPPONENT CONTROL IMPLEMENTATION V1' not in s:raise SystemExit('Existing opponent-control experiment required; no changes made.')
 out=s.replace(needle,block,1)
backup=f.with_name(f.name+'.before-auto-dummy-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));shutil.copy2(f,backup);f.write_text(out,encoding='utf-8',newline='\n');print('Updated:',f);print('Backup:',backup);print('Build and package before testing.')
