import React, { useState } from 'react';
import { View, Text, ScrollView, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { HaloAvatar } from '../../src/components/ui/HaloAvatar';
import { StreakWidget } from '../../src/components/ui/StreakWidget';
import { ProfileStatsHeader } from '../../src/components/ProfileHeader';
import { ProfileTabs } from '../../src/components/ui/ProfileTabs';
import { LockedContentOverlay } from '../../src/components/LockedContentOverlay';

// Mock data for grid
const MOCK_IMAGES = [
  'https://images.unsplash.com/photo-1546519638-68e109498ffc?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1579952363873-27f3bde9be2b?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1593341646782-e0b495cffd32?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1518091043644-c1d4457512c6?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1556906781-9a412961c28c?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1622838320002-dbb6c623d306?auto=format&fit=crop&w=800&q=80',
  'https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=800&q=80',
];

export default function ProfileScreen() {
  const [activeTab, setActiveTab] = useState<'grid' | 'stats' | 'locked'>('grid');

  // Hardcoded user data as per instruction "Assemble these components"
  const user = {
    name: "Alex Thompson",
    username: "@alexbet",
    avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=800&q=80",
    streak: 12
  };

  return (
    <SafeAreaView className="flex-1 bg-black" edges={['top']}>
      <ScrollView contentContainerStyle={{ paddingBottom: 100 }}>
        {/* Header Section */}
        <View className="items-center mt-6 px-4">
           {/* Avatar & Name */}
           <View className="items-center mb-4">
              <HaloAvatar
                imageUri={user.avatar}
                size="lg"
                variant="gold"
                className="mb-3"
              />
              <Text className="text-2xl font-bold text-white">{user.name}</Text>
              <Text className="text-slate-400">{user.username}</Text>
           </View>

           {/* Streak Widget */}
           <View className="mb-8">
              <StreakWidget currentStreak={user.streak} />
           </View>

           {/* Stats Header */}
           <ProfileStatsHeader />
        </View>

        {/* Tabs */}
        <View className="mt-8">
            <ProfileTabs activeTab={activeTab} onTabChange={setActiveTab} />
        </View>

        {/* Content */}
        <View className="p-1">
            {activeTab === 'grid' && (
                <View className="flex-row flex-wrap">
                    {MOCK_IMAGES.map((img, i) => (
                        <View key={i} className="w-1/3 p-0.5 aspect-square">
                            <Image source={{ uri: img }} className="w-full h-full rounded-sm" />
                        </View>
                    ))}
                </View>
            )}

            {activeTab === 'locked' && (
                <View className="p-4">
                    <LockedContentOverlay tipsterName={user.name}>
                         {/* Content to be blurred */}
                         <View className="gap-2">
                             <View className="h-40 w-full bg-slate-800 rounded-lg" />
                             <View className="h-20 w-full bg-slate-800 rounded-lg" />
                             <View className="h-60 w-full bg-slate-800 rounded-lg" />
                         </View>
                    </LockedContentOverlay>
                </View>
            )}

             {activeTab === 'stats' && (
                <View className="p-8 items-center">
                    <Text className="text-slate-500">More detailed stats coming soon...</Text>
                </View>
            )}
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}
