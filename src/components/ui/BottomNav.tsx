import React from 'react';
import { View, Pressable, Platform } from 'react-native';
import { Home, PlusSquare } from 'lucide-react-native';
import { HaloAvatar } from './HaloAvatar';
import { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import { BlurView } from 'expo-blur';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export function BottomNav({ state, descriptors, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();

  return (
    <BlurView
        intensity={80}
        tint="dark"
        className="absolute bottom-0 left-0 right-0 border-t border-white/10"
        style={{ paddingBottom: insets.bottom }}
    >
      <View className="flex-row items-center justify-around h-16 px-2 bg-slate-950/80">
        {state.routes.map((route, index) => {
          const { options } = descriptors[route.key];
          const isFocused = state.index === index;

          const onPress = () => {
            const event = navigation.emit({
              type: 'tabPress',
              target: route.key,
              canPreventDefault: true,
            });

            if (!isFocused && !event.defaultPrevented) {
              navigation.navigate(route.name, route.params);
            }
          };

          let icon;
          if (route.name === 'feed') {
             icon = <Home size={24} color={isFocused ? "white" : "#64748b"} />;
          } else if (route.name === 'upload') {
             icon = <PlusSquare size={24} color={isFocused ? "white" : "#64748b"} />;
          } else if (route.name === 'profile') {
             icon = <HaloAvatar size="sm" variant={isFocused ? 'gold' : 'gray'} />;
          }

          return (
            <Pressable
              key={route.key}
              onPress={onPress}
              className="items-center justify-center p-2"
              accessibilityRole="button"
              accessibilityState={isFocused ? { selected: true } : {}}
            >
              {icon}
            </Pressable>
          );
        })}
      </View>
    </BlurView>
  );
}
