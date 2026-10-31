#pragma once
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
namespace tekken_stance_gate {
void Capture(const uint8_t* b,uint32_t owner,uint32_t held) {
 const char* flag=std::getenv("TEKKEN6_TRACE_STANCE_GATE");
 if(!b || !owner || !flag || std::strcmp(flag,"1"))return;
 static std::mutex mutex;std::lock_guard<std::mutex> lock(mutex);
 static uint32_t previousAction=0,previousCommand[2]={},previousOwner=0;
 static unsigned caseId=0,frame=0,total=0;static bool active=false;
 static std::FILE* f=nullptr;
 if(total>=1600)return;
 auto word=[&](uint32_t a){return uint32_t(b[a])<<24|uint32_t(b[a+1])<<16|uint32_t(b[a+2])<<8|b[a+3];};
 auto valid=[](uint32_t a,unsigned bytes){return a>=0x90000000u && a<=0xC0000000u-bytes;};
 const uint32_t action=word(0x82900C00u+0x10C),state=word(0x82900C00u+0x1C4);
 if(previousOwner!=owner){active=false;previousAction=0;previousCommand[0]=previousCommand[1]=0;previousOwner=owner;}
 // This is a capture filter for the tested neutral u+4 path, not a timing lookup.
 if(action==0xC842u && previousAction!=action) {
   active=true;frame=0;++caseId;previousCommand[0]=previousCommand[1]=0;
 }
 previousAction=action;if(!active)return;
 if(!f){f=std::fopen("practice-stance-gate-trace.txt","w");if(!f)return;
   std::fputs("STANCE GATE V1: read-only input-hook samples, not assumed simulation frames.\nFields: action animation segment recovery attack action_state state reaction_kind reaction_sequence damage_dealt damage_taken health command flags254 flags260\nLinked metadata records are bounded raw words; their meaning is not yet asserted.\n",f);}
 const auto us=std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
 std::fprintf(f,"case=%u sample=%u host_us=%lld held=%08X\n",caseId,++frame,static_cast<long long>(us),held);++total;
 const unsigned fields[]={0x10C,0xC4,0xDC,0x1E8,0x1AC,0x1C0,0x1C4,0x214,0x1A8,0x1D0,0x1D4,0x60,0x108,0x254,0x260};
 for(unsigned side=0;side<2;++side) {
   const uint32_t a=side?0x82901840u:0x82900C00u;
   std::fprintf(f,"P%u",side+1);for(unsigned off:fields)std::fprintf(f," %08X",word(a+off));std::fputc('\n',f);
   const uint32_t command=word(a+0x108);
   if(command!=previousCommand[side] && valid(command,88)) {
     std::fprintf(f,"COMMAND side=%u address=%08X",side+1,command);
     for(unsigned off=0;off<88;off+=4)std::fprintf(f," %08X",word(command+off));
     std::fputc('\n',f);
     const unsigned links[]={20,32,52,56};
     for(unsigned off:links){const uint32_t target=word(command+off);if(!valid(target,160))continue;
       std::fprintf(f,"LINK side=%u offset=%u address=%08X",side+1,off,target);
       for(unsigned j=0;j<160;j+=4)std::fprintf(f," %08X",word(target+j));
       std::fputc('\n',f);
     }
   }
   previousCommand[side]=command;
 }
 if(frame%30==0)std::fflush(f);
 if(frame>=180 || (action!=0xC842u && state==128 && word(0x82900C00u+0xC4)>=6)) {
   active=false;std::fputs("CASE END\n",f);std::fflush(f);
 }
}
}
