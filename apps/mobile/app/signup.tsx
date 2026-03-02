import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../src/context/AuthContext';
import { register } from '../src/services/api';

export default function Signup() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSignup = async () => {
    if (!username || !email || !password || !passwordConfirm) {
      Alert.alert('Erreur', 'Veuillez remplir tous les champs');
      return;
    }

    if (password !== passwordConfirm) {
      Alert.alert('Erreur', 'Les mots de passe ne correspondent pas');
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        username,
        email,
        password,
        password_confirm: passwordConfirm,
      });

      // Auto-login after successful registration
      await login(username, password);

      router.replace('/(tabs)/feed');
    } catch (error: any) {
      let errorMessage = "Échec de l'inscription. Veuillez réessayer.";
      if (error.response && error.response.data) {
        // Extract the first error message if available
        const data = error.response.data;
        const firstKey = Object.keys(data)[0];
        if (firstKey && Array.isArray(data[firstKey])) {
          errorMessage = data[firstKey][0];
        } else if (typeof data === 'string') {
          errorMessage = data;
        }
      }
      Alert.alert('Erreur', errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View className="flex-1 justify-center items-center bg-gray-100 p-4">
      <View className="w-full max-w-sm bg-white p-6 rounded-xl shadow-md">
        <Text className="text-2xl font-bold mb-6 text-center text-gray-800">Inscription</Text>

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

        <View className="mb-4">
          <Text className="block text-gray-700 text-sm font-bold mb-2">Email</Text>
          <TextInput
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500"
            value={email}
            onChangeText={setEmail}
            placeholder="Entrez votre adresse email"
            keyboardType="email-address"
            autoCapitalize="none"
          />
        </View>

        <View className="mb-4">
          <Text className="block text-gray-700 text-sm font-bold mb-2">Mot de passe</Text>
          <TextInput
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500"
            value={password}
            onChangeText={setPassword}
            placeholder="Entrez votre mot de passe"
            secureTextEntry
          />
        </View>

        <View className="mb-6">
          <Text className="block text-gray-700 text-sm font-bold mb-2">Confirmer le mot de passe</Text>
          <TextInput
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500"
            value={passwordConfirm}
            onChangeText={setPasswordConfirm}
            placeholder="Confirmez votre mot de passe"
            secureTextEntry
          />
        </View>

        <TouchableOpacity
          className={`w-full bg-blue-600 py-3 rounded-md items-center mb-4 ${isSubmitting ? 'opacity-70' : ''}`}
          onPress={handleSignup}
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text className="text-white font-bold text-lg">S'inscrire</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity onPress={() => router.back()}>
          <Text className="text-blue-600 text-center font-medium">Retour à la connexion</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
