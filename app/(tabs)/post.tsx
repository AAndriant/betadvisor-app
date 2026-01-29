import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, Image, ScrollView, ActivityIndicator, Alert } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useCreateBet, useAnalyzeTicket } from '../../src/hooks/useBets';
import { Camera, X, Sparkles } from 'lucide-react-native';

export default function PostScreen() {
  const [match, setMatch] = useState('');
  const [selection, setSelection] = useState('');
  const [odds, setOdds] = useState('');
  const [stake, setStake] = useState('');
  const [image, setImage] = useState<string | null>(null);

  const createBetMutation = useCreateBet();
  const { analyze, isAnalyzing } = useAnalyzeTicket();

  const pickImage = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });

    if (!result.canceled) {
      setImage(result.assets[0].uri);
    }
  };

  const handleAnalyze = async () => {
    if (!image) return;

    const formData = new FormData();
    const filename = image.split('/').pop();
    const match_regex = /\.(\w+)$/.exec(filename || '');
    const type = match_regex ? `image/${match_regex[1]}` : `image`;

    // @ts-ignore : React Native FormData specific handling
    formData.append('image', { uri: image, name: filename, type });

    try {
      const ocrData = await analyze(formData);
      // Auto-fill les champs avec les données OCR
      if (ocrData.match) setMatch(ocrData.match);
      if (ocrData.odds) setOdds(ocrData.odds.toString());
      if (ocrData.stake) setStake(ocrData.stake.toString());
      if (ocrData.selection) setSelection(ocrData.selection);

      Alert.alert("Succès", "Ticket analysé avec succès !");
    } catch (error: any) {
      Alert.alert("Erreur", error.message || "Impossible d'analyser le ticket.");
    }
  };

  const handleSubmit = () => {
    if (!match || !selection || !odds || !stake) return;

    const formData = new FormData();
    formData.append('match_title', match);
    formData.append('selection', selection);
    formData.append('odds', odds);
    formData.append('stake', stake);

    if (image) {
      const filename = image.split('/').pop();
      const match_regex = /\.(\w+)$/.exec(filename || '');
      const type = match_regex ? `image/${match_regex[1]}` : `image`;

      // @ts-ignore : React Native FormData specific handling
      formData.append('ticket_image', { uri: image, name: filename, type });
    }

    createBetMutation.mutate(formData);
  };

  return (
    <ScrollView className="flex-1 bg-slate-950 p-4">
      <Text className="text-white text-2xl font-bold mb-6 mt-4">Nouveau Pari</Text>

      {/* Image Picker */}
      <TouchableOpacity
        onPress={pickImage}
        className="h-48 bg-slate-900 border-2 border-dashed border-slate-700 rounded-xl items-center justify-center mb-6 overflow-hidden"
      >
        {image ? (
          <Image source={{ uri: image }} className="w-full h-full" resizeMode="cover" />
        ) : (
          <View className="items-center">
            <Camera color="#94a3b8" size={32} />
            <Text className="text-slate-400 mt-2">Ajouter la preuve (Ticket)</Text>
          </View>
        )}
      </TouchableOpacity>

      {/* AI Analysis Button */}
      {image && (
        <TouchableOpacity
          onPress={handleAnalyze}
          disabled={isAnalyzing}
          className={`mb-6 py-4 rounded-xl flex-row items-center justify-center ${isAnalyzing ? 'bg-purple-900/50' : 'bg-gradient-to-r from-purple-600 to-pink-600 bg-purple-600'}`}
        >
          {isAnalyzing ? (
            <>
              <ActivityIndicator color="white" size="small" />
              <Text className="text-white font-semibold ml-2">L'IA analyse ton ticket...</Text>
            </>
          ) : (
            <>
              <Sparkles color="white" size={20} />
              <Text className="text-white font-semibold ml-2">Analyser avec l'IA</Text>
            </>
          )}
        </TouchableOpacity>
      )}

      {/* Form Fields */}
      <View className="gap-4">
        <View>
          <Text className="text-slate-400 mb-1 ml-1">Match</Text>
          <TextInput
            className="bg-slate-900 text-white p-4 rounded-xl border border-slate-800"
            placeholder="Ex: PSG vs OM"
            placeholderTextColor="#475569"
            value={match} onChangeText={setMatch}
          />
        </View>

        <View>
          <Text className="text-slate-400 mb-1 ml-1">Sélection</Text>
          <TextInput
            className="bg-slate-900 text-white p-4 rounded-xl border border-slate-800"
            placeholder="Ex: PSG Gagne"
            placeholderTextColor="#475569"
            value={selection} onChangeText={setSelection}
          />
        </View>

        <View className="flex-row gap-4">
          <View className="flex-1">
            <Text className="text-slate-400 mb-1 ml-1">Cote</Text>
            <TextInput
              className="bg-slate-900 text-white p-4 rounded-xl border border-slate-800"
              placeholder="1.50"
              placeholderTextColor="#475569"
              keyboardType="numeric"
              value={odds} onChangeText={setOdds}
            />
          </View>
          <View className="flex-1">
            <Text className="text-slate-400 mb-1 ml-1">Mise (€)</Text>
            <TextInput
              className="bg-slate-900 text-white p-4 rounded-xl border border-slate-800"
              placeholder="100"
              placeholderTextColor="#475569"
              keyboardType="numeric"
              value={stake} onChangeText={setStake}
            />
          </View>
        </View>
      </View>

      <TouchableOpacity
        onPress={handleSubmit}
        disabled={createBetMutation.isPending}
        className={`mt-8 py-4 rounded-full items-center ${createBetMutation.isPending ? 'bg-slate-700' : 'bg-emerald-500'}`}
      >
        {createBetMutation.isPending ? (
          <ActivityIndicator color="white" />
        ) : (
          <Text className="text-white font-bold text-lg">Publier le Ticket</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}
