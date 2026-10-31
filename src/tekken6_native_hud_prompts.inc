// Native practice prompt anchors, after the scene's animation update.
#pragma once
namespace native_practice_prompt_layout {
bool Valid(uint32_t a){return a>=0x10000u && a<=0xBFFFFE00u && !(a&3u);}
uint32_t Read(const uint8_t* p,uint32_t a){return uint32_t(p[a])<<24|uint32_t(p[a+1])<<16|uint32_t(p[a+2])<<8|p[a+3];}
void Write(uint8_t* p,uint32_t a,uint32_t v){p[a]=uint8_t(v>>24);p[a+1]=uint8_t(v>>16);p[a+2]=uint8_t(v>>8);p[a+3]=uint8_t(v);}
bool Position(const uint8_t* p,uint32_t n,uint32_t x,uint32_t y){return Read(p,n+320)==x && Read(p,n+324)==y;}
bool Move(uint8_t* p,uint32_t scene) {
 if(!p || !Valid(scene))return false;
 const uint32_t root=Read(p,scene+244);
 if(!Valid(root) || Read(p,root)!=0x820A0514u || Read(p,root+208)!=0u || Read(p,root+12)!=scene)return false;
 uint32_t left=0,right=0;bool leftPanel=false,rightPanel=false;
 uint32_t node=Read(p,root+232);unsigned count=0;
 for(;node && count<64;++count) {
   if(!Valid(node) || Read(p,node)!=0x820A0514u || Read(p,node+12)!=scene || Read(p,node+20)!=root)return false;
   const uint32_t id=Read(p,node+208);
   if(id==8u && Position(p,node,0x43700000u,0x43B40000u))leftPanel=true; // 240,360
   if(id==9u && Position(p,node,0x44820000u,0x43B40000u))rightPanel=true; // 1040,360
   if(id==28u){if(left)return false;left=node;}
   if(id==29u){if(right)return false;right=node;}
   node=Read(p,node+24);
 }
 // Match the complete pair in the practice helper scene, not heap addresses.
 if(node || count<28 || !leftPanel || !rightPanel || !left || !right)return false;
 if(Read(p,left+196)!=0x1C2u || Read(p,right+196)!=0x1C2u)return false;
 const uint32_t nested=Read(p,left+268);
 if(!Valid(nested) || nested!=Read(p,right+268))return false;
 if(Read(p,left+320)!=0x43C00000u || Read(p,right+320)!=0x445C0000u)return false; // 384,880
 const uint32_t ly=Read(p,left+324),ry=Read(p,right+324);
 if((ly!=0x44070000u && ly!=0x44250000u) || (ry!=0x44070000u && ry!=0x44250000u))return false;
 // Absolute assignment avoids drift when native updates leave static nodes alone.
 Write(p,left+324,0x44250000u);Write(p,right+324,0x44250000u); // 660
 return true;
}
}
void RepositionNativePracticeHudPrompts(PPCRegister& scene) {
 if(!practiceRageOwner.load(std::memory_order_acquire))return;
 auto* r=rex::Runtime::instance();auto* p=r?r->virtual_membase():nullptr;
 if(!native_practice_prompt_layout::Move(p,scene.u32))return;
 static std::atomic<bool> logged{false};
 if(!logged.exchange(true,std::memory_order_relaxed)) {
   if(auto* f=std::fopen("native-practice-hud-layout.txt","w")) {
     std::fprintf(f,"Matched native practice prompt pair: Position Reset and Start/Stop Y540 -> Y660.\n");
     std::fclose(f);
   }
 }
}
