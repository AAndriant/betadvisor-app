import React from 'react';
import { View, Text } from 'react-native';
import { Flame, Dribbble, Twitter } from 'lucide-react-native';

const stats = [
  { label: "Yield", value: "18.4", suffix: "%" },
  { label: "Winrate", value: "67.2", suffix: "%" },
  { label: "Total Profit", value: "$12,847", suffix: "" },
];

const badges = [
  {
    icon: Dribbble,
    label: "Expert Tennis",
    colorClass: "text-yellow-400",
    colorHex: "#facc15",
    bg: "bg-yellow-400/10",
    ring: "border-yellow-400/30"
  },
  {
    icon: Flame,
    label: "Hot Streak",
    colorClass: "text-orange-400",
    colorHex: "#fb923c",
    bg: "bg-orange-400/10",
    ring: "border-orange-400/30"
  },
  {
    icon: Twitter,
    label: "Early Bird",
    colorClass: "text-sky-400",
    colorHex: "#38bdf8",
    bg: "bg-sky-400/10",
    ring: "border-sky-400/30"
  },
];

export function ProfileStatsHeader() {
  return (
    <View className="w-full max-w-2xl gap-6">
      {/* Stats Grid */}
      <View className="flex-row justify-between gap-4">
        {stats.map((stat) => (
          <View key={stat.label} className="flex-1 items-center rounded-lg border border-slate-800 bg-slate-900 p-4">
            <Text className="text-3xl font-bold tracking-tight text-white">
                {stat.value}
                {stat.suffix && <Text className="text-2xl text-slate-400">{stat.suffix}</Text>}
            </Text>
            <Text className="mt-1 text-sm font-medium text-slate-400">{stat.label}</Text>
          </View>
        ))}
      </View>

      {/* Badges Row */}
      <View className="flex-row items-center justify-center gap-4">
        {badges.map((badge) => (
          <View key={badge.label} className="items-center gap-2">
            <View className={`flex h-12 w-12 items-center justify-center rounded-full ${badge.bg} border ${badge.ring}`}>
              <badge.icon size={20} color={badge.colorHex} />
            </View>
            <Text className={`text-xs font-medium ${badge.colorClass}`}>{badge.label}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}
