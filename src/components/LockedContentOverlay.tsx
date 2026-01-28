import { View, Text, TouchableOpacity } from 'react-native';
import { Lock } from 'lucide-react-native';
import { BlurView } from 'expo-blur';

export function LockedContentOverlay({ tipsterName }: { tipsterName: string }) {
  return (
    <View className="m-4 overflow-hidden rounded-xl border border-slate-800 bg-slate-950">
      <View className="h-80 w-full items-center justify-center">
         {/* Background Fake Content (Blur) */}
         <View className="absolute inset-0 bg-slate-900 opacity-50" />
         <BlurView intensity={20} className="absolute inset-0" />

         {/* Overlay Card */}
         <View className="mx-6 w-full max-w-xs rounded-2xl border border-white/10 bg-slate-900/90 p-6 items-center shadow-xl">
            <View className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-indigo-500 shadow-lg">
              <Lock size={28} color="white" />
            </View>
            <Text className="mb-5 text-center text-sm text-slate-300">
              Débloquez les pronos de <Text className="font-bold text-white">{tipsterName}</Text>
            </Text>
            <TouchableOpacity className="w-full rounded-xl bg-indigo-600 px-5 py-3">
              <Text className="text-center font-semibold text-white">S'abonner – 9.99€/mo</Text>
            </TouchableOpacity>
         </View>
      </View>
    </View>
  )
}
