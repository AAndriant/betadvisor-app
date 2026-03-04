import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ArrowLeft, Lock, ChevronRight } from 'lucide-react-native';

export default function SecurityScreen() {
    const router = useRouter();

    return (
        <SafeAreaView className="flex-1 bg-slate-950">
            {/* Header */}
            <View className="flex-row items-center px-4 py-3 border-b border-slate-800">
                <TouchableOpacity onPress={() => router.back()} className="mr-3 p-1">
                    <ArrowLeft size={24} color="#fff" />
                </TouchableOpacity>
                <Text className="text-white font-bold text-xl">Sécurité</Text>
            </View>

            <View className="mt-4 mx-4">
                <View className="bg-slate-900 rounded-xl overflow-hidden">
                    <TouchableOpacity
                        onPress={() => router.push('/forgot-password')}
                        className="flex-row items-center p-4"
                    >
                        <View className="bg-slate-800 w-10 h-10 rounded-lg items-center justify-center mr-3">
                            <Lock size={20} color="#6366f1" />
                        </View>
                        <View className="flex-1">
                            <Text className="text-white font-semibold text-base">Changer le mot de passe</Text>
                            <Text className="text-slate-400 text-sm mt-1">Réinitialiser via email</Text>
                        </View>
                        <ChevronRight size={20} color="#475569" />
                    </TouchableOpacity>
                </View>
            </View>
        </SafeAreaView>
    );
}
