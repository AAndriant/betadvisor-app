import React, { useState } from 'react';
import { View, Text, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { HaloAvatar } from '../../src/components/ui/HaloAvatar';
import { StreakWidget } from '../../src/components/ui/StreakWidget';
import { ProfileHeader } from '../../src/components/ProfileHeader';
import { ProfileTabs } from '../../src/components/ui/ProfileTabs';
import { LockedContentOverlay } from '../../src/components/LockedContentOverlay';
import { TicketCard } from '../../src/components/TicketCard';
import { Ticket } from '../../src/services/api';

const mockUser = {
  username: "BetMaster",
  avatarUrl: "https://i.pravatar.cc/150?u=BetMaster",
  currentStreak: 12
};

// @ts-ignore
const mockTicket: Ticket = {
  id: "TICK-1234-5678",
  image: "",
  total_odds: 4.5,
  stake: 50,
  potential_gain: 225,
  status: 'won',
  created_at: new Date().toISOString(),
  user: {
    username: mockUser.username,
    avatar_url: mockUser.avatarUrl
  }
};

export default function ProfileScreen() {
  const [activeTab, setActiveTab] = useState<'grid' | 'stats' | 'locked'>('grid');

  return (
    <ScrollView className="flex-1 bg-slate-950">
      <SafeAreaView edges={['top']} className="flex-1">
          {/* Header Section */}
          <View className="items-center pt-6 pb-6 px-4 space-y-4">
            <HaloAvatar
              size="lg"
              variant="diamond"
              imageUri={mockUser.avatarUrl}
              alt={mockUser.username}
            />
            <View className="items-center space-y-1">
              <Text className="text-2xl font-bold text-white">{mockUser.username}</Text>
              <Text className="text-slate-400">@betmaster_king</Text>
            </View>
            <StreakWidget currentStreak={mockUser.currentStreak} />
          </View>

          {/* Stats Header from Task 1 */}
          <View className="items-center pb-6">
            <ProfileHeader />
          </View>

          {/* Tabs */}
          <ProfileTabs activeTab={activeTab} onTabChange={setActiveTab} />

          {/* Content Area */}
          <View className="p-4 pb-24">
            {activeTab === 'locked' ? (
              <LockedContentOverlay tipsterName={mockUser.username} />
            ) : (
              <View className="gap-4">
                 {/* Mock List of Tickets */}
                 <TicketCard ticket={mockTicket} likes={243} comments={42} />
                 <TicketCard
                    ticket={{
                        ...mockTicket,
                        id: "TICK-9876",
                        status: 'lost',
                        total_odds: 12.4,
                        potential_gain: 0
                    }}
                    likes={89}
                    comments={15}
                />
              </View>
            )}
          </View>
      </SafeAreaView>
    </ScrollView>
  );
}
