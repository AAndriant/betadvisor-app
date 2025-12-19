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
      // Navigation is handled by the auth state listener usually, or explicitly here
      // The prompt says "Redirige vers app/(tabs)/index.tsx une fois connecté"
      // We will handle this in the component or via a side effect in the layout.
      // But explicit redirect is often safer for immediate feedback.
      router.replace('/(tabs)/home');
    } catch (error) {
      Alert.alert('Erreur', 'Échec de la connexion. Vérifiez vos identifiants.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View className="flex-1 justify-center items-center bg-gray-100 p-4">
      <View className="w-full max-w-sm bg-white p-6 rounded-xl shadow-md">
        <Text className="text-2xl font-bold mb-6 text-center text-gray-800">Connexion</Text>

        <View className="mb-4">
          <Text className="block text-gray-700 text-sm font-bold mb-2">Nom d'utilisateur</Text>
          <TextInput
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500"
            value={username}
            onChangeText={setUsername}
            placeholder="Entrez votre nom d'utilisateur"
            autoCapitalize="none"
          />
        </View>

        <View className="mb-6">
          <Text className="block text-gray-700 text-sm font-bold mb-2">Mot de passe</Text>
          <TextInput
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500"
            value={password}
            onChangeText={setPassword}
            placeholder="Entrez votre mot de passe"
            secureTextEntry
          />
        </View>

        <TouchableOpacity
          className={`w-full bg-blue-600 py-3 rounded-md items-center ${isSubmitting ? 'opacity-70' : ''}`}
          onPress={handleLogin}
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text className="text-white font-bold text-lg">Se connecter</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}
