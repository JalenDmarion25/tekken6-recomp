#!/usr/bin/env python3
"""Install a reversible opt-in one-shot playback experiment."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--remove',action='store_true');a=p.parse_args();f=a.root/'src/tekken6_guest_hooks.cpp';s=f.read_text(encoding='utf-8-sig')
gb='// BEGIN FIRST PLAYBACK GLOBALS V1\n';ge='// END FIRST PLAYBACK GLOBALS V1\n';rb='  // BEGIN FIRST PLAYBACK RETURN V1\n';re='  // END FIRST PLAYBACK RETURN V1\n';tb='  // BEGIN FIRST PLAYBACK TICK V1\n';te='  // END FIRST PLAYBACK TICK V1\n';nb='  // BEGIN FIRST PLAYBACK NATIVE V1\n';ne='  // END FIRST PLAYBACK NATIVE V1\n';sb='  // BEGIN FIRST PLAYBACK SELECT V1\n';se='  // END FIRST PLAYBACK SELECT V1\n'
old_native='  if (!enabled || std::strcmp(enabled,"1") != 0 || !opponentToggleTest.load(std::memory_order_relaxed)) return;'
new_native='  if (!enabled || std::strcmp(enabled,"1") != 0) return;'
old_select='  if (!enabled || std::strcmp(enabled, "1") != 0 || !opponentToggleTest.load(std::memory_order_relaxed)) return;'
new_select='  if (!enabled || std::strcmp(enabled, "1") != 0 || (!opponentToggleTest.load(std::memory_order_relaxed) && firstPlaybackState.load(std::memory_order_acquire)!=1)) return;'
old_fighter='  if (fighter.u32 == 0x82900C00u && index.u32 == 8) opponentControlSuppressP1 = true;\n  else if (fighter.u32 == 0x82901840u && index.u32 == 9) index.u64 = 8;'
new_fighter='''  if (fighter.u32 == 0x82900C00u && index.u32 == 8 && opponentToggleTest.load(std::memory_order_relaxed)) opponentControlSuppressP1 = true;
  else if (fighter.u32 == 0x82901840u && index.u32 == 9) {
    index.u64 = 8;
    if (!opponentToggleTest.load(std::memory_order_relaxed) && firstPlaybackState.load(std::memory_order_acquire)==1) firstPlaybackTarget=true;
  }'''
def strip(x,b,e):
 if x.count(b)!=1 or x.count(e)!=1:raise SystemExit('Missing or inconsistent playback markers; no changes made.')
 i=x.index(b);return x[:i]+x[x.index(e,i)+len(e):]
if a.remove:
 if any(s.count(x)!=1 for x in [new_native,new_select,new_fighter]):raise SystemExit('Unexpected playback source; no changes made.')
 out=s
 for b,e in [(gb,ge),(rb,re),(tb,te),(nb,ne),(sb,se)]:out=strip(out,b,e)
 out=out.replace('  if (!opponentToggleTest.load(std::memory_order_relaxed) && firstPlaybackState.load(std::memory_order_acquire)!=1) return;\n','',1).replace(new_native,old_native,1).replace(new_select,old_select,1).replace(new_fighter,old_fighter,1)
else:
 if gb in s:raise SystemExit('Already installed; no changes made.')
 anchors=['// BEGIN OPPONENT CONTROL EXPERIMENT V1\n','  // END OPPONENT CONTROL RETURN V1\n','  // END RECORD CAPTURE TEST V1\n','  opponentControlSuppressP1 = false;\n',old_native,old_select,old_fighter]
 if any(s.count(x)!=1 for x in anchors) or 'BEGIN RECORD CAPTURE TEST V1' not in s:raise SystemExit('Expected capture, toggle, and native control tests required; no changes made.')
 globals='''// BEGIN FIRST PLAYBACK GLOBALS V1
// Test state: 0=not loaded, 1=playing, 2=finished, 3=load failed.
uint32_t firstPlaybackSamples[1800] = {};
unsigned firstPlaybackCount = 0;
unsigned firstPlaybackPosition = 0;
std::atomic<unsigned> firstPlaybackState{0};
std::atomic<uint32_t> firstPlaybackCurrent{0};
std::atomic<unsigned> firstPlaybackReads{0};
thread_local bool firstPlaybackTarget=false;
// END FIRST PLAYBACK GLOBALS V1
'''
 ret='''  // BEGIN FIRST PLAYBACK RETURN V1
  if (firstPlaybackTarget && firstPlaybackState.load(std::memory_order_acquire)==1 &&
      (object.u32==0x822A45CCu || object.u32==0x822A45E0u)) {
    buttons.u64=firstPlaybackCurrent.load(std::memory_order_relaxed);
    firstPlaybackReads.fetch_add(1,std::memory_order_relaxed);
  }
  // END FIRST PLAYBACK RETURN V1
'''
 tick='''  // BEGIN FIRST PLAYBACK TICK V1
  if (firstPlaybackState.load(std::memory_order_acquire)==1 &&
      !opponentToggleTest.load(std::memory_order_relaxed) && practice) {
    if (firstPlaybackPosition < firstPlaybackCount) {
      firstPlaybackCurrent.store(firstPlaybackSamples[firstPlaybackPosition++],std::memory_order_relaxed);
    } else {
      firstPlaybackState.store(2,std::memory_order_release);
      if (std::FILE *f=std::fopen("first-playback-test.txt","a")) {
        std::fprintf(f,"completed updates=%u getter_reads=%u\\n",firstPlaybackPosition,firstPlaybackReads.load());std::fclose(f);
      }
    }
  }
  // END FIRST PLAYBACK TICK V1
'''
 native='''  // BEGIN FIRST PLAYBACK NATIVE V1
  const char *play=std::getenv("TEKKEN6_TEST_FIRST_PLAYBACK");
  if (enabled && std::strcmp(enabled,"1")==0 && play && std::strcmp(play,"1")==0 &&
      !opponentToggleTest.load(std::memory_order_relaxed) && firstPlaybackState.load()==0) {
    std::FILE *src=std::fopen("recording-first-test.txt","r");
    unsigned n=0; long long elapsed=0; char reason[80]={}; bool ok=false;
    if(src) {
      if(std::fscanf(src,"reason=%79s samples=%u elapsed_ms=%lld",reason,&n,&elapsed)==3 && n>0 && n<=1800) {
        ok=true; for(unsigned i=0;i<n;++i) {unsigned index=0,value=0; if(std::fscanf(src,"%u %x",&index,&value)!=2 || index!=i){ok=false;break;} firstPlaybackSamples[i]=value;}
      }
      std::fclose(src);
    }
    if (std::FILE *f=std::fopen("first-playback-test.txt","w")) {std::fprintf(f,"load=%s samples=%u\\n",ok?"ok":"failed",ok?n:0);std::fclose(f);}
    if(ok){firstPlaybackCount=n;firstPlaybackPosition=0;firstPlaybackCurrent.store(0);firstPlaybackState.store(1,std::memory_order_release);}
    else firstPlaybackState.store(3,std::memory_order_release);
  }
  // END FIRST PLAYBACK NATIVE V1
'''
 # Native loading is inserted only into NativeDummyControlTest, not CapturePracticeHeld.
 na='  const char *enabled=std::getenv("TEKKEN6_TEST_OPPONENT_CONTROL");\n  if (!enabled || std::strcmp(enabled,"1") != 0 || !opponentToggleTest.load(std::memory_order_relaxed)) return;'
 assert s.count(na)==1
 out=s.replace(anchors[0],globals+anchors[0],1).replace('  // END OPPONENT CONTROL RETURN V1\n','  // END OPPONENT CONTROL RETURN V1\n'+ret,1).replace('  // END RECORD CAPTURE TEST V1\n','  // END RECORD CAPTURE TEST V1\n'+tick,1)
 out=out.replace(na,'  const char *enabled=std::getenv("TEKKEN6_TEST_OPPONENT_CONTROL");\n'+new_native,1)
 native_anchor='  if (!c || owner.u32!=c || read(b,c)!=0x8207D3E4u || active()) return;\n'
 if out.count(native_anchor)!=1:raise SystemExit('Unexpected native guard; no changes made.')
 out=out.replace(native_anchor,native_anchor+native+'  if (!opponentToggleTest.load(std::memory_order_relaxed) && firstPlaybackState.load(std::memory_order_acquire)!=1) return;\n',1)
 out=out.replace('  opponentControlSuppressP1 = false;\n','  opponentControlSuppressP1 = false;\n'+sb+'  firstPlaybackTarget=false;\n'+se,1)
 out=out.replace(old_select,new_select,1).replace(old_fighter,new_fighter,1)
backup=f.with_name(f.name+'.before-first-playback-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));shutil.copy2(f,backup);f.write_text(out,encoding='utf-8',newline='\n');print('Updated:',f);print('Backup:',backup);print('Build and package.')
