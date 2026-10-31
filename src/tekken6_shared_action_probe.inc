#pragma once
#include <array>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include "tekken6_bulk_command_snapshot.inc"
namespace tekken_shared_probe {
// These are observations, not an asserted universal readiness predicate.
struct Log {
 std::mutex mutex;std::FILE* file=nullptr;unsigned count=0;
 uint32_t owner=0;std::array<uint32_t,72> previous[3][2]{};
 bool seen[3][2]{};
 ~Log(){if(file)std::fclose(file);}
};
inline Log log;
inline bool Pointer(uint32_t p,unsigned size){return p>=0x80000000u && p<=0xC0000000u-size && !(p&3u);}
inline void Capture(unsigned stage,uint32_t actor,uint32_t selected) {
 static const bool enabled=[](){const char* f=std::getenv("TEKKEN6_TRACE_SHARED_ACTION");return f && !std::strcmp(f,"1");}();
 if(!enabled || stage>=3 || (actor!=0x82900C00u && actor!=0x82901840u))return;
 const uint32_t owner=practiceRageOwner.load(std::memory_order_acquire);if(!owner)return;
 auto* rt=rex::Runtime::instance();const auto* b=rt?rt->virtual_membase():nullptr;if(!b)return;
 std::lock_guard<std::mutex> lock(log.mutex);
 if(stage==1)tekken_bulk_snapshot::Capture(b,actor);
 if(log.count>=12000)return;
 if(log.owner!=owner){log.owner=owner;for(auto& s:log.seen)for(auto& v:s)v=false;}
 auto word=[&](uint32_t a){return uint32_t(b[a])<<24|uint32_t(b[a+1])<<16|uint32_t(b[a+2])<<8|b[a+3];};
 // Selection is native input/condition evaluation; commit-entry is reached
 // only after the executor's queue/timing branch. Neither implies idle.
 const unsigned offsets[]={0x78,0xC4,0xDC,0x108,0x10C,0x19C,0x1A8,0x1AC,0x1C0,0x1C4,0x1D0,0x1D4,0x1E8,0x214,0x60,0x3CC,0x774,0x778,0x780,0x784,0x788,0x794,0x7A4};
 std::array<uint32_t,72> data{};unsigned n=0;
 data[n++]=owner;data[n++]=actor;data[n++]=selected;
 for(unsigned i=0;i<2;++i){const uint32_t a=i?0x82901840u:0x82900C00u;
   for(unsigned off:offsets)data[n++]=word(a+off);
   data[n++]=b[a+916];data[n++]=b[a+917];
 }
 const bool valid=Pointer(selected,32);
 for(unsigned off=0;off<32;off+=4)data[n++]=valid?word(selected+off):0;
 const unsigned side=actor==0x82900C00u?0:1;
 if(log.seen[stage][side] && data==log.previous[stage][side])return;
 log.previous[stage][side]=data;log.seen[stage][side]=true;
 if(!log.file){log.file=std::fopen("practice-shared-action.txt","w");if(!log.file)return;
   std::fputs("SHARED ACTION PROBE V1\nStages: 0=native-selector-return 1=scheduler-exit 2=transition-commit-entry\n"
     "Rows: event stage; owner actor selected; P1 then P2 fields; 8 selected-rule words\n"
     "Fighter fields: 078 C4 DC 108 10C 19C 1A8 1AC 1C0 1C4 1D0 1D4 1E8 214 060 3CC 774 778 780 784 788 794 7A4 byte394 byte395\n"
     "Event numbers are NOT simulation frames. Queue and gate fields are NOT assumed readiness.\n",log.file);}
 std::fprintf(log.file,"E %u %u",++log.count,stage);
 for(unsigned i=0;i<n;++i)std::fprintf(log.file," %08X",data[i]);
 std::fputc('\n',log.file);
 if(stage==2 || log.count%64==0 || log.count==12000)std::fflush(log.file);
}
}
void ProbeTekkenNativeSelector(PPCRegister& fighter,PPCRegister& rule){tekken_shared_probe::Capture(0,fighter.u32,rule.u32);}
void ProbeTekkenNativeScheduler(PPCRegister& fighter){tekken_shared_probe::Capture(1,fighter.u32,0);}
void ProbeTekkenNativeCommit(PPCRegister& fighter){tekken_shared_probe::Capture(2,fighter.u32,0);}
