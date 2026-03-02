import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useAuth } from '../src/context/AuthContext';
import { useRouter } from 'expo-router';
import { register } from '../src/services/api';

export default function Signup() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<any>({});
  const { login } = useAuth();
  const router = useRouter();

  const validateEmail = (email: string) => {
    return String(email)
      .toLowerCase()
      .match(
        /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|.(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
      );
  };

  const handleSignup = async () => {
    setErrors({});

    if (!username || !email || !password || !confirmPassword) {
      Alert.alert('Erreur', 'Veuillez remplir tous les champs');
      return;
    }

    if (!validateEmail(email)) {
      setErrors({ email: 'Format d\'email invalide' });
      return;
    }

    if (password !== confirmPassword) {
      setErrors({ confirmPassword: 'Les mots de passe ne correspondent pas' });
      return;
    }

    setIsSubmitting(true);
    try {
      await register(username, email, password);
      // Auto-login après inscription réussie
      await login(username, password);
      router.replace('/(tabs)/feed');
    } catch (error: any) {
      if (error.response && error.response.data) {
        // Afficher les erreurs backend (duplicate email/username, password faible)
        const serverErrors = error.response.data;
        setErrors(serverErrors);

        let errorMessage = 'Échec de l\'inscription. Veuillez vérifier les champs.';
        if (serverErrors.username) errorMessage = `Nom d'utilisateur: ${serverErrors.username.join(' ')}`;
        else if (serverErrors.email) errorMessage = `Email: ${serverErrors.email.join(' ')}`;
        else if (serverErrors.password) errorMessage = `Mot de passe: ${serverErrors.password.join(' ')}`;

        Alert.alert('Erreur', errorMessage);
      } else {
        Alert.alert('Erreur', 'Échec de l\'inscription. Veuillez réessayer plus tard.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View className="flex-1 justify-center items-center bg-gray-100 p-4">
      <View className="w-full max-w-sm bg-white p-6 rounded-xl shadow-md">
        <Text className="text-2xl font-bold mb-6 text-center text-gray-800">Créer un compte</Text>

        <View className="mb-4">
          <Text className="block text-gray-700 text-sm font-bold mb-2">Nom d'utilisateur</Text>
          <TextInput
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:border-blue-500 ${errors.username ? 'border-red-500' : 'border-gray-300'}`}
            value={username}
            onChangeText={setUsername}
            placeholder="Choisissez un nom d'utilisateur"
            autoCapitalize="none"
          />
          {errors.username && <Text className="text-red-500 text-xs mt-1">{errors.username}</Text>}
        </View>

        <View className="mb-4">
          <Text className="block text-gray-700 text-sm font-bold mb-2">Email</Text>
          <TextInput
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:border-blue-500 ${errors.email ? 'border-red-500' : 'border-gray-300'}`}
            value={email}
            onChangeText={setEmail}
            placeholder="Entrez votre email"
            keyboardType="email-address"
            autoCapitalize="none"
          />
          {errors.email && <Text className="text-red-500 text-xs mt-1">{errors.email}</Text>}
        </View>

        <View className="mb-4">
          <Text className="block text-gray-700 text-sm font-bold mb-2">Mot de passe</Text>
          <TextInput
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:border-blue-500 ${errors.password ? 'border-red-500' : 'border-gray-300'}`}
            value={password}
            onChangeText={setPassword}
            placeholder="Créez un mot de passe"
            secureTextEntry
          />
          {errors.password && <Text className="text-red-500 text-xs mt-1">{errors.password}</Text>}
        </View>

        <View className="mb-6">
          <Text className="block text-gray-700 text-sm font-bold mb-2">Confirmez le mot de passe</Text>
          <TextInput
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:border-blue-500 ${errors.confirmPassword ? 'border-red-500' : 'border-gray-300'}`}
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            placeholder="Répétez le mot de passe"
            secureTextEntry
          />
          {errors.confirmPassword && <Text className="text-red-500 text-xs mt-1">{errors.confirmPassword}</Text>}
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

        <View className="flex-row justify-center mt-2">
          <Text className="text-gray-600">Déjà un compte ? </Text>
          <TouchableOpacity onPress={() => router.replace('/login')}>
            <Text className="text-blue-600 font-bold">Se connecter</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}
