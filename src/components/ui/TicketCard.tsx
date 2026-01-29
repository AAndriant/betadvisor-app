import React, { useState } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { cn } from '../../lib/utils';
import { CheckCircle2, XCircle, Clock, TrendingUp, Heart, MessageCircle } from 'lucide-react-native';
import { toggleLike } from '../../services/social';

interface TicketCardProps {
  title: string;
  odds: number;
  status: 'WIN' | 'LOSS' | 'PENDING';
  roi?: number | null;
  id: string;
  likeCount: number;
  commentCount: number;
  isLiked: boolean;
  onPressComment: () => void;
}

export function TicketCard({ title, odds, status, roi, id, likeCount, commentCount, isLiked, onPressComment }: TicketCardProps) {
  const [liked, setLiked] = useState(isLiked);
  const [count, setCount] = useState(likeCount);

  const handleLike = async () => {
    // Optimistic update
    const newLiked = !liked;
    setLiked(newLiked);
    setCount(prev => newLiked ? prev + 1 : prev - 1);

    try {
      await toggleLike(id);
    } catch (e) {
      // Revert on error
      console.error('Error toggling like:', e);
      setLiked(!newLiked);
      setCount(prev => !newLiked ? prev + 1 : prev - 1);
    }
  };
  const statusConfig = {
    WIN: { color: 'text-emerald-500', hex: '#10b981', icon: CheckCircle2, border: 'border-emerald-500/20', bg: 'bg-emerald-500/10' },
    LOSS: { color: 'text-red-500', hex: '#ef4444', icon: XCircle, border: 'border-red-500/20', bg: 'bg-red-500/10' },
    PENDING: { color: 'text-amber-500', hex: '#f59e0b', icon: Clock, border: 'border-amber-500/20', bg: 'bg-amber-500/10' },
  };

  const config = statusConfig[status] || statusConfig.PENDING;
  const Icon = config.icon;

  return (
    <View className={cn("w-full bg-slate-900 border rounded-xl p-4 mb-3", config.border)}>
      <View className="flex-row justify-between items-start mb-3">
        <View className="flex-1 mr-4">
          <Text className="text-white font-bold text-lg mb-1">{title}</Text>
          <View className={cn("self-start flex-row items-center px-2 py-1 rounded-md", config.bg)}>
            <Icon size={14} color={config.hex} />
            <Text className={cn("text-xs font-bold ml-1", config.color)}>{status}</Text>
          </View>
        </View>

        <View className="bg-slate-950 px-3 py-2 rounded-lg border border-slate-800 items-center">
          <Text className="text-slate-400 text-xs uppercase font-bold">Cote</Text>
          <Text className="text-white font-bold text-lg">{odds.toFixed(2)}</Text>
        </View>
      </View>

      {roi !== null && roi !== undefined && (
        <View className="flex-row items-center border-t border-slate-800 pt-3">
          <TrendingUp size={16} color={roi >= 0 ? "#10b981" : "#ef4444"} />
          <Text className={cn("font-bold ml-2", roi >= 0 ? "text-emerald-500" : "text-red-500")}>
            {roi > 0 ? '+' : ''}{roi}% ROI
          </Text>
        </View>
      )}

      {/* Action Bar */}
      <View className="flex-row items-center border-t border-slate-800 pt-3 mt-3">
        <TouchableOpacity
          onPress={handleLike}
          className="flex-row items-center mr-6"
          activeOpacity={0.7}
        >
          <Heart
            size={20}
            color={liked ? "#ef4444" : "#64748b"}
            fill={liked ? "#ef4444" : "transparent"}
          />
          <Text className={cn("ml-2 font-semibold", liked ? "text-red-500" : "text-slate-400")}>
            {count}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={onPressComment}
          className="flex-row items-center"
          activeOpacity={0.7}
        >
          <MessageCircle size={20} color="#64748b" />
          <Text className="text-slate-400 ml-2 font-semibold">
            {commentCount}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
