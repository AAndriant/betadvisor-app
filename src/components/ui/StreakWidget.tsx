import React from 'react';
import { View, Text } from 'react-native';
import { Flame, TrendingUp, Zap } from 'lucide-react-native';
import { cn } from '../../lib/utils';

interface StreakWidgetProps {
  currentStreak: number;
  maxStreak?: number;
}

export function StreakWidget({ currentStreak, maxStreak = 15 }: StreakWidgetProps) {
  const isHot = currentStreak >= 5;
  const isOnFire = currentStreak >= 10;

  return (
    <View
      className={cn(
        'flex-row items-center self-start gap-2 px-3 py-1.5 rounded-full border',
        isOnFire
          ? 'bg-orange-500/20 border-orange-500/30'
          : isHot
          ? 'bg-amber-500/10 border-amber-500/20'
          : 'bg-slate-800 border-slate-700'
      )}
    >
      {isOnFire ? (
        <View className="flex-row items-center">
           <Flame size={16} color="#fb923c" />
           <View className="-ml-2">
             <Flame size={16} color="#f87171" />
           </View>
        </View>
      ) : isHot ? (
        <Flame size={16} color="#fbbf24" />
      ) : (
        <TrendingUp size={16} color="#34d399" />
      )}

      <Text
        className={cn(
          'text-sm font-semibold ml-1',
          isOnFire ? 'text-orange-400' : isHot ? 'text-amber-400' : 'text-emerald-400'
        )}
      >
        {currentStreak}W Streak
      </Text>

      {isOnFire && <Zap size={12} color="#facc15" style={{ marginLeft: 4 }} />}
    </View>
  );
}
