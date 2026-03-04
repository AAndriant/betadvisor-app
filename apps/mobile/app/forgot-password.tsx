import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ArrowLeft } from 'lucide-react-native';
import { requestPasswordReset } from '../src/services/api';
import { showSuccessToast } from '../src/services/toast';

export default function ForgotPasswordScreen() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async () => {
        if (!email.trim()) return;

        setIsLoading(true);
        try {
            await requestPasswordReset(email.trim());
            showSuccessToast('Si cet email existe, un lien de réinitialisation a été envoyé.');
            router.back();
        } catch {
            // The backend always returns 200, but handle network errors gracefully
            showSuccessToast('Si cet email existe, un lien de réinitialisation a été envoyé.');
            router.back();
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <SafeAreaView className="flex-1 bg-slate-950">
            <View className="flex-1 justify-center px-4">
                {/* Back button */}
                <TouchableOpacity
                    onPress={() => router.back()}
                    className="absolute top-4 left-4 z-10 p-2"
                >
                    <ArrowLeft size={24} color="#fff" />
                </TouchableOpacity>

                <View className="bg-slate-900 rounded-2xl border border-slate-800 p-6 mx-4">
                    <Text className="text-white text-2xl font-bold text-center mb-2">
                        Mot de passe oublié
                    </Text>
                    <Text className="text-slate-400 text-sm text-center mb-6">
                        Entrez votre adresse email pour recevoir un lien de réinitialisation.
                    </Text>

                    <Text className="text-slate-300 text-sm font-bold mb-2">Email</Text>
                    <TextInput
                        className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white mb-6"
                        value={email}
                        onChangeText={setEmail}
                        placeholder="votre@email.com"
                        placeholderTextColor="#64748b"
                        keyboardType="email-address"
                        autoCapitalize="none"
                        autoComplete="email"
                    />

                    <TouchableOpacity
                        className={`w-full bg-emerald-500 py-3 rounded-xl items-center mb-4 ${isLoading ? 'opacity-70' : ''}`}
                        onPress={handleSubmit}
                        disabled={isLoading || !email.trim()}
                    >
                        {isLoading ? (
                            <ActivityIndicator color="#ffffff" />
                        ) : (
                            <Text className="text-white font-bold text-lg">Envoyer le lien</Text>
                        )}
                    </TouchableOpacity>

                    <TouchableOpacity onPress={() => router.back()}>
                        <Text className="text-emerald-500 text-center font-medium">
                            Retour à la connexion
                        </Text>
                    </TouchableOpacity>
                </View>
            </View>
        </SafeAreaView>
    );
}
