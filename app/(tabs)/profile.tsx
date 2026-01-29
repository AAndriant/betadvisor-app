import React, { useState } from 'react';
import { View, ScrollView, Text, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ProfileHeader } from '../../src/components/ProfileHeader';
import { TicketCard } from '../../src/components/ui/TicketCard';
import { LockedContentOverlay } from '../../src/components/LockedContentOverlay';

// Mock Data pour affichage
const MOCK_USER = {
  name: "Alex Betting",
  handle: "alex_bet",
  role: "TIPSTER" as const,
  isVerified: true,
  stats: { roi: 12.5, winRate: 68, followers: 1405 }
};

const MOCK_TICKETS = [
  { id: '1', match: 'PSG vs OM', odds: 1.85, stake: 100, status: 'WIN', date: '2h ago', isPremium: false },
  { id: '2', match: 'Lakers vs Bulls', odds: 2.10, stake: 100, status: 'PENDING', date: '5h ago', isPremium: true },
  { id: '3', match: 'Nadal vs Djokovic', odds: 1.50, stake: 200, status: 'LOSS', date: '1d ago', isPremium: false },
];

export default function ProfileScreen() {
  const [activeTab, setActiveTab] = useState('Bets');
  const isSubscriber = false;

  return (
    <SafeAreaView className="flex-1 bg-slate-950 pb-24">
      <ScrollView showsVerticalScrollIndicator={false}>

        <ProfileHeader user={MOCK_USER} />

        <View className="flex-row border-b border-slate-800 px-4 mt-2">
            {['Bets', 'Stats', 'Media'].map((tab) => (
                <TouchableOpacity
                    key={tab}
                    onPress={() => setActiveTab(tab)}
                    className={`mr-6 pb-3 ${activeTab === tab ? 'border-b-2 border-emerald-500' : ''}`}
                >
                    <Text className={`font-medium ${activeTab === tab ? 'text-white' : 'text-slate-500'}`}>
                        {tab}
                    </Text>
                </TouchableOpacity>
            ))}
        </View>

        <View className="p-4 gap-4">
            {MOCK_TICKETS.map((ticket) => (
                <View key={ticket.id} className="relative">
                     <TicketCard
                        title={ticket.match}
                        odds={ticket.odds}
                        status={ticket.status as any}
                        roi={null}
                     />

                     {ticket.isPremium && !isSubscriber && (
                         <LockedContentOverlay onUnlock={() => console.log('Open Paywall')} />
                     )}
                </View>
            ))}
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}
