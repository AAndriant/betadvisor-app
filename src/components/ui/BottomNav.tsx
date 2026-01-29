import React from 'react';
import { View, TouchableOpacity } from 'react-native';
import { BlurView } from 'expo-blur';
import { Home, Search, Plus, Bell, User } from 'lucide-react-native';
import { useRouter, usePathname } from 'expo-router';
import clsx from 'clsx';

export const BottomNav = () => {
  const router = useRouter();
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path || pathname.startsWith(path);

  const NavItem = ({ icon: Icon, path, isMain = false }: any) => (
    <TouchableOpacity
      onPress={() => router.push(path)}
      className={clsx(
        "items-center justify-center",
        isMain ? "-mt-8" : "flex-1"
      )}
    >
        {isMain ? (
            <View className="bg-emerald-500 h-16 w-16 rounded-full items-center justify-center shadow-lg shadow-emerald-500/50 border-4 border-slate-950">
                <Plus color="white" size={32} strokeWidth={3} />
            </View>
        ) : (
            <Icon
                size={24}
                color={isActive(path) ? "#10b981" : "#64748b"}
                strokeWidth={isActive(path) ? 3 : 2}
            />
        )}
    </TouchableOpacity>
  );

  return (
    <View className="absolute bottom-6 left-4 right-4 rounded-3xl overflow-hidden shadow-black/50 shadow-lg">
      <BlurView intensity={90} tint="dark" className="flex-row items-center justify-around py-4 bg-slate-900/80">
        <NavItem icon={Home} path="/(tabs)/feed" />
        <NavItem icon={Search} path="/(tabs)/search" />
        <NavItem icon={Plus} path="/(tabs)/post" isMain />
        <NavItem icon={Bell} path="/(tabs)/notifications" />
        <NavItem icon={User} path="/(tabs)/profile" />
      </BlurView>
    </View>
  );
};
