import React, { useState, useEffect } from 'react';
import {
    View, Text, TouchableOpacity, TextInput, Image,
    ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, StyleSheet,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Camera, User, ArrowLeft, Check } from 'lucide-react-native';
import { fetchMyProfile, updateProfile } from '../src/services/api';
import { showSuccessToast, showErrorToast } from '../src/services/toast';

export default function EditProfileScreen() {
    const router = useRouter();
    const queryClient = useQueryClient();

    const { data: profile, isLoading } = useQuery({
        queryKey: ['myProfile'],
        queryFn: fetchMyProfile,
    });

    const [bio, setBio] = useState('');
    const [avatarImage, setAvatarImage] = useState<any>(null);
    const [previewUri, setPreviewUri] = useState<string | null>(null);

    useEffect(() => {
        if (profile) {
            setBio(profile.bio || '');
            setPreviewUri(profile.avatar_url || null);
        }
    }, [profile]);

    const mutation = useMutation({
        mutationFn: (data: { bio?: string; avatar?: any }) => updateProfile(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['myProfile'] });
            queryClient.invalidateQueries({ queryKey: ['myStats'] });
            showSuccessToast('Profil mis à jour avec succès !');
            router.back();
        },
        onError: () => {
            showErrorToast('Erreur lors de la mise à jour du profil.');
        },
    });

    const pickImage = async () => {
        const result = await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ['images'],
            allowsEditing: true,
            aspect: [1, 1],
            quality: 0.8,
        });

        if (!result.canceled && result.assets[0]) {
            const asset = result.assets[0];
            setAvatarImage(asset);
            setPreviewUri(asset.uri);
        }
    };

    const handleSave = () => {
        const updateData: { bio?: string; avatar?: any } = {};

        if (bio !== (profile?.bio || '')) {
            updateData.bio = bio;
        }

        if (avatarImage) {
            updateData.avatar = avatarImage;
        }

        if (Object.keys(updateData).length === 0) {
            router.back();
            return;
        }

        mutation.mutate(updateData);
    };

    if (isLoading) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#10b981" />
            </View>
        );
    }

    return (
        <SafeAreaView style={styles.container}>
            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : undefined}
                style={{ flex: 1 }}
            >
                {/* Header */}
                <View style={styles.header}>
                    <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                        <ArrowLeft size={24} color="#fff" />
                    </TouchableOpacity>
                    <Text style={styles.headerTitle}>Modifier le profil</Text>
                    <TouchableOpacity
                        onPress={handleSave}
                        disabled={mutation.isPending}
                        style={[styles.saveButton, mutation.isPending && { opacity: 0.5 }]}
                    >
                        {mutation.isPending ? (
                            <ActivityIndicator size="small" color="#fff" />
                        ) : (
                            <Check size={24} color="#fff" />
                        )}
                    </TouchableOpacity>
                </View>

                <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
                    {/* Avatar Section */}
                    <View style={styles.avatarSection}>
                        <TouchableOpacity onPress={pickImage} style={styles.avatarContainer}>
                            {previewUri ? (
                                <Image source={{ uri: previewUri }} style={styles.avatar} />
                            ) : (
                                <View style={styles.avatarPlaceholder}>
                                    <User size={48} color="#64748b" />
                                </View>
                            )}
                            <View style={styles.cameraOverlay}>
                                <Camera size={20} color="#fff" />
                            </View>
                        </TouchableOpacity>
                        <TouchableOpacity onPress={pickImage}>
                            <Text style={styles.changePhotoText}>Changer la photo</Text>
                        </TouchableOpacity>
                    </View>

                    {/* Bio Section */}
                    <View style={styles.fieldSection}>
                        <Text style={styles.fieldLabel}>Bio</Text>
                        <TextInput
                            style={styles.bioInput}
                            value={bio}
                            onChangeText={setBio}
                            placeholder="Décrivez-vous en quelques mots..."
                            placeholderTextColor="#475569"
                            multiline
                            maxLength={500}
                            textAlignVertical="top"
                        />
                        <Text style={styles.charCount}>{bio.length}/500</Text>
                    </View>

                    {/* Username (read-only) */}
                    <View style={styles.fieldSection}>
                        <Text style={styles.fieldLabel}>Nom d'utilisateur</Text>
                        <View style={styles.readOnlyField}>
                            <Text style={styles.readOnlyText}>@{profile?.username}</Text>
                        </View>
                    </View>
                </ScrollView>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#020617',
    },
    loadingContainer: {
        flex: 1,
        backgroundColor: '#020617',
        justifyContent: 'center',
        alignItems: 'center',
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        paddingVertical: 12,
        borderBottomWidth: 1,
        borderBottomColor: '#1e293b',
    },
    backButton: {
        padding: 4,
    },
    headerTitle: {
        color: '#fff',
        fontSize: 18,
        fontWeight: 'bold',
    },
    saveButton: {
        backgroundColor: '#10b981',
        borderRadius: 20,
        padding: 8,
    },
    content: {
        padding: 16,
    },
    avatarSection: {
        alignItems: 'center',
        marginBottom: 32,
        marginTop: 16,
    },
    avatarContainer: {
        position: 'relative',
        marginBottom: 12,
    },
    avatar: {
        width: 120,
        height: 120,
        borderRadius: 60,
        borderWidth: 3,
        borderColor: '#10b981',
    },
    avatarPlaceholder: {
        width: 120,
        height: 120,
        borderRadius: 60,
        backgroundColor: '#1e293b',
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 3,
        borderColor: '#334155',
    },
    cameraOverlay: {
        position: 'absolute',
        bottom: 0,
        right: 0,
        backgroundColor: '#10b981',
        borderRadius: 20,
        padding: 8,
        borderWidth: 3,
        borderColor: '#020617',
    },
    changePhotoText: {
        color: '#10b981',
        fontSize: 16,
        fontWeight: '600',
    },
    fieldSection: {
        marginBottom: 24,
    },
    fieldLabel: {
        color: '#94a3b8',
        fontSize: 14,
        fontWeight: '600',
        marginBottom: 8,
        textTransform: 'uppercase',
        letterSpacing: 0.5,
    },
    bioInput: {
        backgroundColor: '#0f172a',
        borderWidth: 1,
        borderColor: '#1e293b',
        borderRadius: 12,
        padding: 16,
        color: '#fff',
        fontSize: 16,
        minHeight: 120,
    },
    charCount: {
        color: '#475569',
        fontSize: 12,
        textAlign: 'right',
        marginTop: 4,
    },
    readOnlyField: {
        backgroundColor: '#0f172a',
        borderWidth: 1,
        borderColor: '#1e293b',
        borderRadius: 12,
        padding: 16,
        opacity: 0.6,
    },
    readOnlyText: {
        color: '#94a3b8',
        fontSize: 16,
    },
});
