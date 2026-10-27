// Standard playable roster; choice IDs verified against 82744AA8.
#pragma once
#include <cstdint>
namespace quick_select_roster {
struct Fighter {const char* name; uint32_t id, choice; bool fixedCostume;};
constexpr Fighter fighters[]={
 {"Alisa Bosconovitch", 41, 80, false},
 {"Anna Williams", 21, 44, false},
 {"Armor King", 30, 62, false},
 {"Asuka Kazama", 24, 50, false},
 {"Baek Doo San", 26, 54, false},
 {"Bob", 34, 70, false},
 {"Bruce Irvin", 25, 52, false},
 {"Bryan Fury", 12, 26, false},
 {"Christie Monteiro", 8, 16, false},
 {"Craig Marduk", 17, 36, false},
 {"Devil Jin", 27, 56, false},
 {"Eddy Gordo", 33, 18, false},
 {"Feng Wei", 29, 60, false},
 {"Ganryu", 23, 48, false},
 {"Heihachi Mishima", 13, 28, false},
 {"Hwoarang", 6, 12, false},
 {"Jack-6", 19, 40, false},
 {"Jin Kazama", 9, 20, false},
 {"Julia Chang", 10, 22, false},
 {"Kazuya Mishima", 14, 30, false},
 {"King", 3, 6, false},
 {"Kuma", 11, 24, true},
 {"Lars Alexanderson", 40, 78, false},
 {"Lee Chaolan", 15, 32, false},
 {"Lei Wulong", 2, 4, false},
 {"Leo", 37, 76, false},
 {"Lili", 31, 64, false},
 {"Ling Xiaoyu", 7, 14, false},
 {"Marshall Law", 1, 2, false},
 {"Miguel", 36, 74, false},
 {"Mokujin", 18, 38, false},
 {"Nina Williams", 5, 10, false},
 {"Panda", 11, 25, true},
 {"Paul Phoenix", 0, 0, false},
 {"Raven", 28, 58, false},
 {"Roger Jr.", 20, 42, false},
 {"Sergei Dragunov", 32, 66, false},
 {"Steve Fox", 16, 34, false},
 {"Wang Jinrei", 22, 46, false},
 {"Yoshimitsu", 4, 8, false},
 {"Zafina", 35, 72, false},
};
struct Stage {const char* name; uint32_t id;};
constexpr Stage stages[]={
 {"Anger of the Earth", 19},
 {"Azazel's Chamber", 13},
 {"Cemetery", 3},
 {"City After Dark", 4},
 {"Electric Fountain", 18},
 {"Fallen Colony", 9},
 {"Fiesta del Tomate", 5},
 {"Gargoyle's Perch", 11},
 {"Hidden Retreat", 20},
 {"High Roller's Club", 1},
 {"Lightning Storm", 16},
 {"Manji Valley", 7},
 {"Mystical Forest", 0},
 {"Noh Theater", 8},
 {"Rustic Asia", 6},
 {"Temple Grounds", 2},
 {"Tunnel Disaster", 17},
 {"Urban War Zone", 10},
};
constexpr uint32_t fighterCount=sizeof(fighters)/sizeof(fighters[0]);
constexpr uint32_t stageCount=sizeof(stages)/sizeof(stages[0]);
constexpr uint32_t playerRow=503, opponentRow=504, stageRow=505, applyRow=506;
constexpr uint32_t playerFirst=507, opponentFirst=playerFirst+fighterCount;
constexpr uint32_t stageFirst=opponentFirst+fighterCount;
constexpr uint32_t originalTotalCount=stageFirst+stageCount;
constexpr uint32_t subtreeSize=originalTotalCount-502;
// RECORD SLOTS MENU TEST V1: 3 menus, each with 4 action records.
constexpr uint32_t recordSlotBase=originalTotalCount+2*subtreeSize;
constexpr uint32_t recordSlotStride=5;
constexpr uint32_t totalCount=recordSlotBase+3*recordSlotStride;
constexpr uint32_t stringBudget=4096;
}
