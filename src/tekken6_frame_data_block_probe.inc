#pragma once
// Contact classifier correction: 0x1D0/0x1D4 participate in damage processing.
// Neither their numeric values nor the pilot's reaction states prove a block.
namespace tekken_block_probe {
std::atomic<uint64_t> result{0};
std::mutex mutex;
uint32_t owner=0,damage[2]={},attack[2]={};
}
bool TekkenFrameDataPracticeActive(){return practiceRageOwner.load(std::memory_order_acquire)!=0;}
uint64_t TekkenFrameDataResult(){return tekken_block_probe::result.load(std::memory_order_acquire);}
void CaptureTekkenFrameDataCandidates(uint32_t held) {
 using namespace tekken_block_probe;
 std::lock_guard<std::mutex> lock(mutex);
 const uint32_t currentOwner=practiceRageOwner.load(std::memory_order_acquire);
 if(owner!=currentOwner){owner=currentOwner;damage[0]=damage[1]=attack[0]=attack[1]=0;result.store(0,std::memory_order_release);}
 if(!currentOwner)return;
 auto* runtime=rex::Runtime::instance();auto* b=runtime?runtime->virtual_membase():nullptr;if(!b)return;
 auto word=[&](uint32_t a){return uint32_t(b[a])<<24|uint32_t(b[a+1])<<16|uint32_t(b[a+2])<<8|b[a+3];};
 const uint32_t bases[]={0x82900C00u,0x82901840u};
 bool attacking=false;
 for(unsigned i=0;i<2;++i) {
   const auto a=bases[i];const uint32_t nowAttack=word(a+0x1AC),nowDamage=word(a+0x1D0),animation=word(a+0xC4);
   attacking|=nowAttack!=0;
   if(nowAttack && !attack[i])result.store(0,std::memory_order_release);
   if(nowAttack && nowDamage && !damage[i] && animation>0 && animation<=120)
     result.store(animation,std::memory_order_release); // Startup on observed damaging contact only.
   damage[i]=nowDamage;attack[i]=nowAttack;
 }
 // No path sets the block-valid bit. ON BLOCK remains -- until guard is identified.
 const char* enabled=std::getenv("TEKKEN6_TRACE_BLOCK_RESPONSE");
 if(!enabled || std::strcmp(enabled,"1"))return;
 static bool started=false;static unsigned count=0;
 if(!started){if(!attacking)return;started=true;}
 if(count>=3000)return;
 static std::FILE* f=std::fopen("practice-block-response.txt","w");if(!f)return;
 if(!count)std::fprintf(f,"BLOCK RESPONSE V1: starts on ordinary attack, no shortcut.\nEach fighter: 256 big-endian words at offsets 000..3FC, step 4.\n1D0/1D4 are damage-related; former pilot block labels are invalid. Samples are not confirmed simulation frames.\n");
 const auto us=std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
 std::fprintf(f,"sample=%u host_us=%lld held=%08X owner=%08X\n",++count,static_cast<long long>(us),held,currentOwner);
 for(uint32_t a:bases){std::fprintf(f,"%08X",a);for(unsigned off=0;off<0x400;off+=4)std::fprintf(f," %08X",word(a+off));std::fputc('\n',f);}
 if(count%30==0 || count==3000)std::fflush(f);
}
