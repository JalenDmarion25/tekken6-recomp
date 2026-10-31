#pragma once
#include "tekken6_frame_data_measure.inc"
namespace tekken_frame_live {
std::atomic<uint64_t> result{0};
tekken_frame_measure::Meter meter;
std::mutex mutex;
uint32_t owner=0;
}
bool TekkenFrameDataPracticeActive(){return practiceRageOwner.load(std::memory_order_acquire)!=0;}
uint64_t TekkenFrameDataResult(){return tekken_frame_live::result.load(std::memory_order_acquire);}
void CaptureTekkenFrameDataCandidates(uint32_t) {
 using namespace tekken_frame_live;
 const uint32_t currentOwner=practiceRageOwner.load(std::memory_order_acquire);
 std::lock_guard<std::mutex> lock(mutex);
 if(owner!=currentOwner){owner=currentOwner;meter.Reset();result.store(0,std::memory_order_release);}
 if(!currentOwner)return;
 auto* runtime=rex::Runtime::instance();auto* b=runtime?runtime->virtual_membase():nullptr;if(!b)return;
 auto word=[&](uint32_t a){return uint32_t(b[a])<<24|uint32_t(b[a+1])<<16|uint32_t(b[a+2])<<8|b[a+3];};
 tekken_frame_measure::Sample sample{};
 for(unsigned i=0;i<2;++i){const uint32_t a=i?0x82901840u:0x82900C00u;
   sample.p[i]={word(a+0xDC),word(a+0xC4),word(a+0x1AC),word(a+0x1D0),word(a+0x1A8),word(a+0x1C4)};
 }
 if(meter.Step(sample)) {
   result.store(meter.result,std::memory_order_release);
   static unsigned logged=0;
   if(meter.result && logged++<200)if(auto* f=std::fopen("practice-frame-data-live.txt","a")){
     const unsigned startup=unsigned(meter.result&0xFFFFu);
     if(meter.result&(uint64_t(1)<<32))std::fprintf(f,"startup=%u block=%+d\n",startup,int(int16_t((meter.result>>16)&0xFFFFu)));
     else std::fprintf(f,"startup=%u block=pending-or-not-blocked\n",startup);
     std::fclose(f);
   }
 }
}
