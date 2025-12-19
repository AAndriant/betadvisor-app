import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, Image, ActivityIndicator, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AvatarHalo from '../../src/components/AvatarHalo';
import { getUserStats, getUserProfile, UserStats, UserProfile, Badge } from '../../src/services/api';

export default function ProfileScreen() {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [statsData, profileData] = await Promise.all([
        getUserStats(),
        getUserProfile(),
      ]);
      setStats(statsData);
      setProfile(profileData);
    } catch (error) {
      console.error('Error fetching profile data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  if (loading) {
    return (
      <View className="flex-1 justify-center items-center bg-white dark:bg-black">
        <ActivityIndicator size="large" color="#0000ff" />
      </View>
    );
  }

  // Fallbacks if data is missing (though interface suggests they are mandatory except avatar)
  const score = stats?.global_score ?? 0;
  const winRate = stats?.win_rate ?? 0;
  const roi = stats?.roi ?? 0;
  const badges = stats?.badges ?? [];
  const username = profile?.username ?? 'User';

  return (
    <SafeAreaView className="flex-1 bg-white dark:bg-black">
      <ScrollView
        contentContainerStyle={{ paddingBottom: 20 }}
        refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Header Section */}
        <View className="items-center mt-6 mb-4">
          <AvatarHalo avatarUrl={profile?.avatar_url} score={score} />
          <Text className="text-xl font-bold mt-2 text-black dark:text-white">{username}</Text>
        </View>

        {/* KPIs Section */}
        <View className="flex-row justify-around mx-4 mb-8 bg-gray-50 dark:bg-gray-900 p-4 rounded-xl shadow-sm">
          <View className="items-center">
            <Text className="text-gray-500 dark:text-gray-400 text-sm uppercase font-semibold">Win Rate</Text>
            <Text className="text-2xl font-bold text-black dark:text-white">{winRate}%</Text>
          </View>
          <View className="w-[1px] bg-gray-200 dark:bg-gray-700" />
          <View className="items-center">
            <Text className="text-gray-500 dark:text-gray-400 text-sm uppercase font-semibold">ROI</Text>
            <Text className={`text-2xl font-bold ${roi >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {roi > 0 ? '+' : ''}{roi}%
            </Text>
          </View>
        </View>

        {/* Badges Section */}
        <View className="px-4">
          <Text className="text-lg font-bold mb-4 text-black dark:text-white">Badges</Text>
          {badges.length === 0 ? (
            <Text className="text-gray-400 italic">No badges yet.</Text>
          ) : (
            <View className="flex-row flex-wrap gap-4">
              {badges.map((badge) => (
                <View key={badge.id} className={`items-center w-1/4 mb-4 ${!badge.is_owned ? 'opacity-40' : ''}`}>
                    <View className="w-16 h-16 bg-gray-200 rounded-full items-center justify-center overflow-hidden mb-2">
                        {badge.icon_url ? (
                            <Image source={{ uri: badge.icon_url }} className="w-full h-full" resizeMode="cover" />
                        ) : (
                             <Text className="text-xs text-gray-500">{badge.name[0]}</Text>
                        )}
                    </View>
                  <Text className="text-xs text-center text-gray-700 dark:text-gray-300" numberOfLines={2}>
                    {badge.name}
                  </Text>
                </View>
              ))}
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
