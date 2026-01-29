import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { BlurView } from 'expo-blur';
import { Lock } from 'lucide-react-native';

interface LockedContentOverlayProps {
  price?: string;
  onUnlock: () => void;
}

export const LockedContentOverlay: React.FC<LockedContentOverlayProps> = ({ price = "9.99€", onUnlock }) => {
  return (
    <View style={StyleSheet.absoluteFill} className="justify-center items-center overflow-hidden rounded-xl">
      <BlurView intensity={80} tint="dark" style={StyleSheet.absoluteFill} />

      <View className="bg-slate-900/90 p-6 rounded-2xl border border-slate-700 items-center shadow-2xl z-10 w-3/4">
        <View className="bg-slate-800 p-4 rounded-full mb-4">
            <Lock size={32} color="#fbbf24" />
        </View>

        <Text className="text-white font-bold text-lg text-center mb-1">
            Analyse Premium
        </Text>
        <Text className="text-slate-400 text-sm text-center mb-6">
            Abonne-toi pour voir ce pronostic.
        </Text>

        <TouchableOpacity
            onPress={onUnlock}
            className="w-full bg-emerald-500 py-3 rounded-lg flex-row justify-center items-center"
        >
            <Text className="text-white font-bold uppercase text-sm">
                Débloquer ({price}/mois)
            </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};
