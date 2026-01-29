import { Tabs } from 'expo-router';
import { BottomNav } from '../../src/components/ui/BottomNav';
import { View } from 'react-native';

export default function TabLayout() {
  return (
    <View className="flex-1 bg-slate-950">
      <Tabs
        screenOptions={{
          headerShown: false,
          tabBarStyle: { display: 'none' },
        }}
        tabBar={() => <BottomNav />}
      >
        <Tabs.Screen name="feed" />
        <Tabs.Screen name="search" />
        {/* @ts-ignore */}
        <Tabs.Screen name="post" options={{ presentation: 'modal' }} />
        <Tabs.Screen name="notifications" />
        <Tabs.Screen name="profile" />
      </Tabs>
    </View>
  );
}
