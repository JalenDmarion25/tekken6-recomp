// Adjust the computed anchor after command processing and local transforms, before child transforms.
#pragma once
namespace native_practice_prompt_render {
bool Move(uint8_t* p,uint32_t node) {
 using namespace native_practice_prompt_layout;
 if(!p || !Valid(node) || Read(p,node)!=0x820A0514u)return false;
 const uint32_t id=Read(p,node+208);
 if(id!=28u && id!=29u)return false;
 if(Read(p,node+196)!=0x1C2u)return false;
 const uint32_t expectedX=id==28u?0x43C00000u:0x445C0000u;
 const uint32_t y=Read(p,node+324);
 if(Read(p,node+320)!=expectedX || (y!=0x44070000u && y!=0x44250000u))return false;
 const uint32_t scene=Read(p,node+12),root=Read(p,node+20),nested=Read(p,node+268);
 if(!Valid(scene) || !Valid(root) || !Valid(nested))return false;
 if(Read(p,scene+244)!=root || Read(p,root)!=0x820A0514u || Read(p,root+208)!=0 || Read(p,root+12)!=scene)return false;
 // During hierarchy construction, the current child list may be incomplete.
 // Check the distinctive earlier panel anchors in either current or old list.
 bool leftPanel=false,rightPanel=false;
 for(unsigned list=0;list<2 && !(leftPanel && rightPanel);++list) {
   uint32_t n=Read(p,root+(list?248:232));
   for(unsigned count=0;n && count<64;++count) {
     if(!Valid(n) || Read(p,n)!=0x820A0514u || Read(p,n+12)!=scene || Read(p,n+20)!=root)break;
     uint32_t panel=Read(p,n+208);
     if(panel==8u && Position(p,n,0x43700000u,0x43B40000u))leftPanel=true;
     if(panel==9u && Position(p,n,0x44820000u,0x43B40000u))rightPanel=true;
     n=Read(p,n+24);
   }
 }
 if(!leftPanel || !rightPanel)return false;
 Write(p,node+324,0x44250000u); // absolute Y660; repeated calls cannot drift
 return true;
}
}
void RepositionNativePracticeHudPromptBeforeDraw(PPCRegister& node) {
 if(!practiceRageOwner.load(std::memory_order_acquire))return;
 auto* r=rex::Runtime::instance();auto* p=r?r->virtual_membase():nullptr;
 if(!native_practice_prompt_render::Move(p,node.u32))return;
 const uint32_t id=native_practice_prompt_layout::Read(p,node.u32+208);
 const unsigned bit=id==28u?1u:2u;
 static std::atomic<unsigned> logged{0};
 if(logged.fetch_or(bit,std::memory_order_relaxed)&bit)return;
 static std::mutex mutex;std::lock_guard<std::mutex> lock(mutex);
 static std::FILE* f=std::fopen("native-practice-hud-final-transform.txt","w");
 if(f){std::fprintf(f,"Applied prompt anchor %u at Y660 after final native transform.\n",id);std::fflush(f);}
}
