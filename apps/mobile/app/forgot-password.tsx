import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ArrowLeft, Mail, KeyRound } from 'lucide-react-native';
import { requestPasswordReset, confirmPasswordReset } from '../src/services/api';
import { showSuccessToast, showErrorToast } from '../src/services/toast';

type Step = 'request' | 'confirm';

export default function ForgotPasswordScreen() {
    const router = useRouter();
    const [step, setStep] = useState<Step>('request');
    const [email, setEmail] = useState('');
    const [uid, setUid] = useState('');
    const [token, setToken] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleRequestReset = async () => {
        if (!email.trim()) return;

        setIsLoading(true);
        try {
            await requestPasswordReset(email.trim());
            showSuccessToast('Si cet email existe, un code a été envoyé.');
            setStep('confirm');
        } catch {
            showSuccessToast('Si cet email existe, un code a été envoyé.');
            setStep('confirm');
        } finally {
            setIsLoading(false);
        }
    };

    const handleConfirmReset = async () => {
        if (!uid.trim() || !token.trim() || !newPassword.trim()) return;
        if (newPassword !== confirmPassword) {
            showErrorToast('Les mots de passe ne correspondent pas.');
            return;
        }
        if (newPassword.length < 8) {
            showErrorToast('Le mot de passe doit faire au moins 8 caractères.');
            return;
        }

        setIsLoading(true);
        try {
            await confirmPasswordReset(uid.trim(), token.trim(), newPassword);
            showSuccessToast('Mot de passe réinitialisé avec succès !');
            router.replace('/login');
        } catch (e: any) {
            const msg = e?.response?.data?.error;
            if (Array.isArray(msg)) {
                showErrorToast(msg[0]);
            } else if (typeof msg === 'string') {
                showErrorToast(msg);
            } else {
                showErrorToast('Lien invalide ou expiré.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <SafeAreaView className="flex-1 bg-slate-950">
            <View className="flex-1 justify-center px-4">
                {/* Back button */}
                <TouchableOpacity
                    onPress={() => step === 'confirm' ? setStep('request') : router.back()}
                    className="absolute top-4 left-4 z-10 p-2"
                >
                    <ArrowLeft size={24} color="#fff" />
                </TouchableOpacity>

                <View className="bg-slate-900 rounded-2xl border border-slate-800 p-6 mx-4">
                    {step === 'request' ? (
                        <>
                            <View className="items-center mb-4">
                                <View className="w-14 h-14 rounded-full bg-emerald-500/20 items-center justify-center mb-3">
                                    <Mail size={28} color="#10b981" />
                                </View>
                                <Text className="text-white text-2xl font-bold text-center mb-1">
                                    Mot de passe oublié
                                </Text>
                                <Text className="text-slate-400 text-sm text-center">
                                    Entrez votre email pour recevoir un code de réinitialisation.
                                </Text>
                            </View>

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
                                onPress={handleRequestReset}
                                disabled={isLoading || !email.trim()}
                            >
                                {isLoading ? (
                                    <ActivityIndicator color="#ffffff" />
                                ) : (
                                    <Text className="text-white font-bold text-lg">Envoyer le code</Text>
                                )}
                            </TouchableOpacity>

                            <TouchableOpacity onPress={() => router.back()}>
                                <Text className="text-emerald-500 text-center font-medium">
                                    Retour à la connexion
                                </Text>
                            </TouchableOpacity>
                        </>
                    ) : (
                        <>
                            <View className="items-center mb-4">
                                <View className="w-14 h-14 rounded-full bg-emerald-500/20 items-center justify-center mb-3">
                                    <KeyRound size={28} color="#10b981" />
                                </View>
                                <Text className="text-white text-2xl font-bold text-center mb-1">
                                    Nouveau mot de passe
                                </Text>
                                <Text className="text-slate-400 text-sm text-center">
                                    Entrez le UID et le token reçus par email, puis votre nouveau mot de passe.
                                </Text>
                            </View>

                            <Text className="text-slate-300 text-sm font-bold mb-2">UID</Text>
                            <TextInput
                                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white mb-4"
                                value={uid}
                                onChangeText={setUid}
                                placeholder="Code UID de l'email"
                                placeholderTextColor="#64748b"
                                autoCapitalize="none"
                            />

                            <Text className="text-slate-300 text-sm font-bold mb-2">Token</Text>
                            <TextInput
                                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white mb-4"
                                value={token}
                                onChangeText={setToken}
                                placeholder="Token de l'email"
                                placeholderTextColor="#64748b"
                                autoCapitalize="none"
                            />

                            <Text className="text-slate-300 text-sm font-bold mb-2">Nouveau mot de passe</Text>
                            <TextInput
                                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white mb-4"
                                value={newPassword}
                                onChangeText={setNewPassword}
                                placeholder="Min. 8 caractères"
                                placeholderTextColor="#64748b"
                                secureTextEntry
                            />

                            <Text className="text-slate-300 text-sm font-bold mb-2">Confirmer le mot de passe</Text>
                            <TextInput
                                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white mb-6"
                                value={confirmPassword}
                                onChangeText={setConfirmPassword}
                                placeholder="Retapez le mot de passe"
                                placeholderTextColor="#64748b"
                                secureTextEntry
                            />

                            <TouchableOpacity
                                className={`w-full bg-emerald-500 py-3 rounded-xl items-center mb-4 ${isLoading ? 'opacity-70' : ''}`}
                                onPress={handleConfirmReset}
                                disabled={isLoading || !uid.trim() || !token.trim() || !newPassword.trim()}
                            >
                                {isLoading ? (
                                    <ActivityIndicator color="#ffffff" />
                                ) : (
                                    <Text className="text-white font-bold text-lg">Réinitialiser</Text>
                                )}
                            </TouchableOpacity>
                        </>
                    )}
                </View>
            </View>
        </SafeAreaView>
    );
}
