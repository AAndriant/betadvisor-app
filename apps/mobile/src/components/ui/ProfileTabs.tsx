import React from 'react';
import { View, Pressable } from 'react-native';
import { Grid3X3, BarChart3, Lock } from 'lucide-react-native';
import { cn } from '../../lib/utils';

type TabType = 'grid' | 'stats' | 'locked';

interface ProfileTabsProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

export function ProfileTabs({ activeTab, onTabChange }: ProfileTabsProps) {
  const tabs = [
    { id: 'grid' as const, icon: Grid3X3, label: 'Posts' },
    { id: 'stats' as const, icon: BarChart3, label: 'Stats' },
    { id: 'locked' as const, icon: Lock, label: 'Locked' },
  ];

  return (
    <View className="border-t border-slate-800 w-full">
      <View className="flex-row">
        {tabs.map((tab) => (
          <Pressable
            key={tab.id}
            onPress={() => onTabChange(tab.id)}
            className={cn(
              'flex-1 items-center justify-center py-3 relative'
            )}
            accessibilityLabel={tab.label}
          >
            <tab.icon
              size={24}
              color={activeTab === tab.id ? 'white' : '#64748b'} // slate-500
            />
            {activeTab === tab.id && (
              <View className="absolute top-0 left-0 right-0 h-[2px] bg-white" />
            )}
          </Pressable>
        ))}
      </View>
    </View>
  );
}
