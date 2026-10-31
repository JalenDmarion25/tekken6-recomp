// NATIVE PRACTICE HUD TRACE V1: bounded, opt-in; registers and memory untouched.
#pragma once
void TraceNativePracticeHud(PPCRegister& group,PPCRegister& format,
 PPCRegister& a,PPCRegister& b,PPCRegister& c,PPCRegister& d,
 PPCRegister& e,PPCRegister& f,PPCRegister& caller) {
 const char* flag=std::getenv("TEKKEN6_TRACE_NATIVE_HUD");
 if(!flag || std::strcmp(flag,"1")!=0 || !practiceRageOwner.load(std::memory_order_acquire))return;
 auto* runtime=rex::Runtime::instance();auto* memory=runtime?runtime->virtual_membase():nullptr;
 if(!memory || !format.u32 || format.u32>0xFFFFFC00u)return;
 static std::mutex mutex;std::lock_guard<std::mutex> lock(mutex);
 static std::map<uint64_t,unsigned> seen;static unsigned total=0;
 if(total>=384)return;
 uint64_t key=uint64_t(caller.u32)<<32|format.u32;
 // NATIVE HUD OBJECT TRACE V2: distinguish combo, total damage and counter labels.
 if(caller.u32==0x824623ECu || caller.u32==0x8246247Cu || caller.u32==0x82462634u)
   key^=uint64_t(f.u32)<<1;
 if(seen.size()>=128 && !seen.count(key))return;
 if(seen[key]>=3)return;
 ++seen[key];++total;
 static std::FILE* log=std::fopen("native-practice-hud-trace.txt","w");
 if(!log)return;
 std::fprintf(log,"call=%08X group=%u fmt=%08X sample=%u args=%08X,%08X,%08X,%08X,%08X,%08X\nformat=",
 caller.u32,group.u32,format.u32,seen[key],a.u32,b.u32,c.u32,d.u32,e.u32,f.u32);
 for(unsigned i=0;i<512;++i) {
   const unsigned ch=memory[format.u32+i];if(!ch)break;
   if(ch>=32 && ch<127)std::fputc(int(ch),log);
   else std::fprintf(log,"<%02X>",ch);
 }
 std::fputc('\n',log);std::fflush(log);
}
