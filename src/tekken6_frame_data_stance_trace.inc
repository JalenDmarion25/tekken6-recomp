#pragma once
#include <array>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
namespace tekken_stance_trace {
struct Snapshot {int64_t us;uint32_t held,owner;uint32_t words[2][320];};
void Capture(const uint8_t* b,uint32_t owner,uint32_t held) {
 const char* flag=std::getenv("TEKKEN6_TRACE_STANCE_FRAMES");
 if(!flag || std::strcmp(flag,"1") || !b || !owner)return;
 static std::mutex mutex;std::lock_guard<std::mutex> lock(mutex);
 static std::array<Snapshot,120> pre{};
 static unsigned head=0,available=0,post=0,printed=0;
 static uint32_t traceOwner=0;static bool started=false,stopped=false;
 static std::FILE* f=nullptr;
 if(stopped)return;
 if(traceOwner!=owner) {
   if(started){stopped=true;if(f){std::fputs("CAPTURE STOPPED: practice owner changed\n",f);std::fflush(f);}return;}
   traceOwner=owner;head=available=0;
 }
 if(post>=3600)return;
 Snapshot now{};now.owner=owner;now.held=held;
 now.us=std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
 auto word=[&](uint32_t a){return uint32_t(b[a])<<24|uint32_t(b[a+1])<<16|uint32_t(b[a+2])<<8|b[a+3];};
 for(unsigned i=0;i<2;++i){const uint32_t a=i?0x82901840u:0x82900C00u;
   for(unsigned j=0;j<320;++j){const unsigned off=j<256?j*4:0x700+(j-256)*4;now.words[i][j]=word(a+off);}
 }
 auto write=[&](const Snapshot& s,bool beforeAttack) {
   std::fprintf(f,"sample=%u host_us=%lld held=%08X owner=%08X preroll=%u\n",++printed,static_cast<long long>(s.us),s.held,s.owner,unsigned(beforeAttack));
   for(unsigned i=0;i<2;++i){std::fprintf(f,"%08X",i?0x82901840u:0x82900C00u);
     for(unsigned j=0;j<320;++j)std::fprintf(f," %08X",s.words[i][j]);
     std::fputc('\n',f);}
 };
 if(!started) {
   const bool attack=now.words[0][0x1AC/4] || now.words[1][0x1AC/4];
   if(!attack){pre[head]=now;head=(head+1)%120;if(available<120)++available;return;}
   f=std::fopen("practice-stance-frames.txt","w");if(!f){stopped=true;return;}
   std::fputs("STANCE/STRING CAPTURE V1: input-hook samples, not confirmed simulation frames.\nEach fighter: 320 big-endian words. First 256: offsets 000..3FC. Last 64: offsets 700..7FC.\nUp to 120 pre-attack samples, followed by at most 3600 samples. No controller shortcut or guest writes.\n",f);
   started=true;
   for(unsigned j=0;j<available;++j)write(pre[(head+120-available+j)%120],true);
 }
 write(now,false);++post;
 if(post%30==0 || post==3600)std::fflush(f);
}
}
