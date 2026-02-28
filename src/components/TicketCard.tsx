import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { Heart, MessageCircle, Bookmark, BadgeCheck, CheckCircle2 } from 'lucide-react-native';
import { HaloAvatar } from './ui/HaloAvatar';
import { Ticket } from '../services/api';
import { cn } from '../lib/utils';

interface TicketCardProps {
  ticket: Ticket;
  likes?: number;
  comments?: number;
}

export function TicketCard({ ticket, likes = 142, comments = 23 }: TicketCardProps) {
  return (
    <View className="w-full bg-slate-950 rounded-xl border border-slate-800 overflow-hidden my-2">
      {/* Header */}
      <View className="flex-row items-center gap-3 p-4">
        <HaloAvatar
           imageUri={ticket.user.avatar_url}
           alt={ticket.user.username}
           size="sm"
           variant="gold"
        />
        <View className="flex-row items-center gap-1.5">
          <Text className="font-semibold text-white text-base">{ticket.user.username}</Text>
          <BadgeCheck size={16} color="#34d399" />
        </View>
      </View>

      {/* Content */}
      <View className="px-4 pb-4 gap-4">
        {/* Ticket Info */}
        <View className="flex-row items-center gap-2">
          <Text className="text-2xl">🎫</Text>
          <Text className="text-slate-300 font-medium">
             Ticket #{ticket.id.substring(0, 8)}
          </Text>
        </View>

        {/* Odds Box */}
        <View className="bg-emerald-500 rounded-lg p-4">
          <Text className="text-xs font-medium text-emerald-950 uppercase tracking-wide mb-1">Total Odds</Text>
          <Text className="text-lg font-bold text-slate-950">{ticket.total_odds.toFixed(2)}</Text>
        </View>

        {/* Stake and Potential Gain */}
        <View className="gap-2">
            <View className="flex-row items-center gap-2">
                <View className="h-2 w-2 rounded-full bg-emerald-500" />
                <Text className="text-slate-400 text-sm">Stake: {ticket.stake} units</Text>
            </View>
            <View className="flex-row items-center gap-2">
                <View className="h-2 w-2 rounded-full bg-emerald-500" />
                <Text className="text-slate-400 text-sm">Potential Gain: {ticket.potential_gain} units</Text>
            </View>
        </View>

        {/* Status Label */}
        <View className="flex-row items-center gap-2 bg-slate-900/50 rounded-lg px-3 py-2 border border-slate-800 self-start">
          <CheckCircle2 size={16} color={ticket.status === 'won' ? "#34d399" : ticket.status === 'lost' ? "#f87171" : "#fbbf24"} />
          <Text className="text-sm text-slate-300 capitalize">{ticket.status}</Text>
        </View>
      </View>

      {/* Footer */}
      <View className="flex-row items-center justify-between px-4 py-3 border-t border-slate-800">
        <View className="flex-row items-center gap-4">
          <Pressable className="flex-row items-center gap-1.5">
            <Heart size={20} color="#94a3b8" />
            <Text className="text-sm text-slate-400">{likes}</Text>
          </Pressable>
          <Pressable className="flex-row items-center gap-1.5">
            <MessageCircle size={20} color="#94a3b8" />
            <Text className="text-sm text-slate-400">{comments}</Text>
          </Pressable>
        </View>
        <Pressable
          className="bg-emerald-500 rounded-md px-3 py-1.5 flex-row items-center gap-1.5"
        >
          <Bookmark size={16} color="#020617" />
          <Text className="text-slate-950 font-semibold text-sm">Save</Text>
        </Pressable>
      </View>
    </View>
  );
}
