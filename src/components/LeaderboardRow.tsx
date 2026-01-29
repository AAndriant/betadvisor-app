import React from 'react';
import { View, Text, TouchableOpacity, Image } from 'react-native';
import { Trophy, Medal } from 'lucide-react-native';
import { LeaderboardUser } from '../services/users';

interface LeaderboardRowProps {
    rank: number;
    user: LeaderboardUser;
    onPress?: (user: LeaderboardUser) => void;
}

export default function LeaderboardRow({ rank, user, onPress }: LeaderboardRowProps) {
    // Determine medal color for top 3
    const getMedalColor = (rank: number) => {
        switch (rank) {
            case 1:
                return '#FFD700'; // Gold
            case 2:
                return '#C0C0C0'; // Silver
            case 3:
                return '#CD7F32'; // Bronze
            default:
                return '#6B7280'; // Gray
        }
    };

    const isTopThree = rank <= 3;
    const medalColor = getMedalColor(rank);

    // Determine ROI color
    const getRoiColor = (roi: number) => {
        if (roi > 0) return 'text-green-500';
        if (roi < 0) return 'text-red-500';
        return 'text-gray-400';
    };

    const roiColor = getRoiColor(user.roi ?? 0);

    // Format ROI with + sign for positive values
    const formatROI = (roi: number | null | undefined) => {
        const value = roi ?? 0;
        const sign = value > 0 ? '+' : '';
        return `${sign}${value.toFixed(1)}%`;
    };

    // Fallback avatar
    const avatarSource = user.avatar_url
        ? { uri: user.avatar_url }
        : { uri: 'https://via.placeholder.com/150' };

    return (
        <TouchableOpacity
            onPress={() => onPress?.(user)}
            className="flex-row items-center bg-gray-900/50 border border-gray-800 rounded-xl p-4 mb-3 mx-4"
            activeOpacity={0.7}
        >
            {/* Rank Badge */}
            <View className="w-12 items-center justify-center mr-3">
                {isTopThree ? (
                    <View className="items-center">
                        {rank === 1 ? (
                            <Trophy size={28} color={medalColor} fill={medalColor} />
                        ) : (
                            <Medal size={28} color={medalColor} fill={medalColor} />
                        )}
                        <Text className="text-xs font-bold mt-1" style={{ color: medalColor }}>
                            #{rank}
                        </Text>
                    </View>
                ) : (
                    <Text className="text-gray-400 font-bold text-lg">#{rank}</Text>
                )}
            </View>

            {/* Avatar */}
            <View className="mr-3">
                <Image
                    source={avatarSource}
                    className="w-12 h-12 rounded-full bg-gray-700"
                    resizeMode="cover"
                />
            </View>

            {/* User Info */}
            <View className="flex-1">
                <Text className="text-white font-semibold text-base mb-1">
                    {user.username}
                </Text>
                <Text className="text-gray-400 text-sm">
                    Winrate: {(user.win_rate ?? 0).toFixed(1)}%
                </Text>
            </View>

            {/* ROI Display */}
            <View className="items-end">
                <Text className={`font-bold text-2xl ${roiColor}`}>
                    {formatROI(user.roi)}
                </Text>
                <Text className="text-gray-500 text-xs mt-1">ROI</Text>
            </View>
        </TouchableOpacity>
    );
}
