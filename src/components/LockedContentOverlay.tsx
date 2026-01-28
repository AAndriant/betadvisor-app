import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { Lock } from 'lucide-react-native';
import { BlurView } from 'expo-blur';

interface LockedContentOverlayProps {
  tipsterName: string;
  children: React.ReactNode;
}

export function LockedContentOverlay({
  tipsterName,
  children,
}: LockedContentOverlayProps) {
  const isWeb = Platform.OS === 'web';

  if (isWeb) {
      return (
        <View
            style={{
                width: '100%',
                borderRadius: 8,
                borderWidth: 1,
                borderColor: '#1e293b',
                backgroundColor: 'black',
                height: 300,
                alignItems: 'center',
                justifyContent: 'center',
                padding: 10
            }}
        >
             <View
                style={{
                    width: '100%',
                    maxWidth: 280,
                    borderRadius: 16,
                    backgroundColor: 'white',
                    padding: 16,
                    alignItems: 'center',
                    borderWidth: 1,
                    borderColor: 'rgba(255,255,255,0.1)',
                    shadowColor: "#000",
                    shadowOffset: { width: 0, height: 2 },
                    shadowOpacity: 0.25,
                    shadowRadius: 3.84,
                }}
            >
                <View style={{ marginBottom: 12, height: 48, width: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 9999, backgroundColor: '#6366f1' }}>
                    <Lock size={24} color="white" />
                </View>
                <Text style={{ marginBottom: 16, fontSize: 14, color: 'black', textAlign: 'center' }}>
                    Unlock <Text style={{ fontWeight: 'bold', color: 'black' }}>{tipsterName}</Text>'s picks
                </Text>
                <TouchableOpacity style={{ width: '100%', borderRadius: 12, backgroundColor: '#4f46e5', paddingHorizontal: 16, paddingVertical: 10, alignItems: 'center' }}>
                    <Text style={{ fontWeight: '600', color: 'white' }}>Subscribe – 9.99€/mo</Text>
                </TouchableOpacity>
            </View>
        </View>
      );
  }

  return (
    <View className="w-full rounded-lg border border-slate-800 bg-black overflow-hidden relative">
      <View style={{ opacity: 0.5 }}>
         {children}
      </View>
        <BlurView
            intensity={20}
            style={StyleSheet.absoluteFill}
            tint="dark"
        >
             <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 }}>
                <View className="w-full max-w-xs rounded-2xl border border-white/10 bg-slate-900 p-6 items-center shadow-2xl">
                    <View className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-indigo-500 shadow-lg">
                        <Lock size={28} color="white" />
                    </View>
                    <Text className="mb-5 text-sm text-slate-300 text-center">
                        Unlock <Text className="font-bold text-white">{tipsterName}</Text>'s picks
                    </Text>
                    <TouchableOpacity className="w-full rounded-xl bg-indigo-600 px-5 py-3 items-center">
                        <Text className="font-semibold text-white">Subscribe – 9.99€/mo</Text>
                    </TouchableOpacity>
                </View>
             </View>
        </BlurView>
    </View>
  );
}
