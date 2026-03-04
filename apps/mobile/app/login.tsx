import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useAuth } from '../src/context/AuthContext';
import { useRouter } from 'expo-router';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleLogin = async () => {
    if (!username || !password) {
      Alert.alert('Erreur', 'Veuillez remplir tous les champs');
      return;
    }

    setIsSubmitting(true);
    try {
      await login(username, password);
      router.replace('/(tabs)/feed');
    } catch (error) {
      Alert.alert('Erreur', 'Échec de la connexion. Vérifiez vos identifiants.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View className="flex-1 justify-center items-center bg-slate-950 p-4">
      <View className="w-full max-w-sm bg-slate-900 p-6 rounded-xl border border-slate-800">
        <Text className="text-3xl font-bold mb-2 text-center text-white">BetAdvisor</Text>
        <Text className="text-sm text-slate-400 text-center mb-8">Connecte-toi pour continuer</Text>

        <View className="mb-4">
          <Text className="text-slate-300 text-sm font-bold mb-2">Nom d'utilisateur</Text>
          <TextInput
            className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white"
            value={username}
            onChangeText={setUsername}
            placeholder="Entrez votre nom d'utilisateur"
            placeholderTextColor="#64748b"
            autoCapitalize="none"
          />
        </View>

        <View className="mb-6">
          <Text className="text-slate-300 text-sm font-bold mb-2">Mot de passe</Text>
          <TextInput
            className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white"
            value={password}
            onChangeText={setPassword}
            placeholder="Entrez votre mot de passe"
            placeholderTextColor="#64748b"
            secureTextEntry
          />
        </View>

        <TouchableOpacity
          className={`w-full bg-emerald-500 py-3 rounded-xl items-center mb-4 ${isSubmitting ? 'opacity-70' : ''}`}
          onPress={handleLogin}
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text className="text-white font-bold text-lg">Se connecter</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity onPress={() => router.push('/signup')}>
          <Text className="text-emerald-500 text-center font-medium">Vous n'avez pas de compte ? S'inscrire</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
