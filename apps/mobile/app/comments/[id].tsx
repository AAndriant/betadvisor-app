import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TextInput, TouchableOpacity, ActivityIndicator, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Send, ArrowLeft } from 'lucide-react-native';
import { fetchComments, postComment } from '../../src/services/social';

interface Comment {
    id: string;
    author_name: string;
    content: string;
    created_at: string;
}

export default function CommentsScreen() {
    const { id } = useLocalSearchParams<{ id: string }>();
    const router = useRouter();
    const [comments, setComments] = useState<Comment[]>([]);
    const [loading, setLoading] = useState(true);
    const [newComment, setNewComment] = useState('');
    const [posting, setPosting] = useState(false);

    const loadComments = async () => {
        if (!id) return;
        try {
            setLoading(true);
            const data = await fetchComments(id);
            setComments(data);
        } catch (error) {
            console.error('Error loading comments:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadComments();
    }, [id]);

    const handlePostComment = async () => {
        if (!newComment.trim() || !id || posting) return;

        try {
            setPosting(true);
            await postComment(id, newComment.trim());
            setNewComment('');
            await loadComments(); // Refresh comments
        } catch (error) {
            console.error('Error posting comment:', error);
        } finally {
            setPosting(false);
        }
    };

    const renderComment = ({ item }: { item: Comment }) => (
        <View className="px-4 py-3 border-b border-slate-800">
            <Text className="text-white font-semibold mb-1">{item.author_name}</Text>
            <Text className="text-slate-300">{item.content}</Text>
            <Text className="text-slate-500 text-xs mt-1">
                {new Date(item.created_at).toLocaleDateString('fr-FR', {
                    day: 'numeric',
                    month: 'short',
                    hour: '2-digit',
                    minute: '2-digit'
                })}
            </Text>
        </View>
    );

    return (
        <SafeAreaView className="flex-1 bg-slate-950" edges={['top']}>
            {/* Header */}
            <View className="px-4 py-3 border-b border-slate-800 flex-row items-center">
                <TouchableOpacity onPress={() => router.back()} className="mr-3">
                    <ArrowLeft size={24} color="#fff" />
                </TouchableOpacity>
                <Text className="text-white font-bold text-xl">Commentaires</Text>
            </View>

            {/* Comments List */}
            {loading ? (
                <View className="flex-1 justify-center items-center">
                    <ActivityIndicator size="large" color="#10b981" />
                </View>
            ) : (
                <KeyboardAvoidingView
                    className="flex-1"
                    behavior={Platform.OS === 'ios' ? 'padding' : undefined}
                    keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
                >
                    <FlatList
                        data={comments}
                        keyExtractor={(item) => item.id}
                        renderItem={renderComment}
                        contentContainerStyle={{ paddingBottom: 20 }}
                        ListEmptyComponent={
                            <View className="flex-1 justify-center items-center py-20">
                                <Text className="text-slate-500">Aucun commentaire pour le moment</Text>
                            </View>
                        }
                    />

                    {/* Input Bar */}
                    <View className="border-t border-slate-800 bg-slate-900 px-4 py-3 flex-row items-center">
                        <TextInput
                            className="flex-1 bg-slate-950 text-white px-4 py-3 rounded-lg mr-3 border border-slate-700"
                            placeholder="Ajouter un commentaire..."
                            placeholderTextColor="#64748b"
                            value={newComment}
                            onChangeText={setNewComment}
                            multiline
                            maxLength={500}
                        />
                        <TouchableOpacity
                            onPress={handlePostComment}
                            disabled={!newComment.trim() || posting}
                            className={`p-3 rounded-lg ${newComment.trim() && !posting ? 'bg-emerald-600' : 'bg-slate-800'}`}
                            activeOpacity={0.7}
                        >
                            {posting ? (
                                <ActivityIndicator size="small" color="#fff" />
                            ) : (
                                <Send size={20} color="#fff" />
                            )}
                        </TouchableOpacity>
                    </View>
                </KeyboardAvoidingView>
            )}
        </SafeAreaView>
    );
}
