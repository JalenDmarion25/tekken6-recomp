#include <atomic>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <cassert>
#include <sys/mman.h>
union PPCRegister {uint64_t u64;uint32_t u32;};
std::atomic<uint32_t> practiceRageOwner{1};uint8_t* memory;
namespace rex {struct Runtime{static Runtime* instance(){static Runtime r;return &r;}uint8_t* virtual_membase(){return memory;}};}
#include "../src/tekken6_shared_action_probe.inc"
int main(){
 memory=(uint8_t*)mmap(nullptr,0xC0000000ULL,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_NORESERVE,-1,0);assert(memory!=MAP_FAILED);
 setenv("TEKKEN6_TRACE_SHARED_ACTION","1",1);
 setenv("TEKKEN6_SNAPSHOT_COMMANDS","1",1);
 auto w=[&](uint32_t a,uint32_t v){for(int j=3;j>=0;--j){memory[a+j]=v&255;v>>=8;}};
 const uint32_t root=0xA1000000,table=0xA1001000;
 w(0x82900C00+128,root);w(0x82900C00+256,root);w(root+460,table);w(root+464,3);
 for(unsigned i=0;i<3;++i){w(table+i*88,0x8200ED68);w(table+i*88+20,root+0x2000+i*32);w(root+0x2000+i*32,0x8000);}

 PPCRegister p{0x1234000082900C00ULL},r{0x56780000A0000000ULL};const auto originalP=p.u64,originalR=r.u64;
 uint8_t a[2048],b[2048],rule[32];memcpy(a,memory+0x82900C00,2048);memcpy(b,memory+0x82901840,2048);memcpy(rule,memory+0xA0000000,32);
 ProbeTekkenNativeSelector(p,r);assert(tekken_shared_probe::log.count==1);
 ProbeTekkenNativeSelector(p,r);assert(tekken_shared_probe::log.count==1);
 ProbeTekkenNativeScheduler(p);ProbeTekkenNativeCommit(p);assert(tekken_shared_probe::log.count==3);
 assert(p.u64==originalP && r.u64==originalR);
 assert(!memcmp(a,memory+0x82900C00,2048) && !memcmp(b,memory+0x82901840,2048) && !memcmp(rule,memory+0xA0000000,32));
 p.u64=1;ProbeTekkenNativeScheduler(p);assert(tekken_shared_probe::log.count==3);
 p.u64=0x82901840;practiceRageOwner=0;ProbeTekkenNativeScheduler(p);assert(tekken_shared_probe::log.count==3);
 practiceRageOwner=2;ProbeTekkenNativeScheduler(p);assert(tekken_shared_probe::log.count==4);
 auto* captured=std::fopen("practice-command-snapshot.txt","r");assert(captured);
 char capturedText[20000]={};std::fread(capturedText,1,sizeof(capturedText)-1,captured);std::fclose(captured);
 assert(std::strstr(capturedText,"count=3") && std::strstr(capturedText,"B A1001000 88") && std::strstr(capturedText,"B A10010B0 88") && std::strstr(capturedText,"cap=0"));
 tekken_shared_probe::log.count=12000;ProbeTekkenNativeCommit(p);assert(tekken_shared_probe::log.count==12000);
}
