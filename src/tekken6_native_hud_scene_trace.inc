// Full UI scene snapshots after native animation updates. Read-only and bounded.
#pragma once
namespace native_hud_scene_trace {
uint32_t Read(const uint8_t* p,uint32_t a){return uint32_t(p[a])<<24|uint32_t(p[a+1])<<16|uint32_t(p[a+2])<<8|p[a+3];}
bool Valid(uint32_t a){return a>=0x10000u && a<=0xBFFFFE00u && !(a&3u);}
}
void TraceNativePracticeHudScene(PPCRegister& scene) {
 using namespace native_hud_scene_trace;
 const char* flag=std::getenv("TEKKEN6_TRACE_NATIVE_HUD_SCENES");
 if(!flag || std::strcmp(flag,"1") || !practiceRageOwner.load(std::memory_order_acquire) || !Valid(scene.u32))return;
 auto* r=rex::Runtime::instance();auto* p=r?r->virtual_membase():nullptr;if(!p)return;
 static std::mutex mutex;std::lock_guard<std::mutex> lock(mutex);
 static std::map<uint64_t,unsigned> counts;
 const uint32_t root=Read(p,scene.u32+244);if(!Valid(root))return;
 const uint64_t key=uint64_t(scene.u32)<<32|root;
 if(counts.size()>=32 && !counts.count(key))return;
 unsigned& calls=counts[key];if(calls>=600)return;
 ++calls;if(calls!=1 && calls!=60 && calls!=600)return;
 static std::FILE* f=std::fopen("native-practice-hud-scenes.txt","w");if(!f)return;
 std::fprintf(f,"SCENE %08X root=%08X call=%u\n",scene.u32,root,calls);
 uint32_t pending[1024];unsigned queued=1,total=0;pending[0]=root;
 std::map<uint32_t,bool> visited;
 while(queued && total<512) {
   uint32_t n=pending[--queued];if(!Valid(n) || visited.count(n))continue;
   visited[n]=true;++total;
   std::fprintf(f,"NODE %08X id=%u parent=%08X child=%08X next=%08X\n",n,Read(p,n+208),Read(p,n+20),Read(p,n+232),Read(p,n+24));
   // Metadata and transform values include inactive nodes as well as visible ones.
   for(unsigned off=0;off<512;off+=4) {
     uint32_t word=Read(p,n+off);float value;std::memcpy(&value,&word,4);
     std::fprintf(f,"+%03X %08X f=%.7g\n",off,word,double(value));
   }
   if(queued<1023)pending[queued++]=Read(p,n+24);
   if(queued<1023)pending[queued++]=Read(p,n+232);
 }
 std::fprintf(f,"END nodes=%u capped=%u\n",total,unsigned(queued!=0));std::fflush(f);
}
