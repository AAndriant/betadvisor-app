import React, { useState } from 'react';
import { View, Text, TouchableOpacity, Image, ActivityIndicator, ScrollView, Alert } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { uploadTicket } from '../src/features/tickets/ticketService';
import { useRouter } from 'expo-router';

export default function CreateTicket() {
    const [image, setImage] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const router = useRouter();

    const [aspectRatio, setAspectRatio] = useState(1);

    const pickImage = async () => {
        // Request permission
        const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (status !== 'granted') {
            Alert.alert('Permission refusée', 'Nous avons besoin de la permission pour accéder à la galerie.');
            return;
        }

        const result = await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ImagePicker.MediaTypeOptions.Images,
            allowsEditing: false, // On laisse l'image entière
            quality: 1,
        });

        if (!result.canceled) {
            const uri = result.assets[0].uri;
            setImage(uri);
            setResult(null);
            Image.getSize(uri, (width, height) => {
                setAspectRatio(width / height);
            });
        }
    };

    const takePhoto = async () => {
        const { status } = await ImagePicker.requestCameraPermissionsAsync();
        if (status !== 'granted') {
            Alert.alert('Permission refusée', 'Nous avons besoin de la permission pour accéder à la caméra.');
            return;
        }

        const result = await ImagePicker.launchCameraAsync({
            allowsEditing: false, // On laisse l'image entière
            quality: 1,
        });

        if (!result.canceled) {
            const uri = result.assets[0].uri;
            setImage(uri);
            setResult(null);
            Image.getSize(uri, (width, height) => {
                setAspectRatio(width / height);
            });
        }
    };

    const handleUpload = async () => {
        if (!image) return;

        setLoading(true);
        try {
            const data = await uploadTicket(image);
            setResult(data);
            Alert.alert('Succès', 'Ticket analysé avec succès !');
        } catch (error: any) {
            console.error(error);
            const errorMessage = error.response?.data ? JSON.stringify(error.response.data) : (error.message || "Une erreur est survenue");
            Alert.alert('Erreur', errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <View className="flex-1 bg-white">
            <ScrollView className="flex-1 p-4">
                <Text className="text-2xl font-bold mb-6 text-center text-gray-800">Nouveau Ticket</Text>

                <View className="space-y-4">
                    {/* Primary Button: Gallery */}
                    <TouchableOpacity
                        onPress={pickImage}
                        className="bg-blue-600 p-4 rounded-xl items-center shadow-lg"
                    >
                        <Text className="text-white font-bold text-lg">Importer un Ticket</Text>
                    </TouchableOpacity>

                    {/* Secondary Button: Camera */}
                    <TouchableOpacity
                        onPress={takePhoto}
                        className="border border-blue-600 p-3 rounded-xl items-center"
                    >
                        <Text className="text-blue-600 font-semibold text-base">Prendre une photo</Text>
                    </TouchableOpacity>
                </View>

                {/* Image Preview */}
                {image && (
                    <View className="mt-8 mb-20">
                        <Image
                            source={{ uri: image }}
                            style={{ width: '100%', aspectRatio: aspectRatio }}
                            resizeMode="contain"
                            className="rounded-lg bg-gray-100"
                        />
                    </View>
                )}

                {/* Result Display */}
                {result && (
                    <View className="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-200 mb-20">
                        <Text className="font-bold text-lg mb-2 text-gray-800">Résultat de l'analyse :</Text>
                        <Text className="font-mono text-xs text-gray-600">
                            {JSON.stringify(result, null, 2)}
                        </Text>
                    </View>
                )}
            </ScrollView>

            {/* Sticky Action Button */}
            {image && (
                <View className="absolute bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-200">
                    <TouchableOpacity
                        onPress={handleUpload}
                        disabled={loading}
                        className={`w-full p-4 rounded-xl items-center ${loading ? 'bg-gray-400' : 'bg-green-600'}`}
                    >
                        {loading ? (
                            <ActivityIndicator color="white" />
                        ) : (
                            <Text className="text-white font-bold text-lg">ANALYSER LE PARI</Text>
                        )}
                    </TouchableOpacity>
                </View>
            )}
        </View>
    );
}
