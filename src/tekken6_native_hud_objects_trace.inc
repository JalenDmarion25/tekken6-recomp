// NATIVE HUD OBJECT TRACE V2: bounded UI-object and animation data; read-only.
#pragma once
namespace native_hud_objects_trace_detail {
uint32_t Read(const uint8_t* b,uint32_t a){return uint32_t(b[a])<<24|uint32_t(b[a+1])<<16|uint32_t(b[a+2])<<8|b[a+3];}
void Dump(const char* kind,uint32_t caller,uint32_t object,unsigned size) {
 const char* flag=std::getenv("TEKKEN6_TRACE_NATIVE_HUD");
 if(!flag || std::strcmp(flag,"1")!=0 || !practiceRageOwner.load(std::memory_order_acquire))return;
 if(object<0x10000u || object>0xC0000000u-size)return;
 auto* r=rex::Runtime::instance();auto* b=r?r->virtual_membase():nullptr;if(!b)return;
 static std::mutex mutex;std::lock_guard<std::mutex> lock(mutex);
 static std::map<uint64_t,unsigned> seen;static unsigned total=0;
 uint64_t key=uint64_t(caller)<<32|object;
 if(size==416)for(unsigned i=0;i<5;++i)
   key^=uint64_t(Read(b,object+12+i*40+36))*(0x9E3779B1ull+i);
 if(total>=128 || seen[key]>=2)return;
 ++seen[key];++total;
 static std::FILE* f=std::fopen("native-practice-hud-objects.txt","w");if(!f)return;
 std::fprintf(f,"%s caller=%08X object=%08X sample=%u\n",kind,caller,object,seen[key]);
 for(unsigned i=0;i<size;i+=4){uint32_t v=Read(b,object+i);float x;std::memcpy(&x,&v,4);std::fprintf(f,"+%03X %08X float=%.5g\n",i,v,double(x));}
 if(size==416)for(unsigned i=0;i<5;++i) {
   const uint32_t entry=object+12+i*40,def=Read(b,entry+36),label=Read(b,entry+8);
   std::fprintf(f,"animation=%u definition=%08X label=%08X\n",i,def,label);
   if(def>=0x10000u && def<=0xBFFFFFC0u)
     for(unsigned j=0;j<40;j+=4)std::fprintf(f,"def+%02X %08X\n",j,Read(b,def+j));
   if(label>=0x10000u && label<=0xBFFFFF80u) {
     std::fputs("label-bytes=",f);
     for(unsigned j=0;j<96;++j)std::fprintf(f,"%02X",b[label+j]);
     std::fputc('\n',f);
   }
 }
 std::fflush(f);
}
}
void TraceNativePracticeHudObject(PPCRegister& object,PPCRegister& caller){
 native_hud_objects_trace_detail::Dump("object",caller.u32,object.u32,256);
}
void TraceNativePracticeHudAnimations(PPCRegister& object,PPCRegister& caller){
 native_hud_objects_trace_detail::Dump("practice-animation",caller.u32,object.u32,416);
}
