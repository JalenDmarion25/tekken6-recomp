#!/usr/bin/env python3
"""Add a reversible opt-in trace of practice menu values and context."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--remove',action='store_true');a=p.parse_args();f=a.root/'src/tekken6_quick_select_apply.inc';s=f.read_text(encoding='utf-8-sig')
begin=' // BEGIN DUMMY SETTING TRACE V1\n';end=' // END DUMMY SETTING TRACE V1\n'
needle=' if(active())return;\n current={read(b,c+356),read(b,c+360),read(b,c+352)};'
block=''' // BEGIN DUMMY SETTING TRACE V1
 if (const char* path=std::getenv("TEKKEN6_DUMMY_SETTING_TRACE")) {
  if (*path) {
   static std::FILE* trace=std::fopen(path,"w");
   static unsigned snapshot=0;
   if(trace && snapshot<12) {
    std::fprintf(trace,"SNAPSHOT %u context=%08X records=%08X\\n",++snapshot,c,records);
    for(uint32_t i=0;i<496;++i)
     std::fprintf(trace,"record %u value=%u\\n",i,read(b,records+i*96+80));
    for(uint32_t offset=0;offset<420;offset+=4)
     std::fprintf(trace,"context +%03X = %08X\\n",offset,read(b,c+offset));
    std::fflush(trace);
   }
  }
 }
 // END DUMMY SETTING TRACE V1
'''
if a.remove:
 if s.count(begin)!=1 or s.count(end)!=1:raise SystemExit('Trace markers missing or inconsistent; no changes made.')
 i=s.index(begin);j=s.index(end,i)+len(end);out=s[:i]+s[j:]
else:
 if begin in s or end in s:raise SystemExit('Diagnostic already installed or partial installation; no changes made.')
 if s.count(needle)!=1 or '#include <cstdlib>' not in s:raise SystemExit('Unexpected source layout; no changes made.')
 out=s.replace(needle,' if(active())return;\n'+block+' current={read(b,c+356),read(b,c+360),read(b,c+352)};',1)
backup=f.with_name(f.name+'.before-dummy-trace-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));shutil.copy2(f,backup);f.write_text(out,encoding='utf-8',newline='\n');print('Updated:',f);print('Backup:',backup);print('Build and package before testing.')
