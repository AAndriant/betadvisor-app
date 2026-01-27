import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, Image, ScrollView, Alert, ActivityIndicator } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { uploadTicket, getTicketStatus } from '../../src/services/api';
import { useRouter } from 'expo-router';
import { useQueryClient } from '@tanstack/react-query';

export default function UploadTicketScreen() {
  const [image, setImage] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'failed'>('idle');
  const [result, setResult] = useState<any>(null);
  const [statusUrl, setStatusUrl] = useState<string | null>(null);

  const router = useRouter();
  const queryClient = useQueryClient();

  const pickImage = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 1,
    });

    if (!result.canceled) {
      setImage(result.assets[0].uri);
      resetState();
    }
  };

  const takePhoto = async () => {
    const permissionResult = await ImagePicker.requestCameraPermissionsAsync();

    if (permissionResult.granted === false) {
      Alert.alert("Erreur", "La permission d'accéder à la caméra est requise.");
      return;
    }

    let result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      quality: 1,
    });

    if (!result.canceled) {
      setImage(result.assets[0].uri);
      resetState();
    }
  };

  const resetState = () => {
    setResult(null);
    setAnalysisStatus('idle');
    setStatusUrl(null);
  };

  const handleSuccess = (data: any) => {
    setResult(data);
    setAnalysisStatus('completed');
    setUploading(false);

    // Invalidate queries to refresh the feed
    queryClient.invalidateQueries({ queryKey: ['tickets', 'list'] });

    Alert.alert(
      "Succès",
      "Ticket analysé et ajouté avec succès !",
      [
        {
          text: "Voir le feed",
          onPress: () => {
             // Navigate to the Feed tab
             // Note: In Expo Router with Tabs, switching tabs can be done via push or link.
             // router.replace('/(tabs)/') might work if index is mapped to root.
             router.replace('/(tabs)/feed');
          }
        }
      ]
    );
  };

  const handleUpload = async () => {
    if (!image) return;

    setUploading(true);
    setAnalysisStatus('uploading');

    try {
      const response = await uploadTicket(image);
      // Expected response: { status_url: "...", ... } or { id: "..." }

      const url = response.status_url || response.id;

      // Check if it's a polling URL (usually starts with http or is a path)
      // If response has ID but no status_url, it might be immediate result if status is already there?
      // For now, assuming if status_url is present, we poll.

      if (response.status_url) {
        setStatusUrl(response.status_url);
        setAnalysisStatus('processing');
      } else if (url && !response.status) {
         // Fallback if API returns just an ID but we expect a status URL?
         // Or maybe the ID IS the thing to poll?
         // The original code used: const url = response.status_url || response.id;
         // Let's stick to original logic but be careful.
         setStatusUrl(url);
         setAnalysisStatus('processing');
      } else {
        // Maybe the result is immediate?
        handleSuccess(response);
      }
    } catch (error) {
      console.error("Upload error:", error);
      Alert.alert("Erreur", "Échec de l'envoi du ticket.");
      setAnalysisStatus('failed');
      setUploading(false);
    }
  };

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    if (analysisStatus === 'processing' && statusUrl) {
      intervalId = setInterval(async () => {
        try {
          const statusData = await getTicketStatus(statusUrl);
          console.log("Polling status:", statusData);

          if (statusData.status === 'completed' || statusData.status === 'success') {
            clearInterval(intervalId);
            handleSuccess(statusData);
          } else if (statusData.status === 'failed' || statusData.status === 'error') {
            setAnalysisStatus('failed');
            setUploading(false);
            clearInterval(intervalId);
            Alert.alert("Erreur", "L'analyse a échoué.");
          }
          // If still 'processing' or 'pending', continue polling
        } catch (error) {
          console.error("Polling error:", error);
        }
      }, 3000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [analysisStatus, statusUrl]);

  return (
    <ScrollView className="flex-1 bg-white p-4">
      <Text className="text-2xl font-bold mb-6 text-center">Scanner un Ticket</Text>

      <View className="items-center mb-6">
        {image ? (
          <Image source={{ uri: image }} className="w-64 h-64 rounded-lg bg-gray-200" resizeMode="contain" />
        ) : (
          <View className="w-64 h-64 bg-gray-100 rounded-lg justify-center items-center border-2 border-dashed border-gray-300">
            <Text className="text-gray-400">Aucune image sélectionnée</Text>
          </View>
        )}
      </View>

      <View className="flex-row justify-around mb-6">
        <TouchableOpacity
          onPress={takePhoto}
          className="bg-blue-500 py-3 px-4 rounded-lg flex-1 mr-2 items-center"
          disabled={uploading}
        >
          <Text className="text-white font-semibold">Prendre une photo</Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={pickImage}
          className="bg-blue-500 py-3 px-4 rounded-lg flex-1 ml-2 items-center"
          disabled={uploading}
        >
          <Text className="text-white font-semibold">Choisir de la galerie</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        onPress={handleUpload}
        className={`py-4 rounded-lg items-center ${!image || uploading ? 'bg-gray-400' : 'bg-green-600'}`}
        disabled={!image || uploading}
      >
        {uploading ? (
          <View className="flex-row items-center">
             <ActivityIndicator color="white" className="mr-2" />
             <Text className="text-white font-bold text-lg">
               {analysisStatus === 'uploading' ? 'Envoi en cours...' : 'Analyse en cours...'}
             </Text>
          </View>
        ) : (
          <Text className="text-white font-bold text-lg">Analyser le Ticket</Text>
        )}
      </TouchableOpacity>

      {analysisStatus === 'completed' && result && (
        <View className="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <Text className="text-xl font-bold mb-2 text-green-700">Succès !</Text>
          <Text className="text-gray-700">Le ticket a été ajouté au feed.</Text>
        </View>
      )}

      {analysisStatus === 'failed' && (
        <View className="mt-8 p-4 bg-red-50 rounded-lg border border-red-200">
          <Text className="text-red-700 font-bold">L'analyse a échoué. Veuillez réessayer.</Text>
        </View>
      )}
    </ScrollView>
  );
}
