import React from 'react';
import { View, Text, Image } from 'react-native';
import { Ticket } from '../services/api';

interface TicketCardProps {
  ticket: Ticket;
}

const formatRelativeTime = (dateString: string) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return 'À l\'instant';
  if (diffInSeconds < 3600) return `il y a ${Math.floor(diffInSeconds / 60)} min`;
  if (diffInSeconds < 86400) return `il y a ${Math.floor(diffInSeconds / 3600)} h`;
  return `il y a ${Math.floor(diffInSeconds / 86400)} j`;
};

export const TicketCard = ({ ticket }: TicketCardProps) => {
  const isWon = ticket.status === 'won';
  const gainColor = isWon ? 'text-green-600' : 'text-gray-500';

  return (
    <View className="bg-white rounded-xl shadow-sm mb-4 overflow-hidden border border-gray-100 mx-4">
      {/* Header */}
      <View className="flex-row items-center p-3">
        <Image
          source={{ uri: ticket.user.avatar_url || `https://ui-avatars.com/api/?name=${ticket.user.username}&background=random` }}
          className="w-10 h-10 rounded-full bg-gray-200"
        />
        <View className="ml-3">
          <Text className="font-bold text-gray-900">{ticket.user.username}</Text>
          <Text className="text-xs text-gray-500">{formatRelativeTime(ticket.created_at)}</Text>
        </View>
      </View>

      {/* Image */}
      <View className="w-full h-96 bg-gray-100">
        <Image
          source={{ uri: ticket.image }}
          className="w-full h-full"
          resizeMode="cover"
        />
      </View>

      {/* Footer (OCR Data) */}
      <View className="p-4 flex-row justify-between items-center bg-gray-50">
        <View>
          <Text className="text-gray-500 text-xs uppercase">Cote Totale</Text>
          <Text className="text-2xl font-black text-blue-900">@{ticket.total_odds?.toFixed(2) || '---'}</Text>
        </View>

        <View className="items-end">
            <View className="flex-row items-baseline">
                <Text className="text-gray-500 text-xs mr-1">Mise:</Text>
                <Text className="font-semibold text-gray-900">{ticket.stake}€</Text>
            </View>
            <View className="flex-row items-baseline mt-1">
                <Text className="text-gray-500 text-xs mr-1">Gain:</Text>
                <Text className={`font-bold text-lg ${gainColor}`}>
                    {ticket.potential_gain}€
                </Text>
            </View>
        </View>
      </View>
    </View>
  );
};
