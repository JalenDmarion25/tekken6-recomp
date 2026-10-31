// Filter the actual widget drawing path; no register or guest-memory writes.
#pragma once
namespace practice_widget_trace {
uint32_t Read(const uint8_t* p,uint32_t a){return uint32_t(p[a])<<24|uint32_t(p[a+1])<<16|uint32_t(p[a+2])<<8|p[a+3];}
unsigned Half(const uint8_t* p,uint32_t a){return unsigned(p[a])<<8|p[a+1];}
bool Valid(uint32_t a,unsigned size=128){return a>=0x10000u && a<=0xC0000000u-size;}
void Capture(unsigned kind,uint32_t object,int x,int y,int width=0,int height=0) {
 const char* flag=std::getenv("TEKKEN6_TRACE_PRACTICE_WIDGETS");
 if(!flag || std::strcmp(flag,"1") || !practiceRageOwner.load(std::memory_order_acquire))return;
 auto* runtime=rex::Runtime::instance();auto* p=runtime?runtime->virtual_membase():nullptr;
 if(!p || !Valid(object,1408))return;
 static std::mutex mutex;std::lock_guard<std::mutex> lock(mutex);
 static std::FILE* f=std::fopen("practice-widget-draw.txt","w");if(!f)return;
 static unsigned entered=0;const unsigned bit=1u<<kind;
 if(!(entered&bit)){entered|=bit;std::fprintf(f,"ACTIVE hook=%u practice=%08X (read-only widget trace)\n",kind,practiceRageOwner.load());std::fflush(f);}
 if(y<480 || y>720 || x< -128 || x>1408)return;
 if(kind>=2 && (width<160 || width>440 || height<12 || height>100 || (x>440 && x<800)))return;
 uint32_t hash=2166136261u;
 if(kind<2)for(unsigned i=0;i<192;++i)hash=(hash^p[object+1120+i])*16777619u;
 const uint64_t key=(uint64_t(object)<<32)^uint32_t(x*257+y)^uint64_t(hash)<<1^uint64_t(kind)<<60;
 static std::map<uint64_t,bool> seen;static unsigned texts=0,frames=0;
 if(seen.count(key) || (kind<2?texts>=160:frames>=96))return;
 seen[key]=true;if(kind<2)++texts;else ++frames;
 std::fprintf(f,"WIDGET hook=%u object=%08X xy=%d,%d size=%d,%d\n",kind,object,x,y,width,height);
 if(kind<2) {
   std::fputs("text-ascii=",f);
   for(unsigned i=0;i<192;++i){unsigned c=p[object+1120+i];if(c>=32 && c<127)std::fputc(c,f);else std::fprintf(f,"<%02X>",c);}
   std::fputc('\n',f);
 }
 // The widget parent chain identifies the complete frame, rather than its text alone.
 uint32_t current=object;
 for(unsigned depth=0;depth<5 && Valid(current);++depth) {
   std::fprintf(f,"parent[%u]=%08X vtable=%08X link=%08X local=%d,%d current=%d,%d size=%u,%u screen=%d,%d\n",depth,current,Read(p,current),Read(p,current+4),int(int16_t(Half(p,current+30))),int(int16_t(Half(p,current+32))),int(int16_t(Half(p,current+34))),int(int16_t(Half(p,current+36))),Half(p,current+42),Half(p,current+44),int(int16_t(Half(p,current+46))),int(int16_t(Half(p,current+48))));
   for(unsigned off=0;off<96;off+=4)std::fprintf(f,"+%02X %08X\n",off,Read(p,current+off));
   uint32_t parent=Read(p,current+4);if(!parent || parent==current)break;current=parent;
 }
 std::fflush(f);
}
}
void TracePracticeWidgetTextA(PPCRegister& object,PPCRegister& x,PPCRegister& y){practice_widget_trace::Capture(0,object.u32,x.s32,y.s32);}
void TracePracticeWidgetTextB(PPCRegister& object,PPCRegister& x,PPCRegister& y){practice_widget_trace::Capture(1,object.u32,x.s32,y.s32);}
void TracePracticeWidgetFrame(PPCRegister& object,PPCRegister& x,PPCRegister& y){
 auto* r=rex::Runtime::instance();auto* p=r?r->virtual_membase():nullptr;
 if(p && practice_widget_trace::Valid(object.u32))practice_widget_trace::Capture(2,object.u32,x.s32,y.s32,practice_widget_trace::Half(p,object.u32+42),practice_widget_trace::Half(p,object.u32+44));
}
void TracePracticeWidgetQuad(PPCRegister& object,PPCRegister& rect){
 auto* r=rex::Runtime::instance();auto* p=r?r->virtual_membase():nullptr;
 if(!p || !practice_widget_trace::Valid(rect.u32,16))return;
 const int x=int32_t(practice_widget_trace::Read(p,rect.u32)),y=int32_t(practice_widget_trace::Read(p,rect.u32+4));
 const int64_t width=int64_t(int32_t(practice_widget_trace::Read(p,rect.u32+8)))-x;
 const int64_t height=int64_t(int32_t(practice_widget_trace::Read(p,rect.u32+12)))-y;
 if(width>=160 && width<=440 && height>=12 && height<=100)practice_widget_trace::Capture(3,object.u32,x,y,int(width),int(height));
}
