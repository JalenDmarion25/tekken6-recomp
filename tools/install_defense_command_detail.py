#!/usr/bin/env python3
"""Extend the opt-in defensive-command trace with selected-state snapshots."""
from pathlib import Path
from datetime import datetime
import argparse, shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--remove',action='store_true');a=p.parse_args();f=a.root/'src/tekken6_quick_select_trace.inc';s=f.read_text(encoding='utf-8-sig')
old='  if(ctx) dump(f,base,"practice-context",ctx,420);\n'
b='  // BEGIN DEFENSE COMMAND DETAIL V2\n';e='  // END DEFENSE COMMAND DETAIL V2\n'
new='''  // BEGIN DEFENSE COMMAND DETAIL V2
  if(ctx) {
    dump(f,base,"practice-context",ctx,420);
    // These are candidate guest pointers observed in practice-context snapshots.
    const uint32_t offsets[]={0xB8u,0xC4u,0x184u,0x18Cu};
    for(uint32_t offset:offsets) {
      const uint32_t candidate=read(base,ctx+offset);
      // Only inspect aligned addresses in the observed SystemHeap range.
      if(candidate>=0xA0000000u && candidate<=0xBFFFFF00u && !(candidate&3)) {
        char label[40];std::snprintf(label,sizeof(label),"context-pointer-%03X",offset);
        dump(f,base,label,candidate,256);
      }
    }
  }
  if(span(object,4)) {
    const uint32_t vt=read(base,object);
    if(span(vt,576)) std::fprintf(f,"apply-callback-386=%08X\\n",read(base,vt+572));
  }
  // END DEFENSE COMMAND DETAIL V2
'''
if a.remove:
 if s.count(b)!=1 or s.count(e)!=1:raise SystemExit('Detail trace missing or inconsistent; no changes made.')
 i=s.index(b);out=s[:i]+old+s[s.index(e,i)+len(e):]
else:
 if b in s:raise SystemExit('Detail trace already installed; no changes made.')
 if 'BEGIN DEFENSE COMMAND TRACE V1' not in s or s.count(old)!=1:raise SystemExit('Original defense command trace is required; no changes made.')
 out=s.replace(old,new,1)
backup=f.with_name(f.name+'.before-defense-detail-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));shutil.copy2(f,backup);f.write_text(out,encoding='utf-8',newline='\n');print('Updated:',f);print('Backup:',backup);print('Rebuild and package.')
