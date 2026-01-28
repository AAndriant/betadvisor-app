import { Tabs } from 'expo-router';
import React from 'react';
import { BottomNav } from '../../src/components/ui/BottomNav';

export default function TabLayout() {
  return (
    <Tabs
      tabBar={() => <BottomNav />}
      screenOptions={{
        headerShown: false,
      }}>
      <Tabs.Screen
        name="feed"
        options={{
          title: 'Feed',
        }}
      />
      <Tabs.Screen
        name="upload"
        options={{
          title: 'Scanner',
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profil',
        }}
      />
    </Tabs>
  );
}
