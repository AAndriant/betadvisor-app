import { View, TouchableOpacity } from 'react-native';
import { Home, Search, PlusSquare, Calendar, User } from 'lucide-react-native';
import { HaloAvatar } from './HaloAvatar';
import { useRouter, usePathname } from 'expo-router';

export function BottomNav() {
  const router = useRouter();
  const pathname = usePathname();

  const navItems = [
    { id: 'feed', icon: Home, route: '/(tabs)/' }, // Feed est l'index
    { id: 'explore', icon: Search, route: '/explore' },
    { id: 'upload', icon: PlusSquare, route: '/(tabs)/upload' }, // Scanner
    { id: 'events', icon: Calendar, route: '/events' },
    { id: 'profile', icon: User, route: '/(tabs)/profile' },
  ];

  return (
    <View className="absolute bottom-0 left-0 right-0 h-20 flex-row items-center justify-around border-t border-white/10 bg-slate-950/90 pb-5 pt-2">
      {navItems.map((item) => {
        const isActive = pathname === item.route || (item.id === 'feed' && pathname === '/');
        const isUpload = item.id === 'upload';
        const isProfile = item.id === 'profile';

        return (
          <TouchableOpacity
            key={item.id}
            onPress={() => router.push(item.route as any)}
            className={`items-center justify-center ${isUpload ? 'mb-6' : ''}`}
          >
            {isProfile ? (
              <View className={isActive ? "rounded-full border-2 border-indigo-500" : ""}>
                <HaloAvatar size="sm" variant="gold" />
              </View>
            ) : (
              <item.icon
                size={isUpload ? 40 : 24}
                color={isActive ? '#6366f1' : '#94a3b8'} // Indigo-500 vs Slate-400
                fill={isActive && !isUpload ? '#6366f1' : 'transparent'}
              />
            )}
          </TouchableOpacity>
        );
      })}
    </View>
  );
}
