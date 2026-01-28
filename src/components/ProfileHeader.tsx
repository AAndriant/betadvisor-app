import { View, Text } from 'react-native';
import { Flame, Trophy, Twitter, Dribbble } from 'lucide-react-native';

const stats = [
  { label: "Yield", value: "18.4", suffix: "%" },
  { label: "Winrate", value: "67.2", suffix: "%" },
  { label: "Total Profit", value: "$12,847", suffix: "" },
]

const badges = [
  { icon: Dribbble, label: "Expert Tennis", color: "text-yellow-400", bg: "bg-yellow-400/10", ring: "border-yellow-400/30" },
  { icon: Flame, label: "Hot Streak", color: "text-orange-400", bg: "bg-orange-400/10", ring: "border-orange-400/30" },
  { icon: Twitter, label: "Early Bird", color: "text-sky-400", bg: "bg-sky-400/10", ring: "border-sky-400/30" },
]

export function ProfileHeader() {
  return (
    <View className="w-full max-w-2xl space-y-6 px-4 pt-4">
      {/* Stats Row */}
      <View className="flex-row justify-between gap-2">
        {stats.map((stat) => (
          <View key={stat.label} className="flex-1 items-center rounded-lg border border-slate-800 bg-slate-900 p-4">
            <Text className="text-2xl font-bold text-white">
              {stat.value}
              {stat.suffix && <Text className="text-lg text-slate-500">{stat.suffix}</Text>}
            </Text>
            <Text className="mt-1 text-xs font-medium text-slate-500">{stat.label}</Text>
          </View>
        ))}
      </View>

      {/* Badges Row */}
      <View className="flex-row justify-center gap-4 py-2">
        {badges.map((badge) => (
          <View key={badge.label} className="items-center gap-2">
            <View className={`flex h-12 w-12 items-center justify-center rounded-full ${badge.bg} border ${badge.ring}`}>
              <badge.icon
                size={20}
                className={badge.color}
                color={badge.color.includes('yellow') ? '#facc15' : badge.color.includes('orange') ? '#fb923c' : '#38bdf8'}
              />
            </View>
            <Text className={`text-xs font-medium ${badge.color}`}>{badge.label}</Text>
          </View>
        ))}
      </View>
    </View>
  )
}
