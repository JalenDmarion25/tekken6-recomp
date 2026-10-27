#!/usr/bin/env python3
"""Extend the existing settings trace with fighter memory snapshots."""
import argparse,shutil
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--remove',action='store_true');a=p.parse_args();f=a.root/'src/tekken6_quick_select_apply.inc';s=f.read_text(encoding='utf-8-sig')
begin='    // BEGIN LIVE DUMMY TRACE V1\n';end='    // END LIVE DUMMY TRACE V1\n'
needle='    for(uint32_t offset=0;offset<420;offset+=4)\n'
block='''    // BEGIN LIVE DUMMY TRACE V1
    // Read the observed P1 and P2 fighter blocks for comparison only.
    for(uint32_t side=0;side<2;++side) {
     const uint32_t fighter=side?0x82901840u:0x82900C00u;
     for(uint32_t offset=0;offset<0xC00;offset+=4)
      std::fprintf(trace,"fighter %u +%03X = %08X\\n",side,offset,read(b,fighter+offset));
    }
    // END LIVE DUMMY TRACE V1
'''
if a.remove:
 if s.count(begin)!=1 or s.count(end)!=1:raise SystemExit('Markers missing; no changes made.')
 i=s.index(begin);j=s.index(end,i)+len(end);out=s[:i]+s[j:]
else:
 if begin in s or end in s:raise SystemExit('Trace already installed or partially installed; no changes made.')
 if s.count(needle)!=1 or 'BEGIN DUMMY SETTING TRACE V1' not in s:raise SystemExit('Existing dummy-setting diagnostic required; no changes made.')
 out=s.replace(needle,block+needle,1)
backup=f.with_name(f.name+'.before-live-dummy-trace-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));shutil.copy2(f,backup);f.write_text(out,encoding='utf-8',newline='\n');print('Updated:',f);print('Backup:',backup);print('Build and package before testing.')
