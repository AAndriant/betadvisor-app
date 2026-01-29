import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { HaloAvatar } from './ui/HaloAvatar';
import { TrendingUp, Award, CheckCircle2 } from 'lucide-react-native';

interface ProfileHeaderProps {
  user: {
    name: string;
    handle: string;
    avatarUrl?: string;
    isVerified?: boolean;
    role: 'TIPSTER' | 'PUNTER';
    stats?: {
      roi: number;
      winRate: number;
      followers: number;
    };
  };
}

export const ProfileHeader: React.FC<ProfileHeaderProps> = ({ user }) => {
  return (
    <View className="px-4 pt-2 pb-6 bg-slate-950">
      {/* Top Row: Avatar & Actions */}
      <View className="flex-row items-center justify-between mb-4">
        <HaloAvatar
          uri={user.avatarUrl}
          fallback={user.name[0]}
          size="lg"
          premium={user.role === 'TIPSTER'}
        />

        <View className="flex-row gap-4">
            <View className="items-center">
                <Text className="text-white font-bold text-lg">{user.stats?.followers || 0}</Text>
                <Text className="text-slate-400 text-xs">Abonnés</Text>
            </View>
            <TouchableOpacity className="bg-emerald-500 px-6 py-2 rounded-full justify-center">
                <Text className="text-white font-bold text-sm">S'abonner</Text>
            </TouchableOpacity>
        </View>
      </View>

      {/* Identity */}
      <View className="mb-4">
        <View className="flex-row items-center gap-1">
            <Text className="text-2xl font-bold text-white">{user.name}</Text>
            {user.isVerified && <CheckCircle2 size={20} color="#10b981" fill="black" />}
        </View>
        <Text className="text-slate-400 text-sm">@{user.handle} • Paris Sportifs</Text>
      </View>

      {/* High-Level Stats (Unit Economics) */}
      {user.role === 'TIPSTER' && user.stats && (
        <View className="flex-row gap-3 mt-2">
            <View className="flex-1 bg-slate-900 border border-slate-800 rounded-xl p-3 flex-row items-center gap-3">
                <View className="bg-emerald-500/10 p-2 rounded-lg">
                    <TrendingUp size={20} color="#10b981" />
                </View>
                <View>
                    <Text className="text-slate-400 text-xs font-medium">Yield (ROI)</Text>
                    <Text className="text-emerald-400 font-bold text-lg">+{user.stats.roi}%</Text>
                </View>
            </View>

            <View className="flex-1 bg-slate-900 border border-slate-800 rounded-xl p-3 flex-row items-center gap-3">
                <View className="bg-indigo-500/10 p-2 rounded-lg">
                    <Award size={20} color="#6366f1" />
                </View>
                <View>
                    <Text className="text-slate-400 text-xs font-medium">Réussite</Text>
                    <Text className="text-white font-bold text-lg">{user.stats.winRate}%</Text>
                </View>
            </View>
        </View>
      )}
    </View>
  );
};
