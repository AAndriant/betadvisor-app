import React, { useState, useCallback } from 'react';
import {
    View,
    Text,
    TextInput,
    FlatList,
    TouchableOpacity,
    ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Trophy, Search as SearchIcon } from 'lucide-react-native';
import { fetchLeaderboard, searchUsers, LeaderboardUser } from '../../src/services/users';
import LeaderboardRow from '../../src/components/LeaderboardRow';

type TabType = 'leaderboard' | 'search';

export default function SearchScreen() {
    const router = useRouter();
    const [activeTab, setActiveTab] = useState<TabType>('leaderboard');
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<LeaderboardUser[]>([]);
    const [isSearching, setIsSearching] = useState(false);

    // Fetch leaderboard on mount
    const {
        data: leaderboard,
        isLoading: isLoadingLeaderboard,
        error: leaderboardError,
    } = useQuery({
        queryKey: ['leaderboard'],
        queryFn: fetchLeaderboard,
    });

    // Handle search submission
    const handleSearch = useCallback(async () => {
        if (!searchQuery.trim()) {
            setSearchResults([]);
            return;
        }

        setIsSearching(true);
        try {
            const results = await searchUsers(searchQuery);
            setSearchResults(results);
        } catch (error) {
            console.error('Search error:', error);
            setSearchResults([]);
        } finally {
            setIsSearching(false);
        }
    }, [searchQuery]);

    // Handle user press - navigate to user profile
    const handleUserPress = (user: LeaderboardUser) => {
        router.push({
            pathname: '/user/[id]',
            params: { id: user.id }
        });
    };

    // Render segmented control
    const renderSegmentedControl = () => (
        <View className="flex-row bg-gray-900/50 border border-gray-800 rounded-xl p-1 mx-4 mb-4">
            <TouchableOpacity
                onPress={() => setActiveTab('leaderboard')}
                className={`flex-1 flex-row items-center justify-center py-3 rounded-lg ${activeTab === 'leaderboard' ? 'bg-yellow-500' : 'bg-transparent'
                    }`}
                activeOpacity={0.7}
            >
                <Trophy
                    size={18}
                    color={activeTab === 'leaderboard' ? '#000' : '#9CA3AF'}
                />
                <Text
                    className={`ml-2 font-semibold ${activeTab === 'leaderboard' ? 'text-black' : 'text-gray-400'
                        }`}
                >
                    Top Tipsters
                </Text>
            </TouchableOpacity>

            <TouchableOpacity
                onPress={() => setActiveTab('search')}
                className={`flex-1 flex-row items-center justify-center py-3 rounded-lg ${activeTab === 'search' ? 'bg-yellow-500' : 'bg-transparent'
                    }`}
                activeOpacity={0.7}
            >
                <SearchIcon
                    size={18}
                    color={activeTab === 'search' ? '#000' : '#9CA3AF'}
                />
                <Text
                    className={`ml-2 font-semibold ${activeTab === 'search' ? 'text-black' : 'text-gray-400'
                        }`}
                >
                    Rechercher
                </Text>
            </TouchableOpacity>
        </View>
    );

    // Render search input
    const renderSearchInput = () => (
        <View className="mx-4 mb-4">
            <View className="flex-row items-center bg-gray-900/50 border border-gray-800 rounded-xl px-4 py-3">
                <SearchIcon size={20} color="#9CA3AF" />
                <TextInput
                    className="flex-1 ml-3 text-white text-base"
                    placeholder="Rechercher un utilisateur..."
                    placeholderTextColor="#6B7280"
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                    onSubmitEditing={handleSearch}
                    returnKeyType="search"
                />
            </View>
            {searchQuery.trim() && (
                <TouchableOpacity
                    onPress={handleSearch}
                    className="bg-yellow-500 rounded-xl py-3 mt-3"
                    activeOpacity={0.8}
                >
                    <Text className="text-black font-bold text-center">
                        Rechercher
                    </Text>
                </TouchableOpacity>
            )}
        </View>
    );

    // Render leaderboard tab
    const renderLeaderboardTab = () => {
        if (isLoadingLeaderboard) {
            return (
                <View className="flex-1 items-center justify-center">
                    <ActivityIndicator size="large" color="#EAB308" />
                    <Text className="text-gray-400 mt-4">Chargement du classement...</Text>
                </View>
            );
        }

        if (leaderboardError) {
            return (
                <View className="flex-1 items-center justify-center px-4">
                    <Text className="text-red-500 text-center">
                        Erreur lors du chargement du classement
                    </Text>
                </View>
            );
        }

        return (
            <FlatList
                data={leaderboard || []}
                keyExtractor={(item) => item.id}
                renderItem={({ item, index }) => (
                    <LeaderboardRow
                        rank={index + 1}
                        user={item}
                        onPress={handleUserPress}
                    />
                )}
                contentContainerClassName="pb-4"
                showsVerticalScrollIndicator={false}
                ListEmptyComponent={
                    <View className="items-center justify-center py-12">
                        <Text className="text-gray-400">Aucun utilisateur trouvé</Text>
                    </View>
                }
            />
        );
    };

    // Render search tab
    const renderSearchTab = () => {
        if (isSearching) {
            return (
                <View className="flex-1 items-center justify-center">
                    <ActivityIndicator size="large" color="#EAB308" />
                    <Text className="text-gray-400 mt-4">Recherche en cours...</Text>
                </View>
            );
        }

        if (searchResults.length === 0 && searchQuery.trim()) {
            return (
                <View className="items-center justify-center py-12">
                    <Text className="text-gray-400">Aucun résultat trouvé</Text>
                </View>
            );
        }

        return (
            <FlatList
                data={searchResults}
                keyExtractor={(item) => item.id}
                renderItem={({ item, index }) => (
                    <LeaderboardRow
                        rank={index + 1}
                        user={item}
                        onPress={handleUserPress}
                    />
                )}
                contentContainerClassName="pb-4"
                showsVerticalScrollIndicator={false}
                ListEmptyComponent={
                    !searchQuery.trim() ? (
                        <View className="items-center justify-center py-12 px-8">
                            <SearchIcon size={48} color="#4B5563" />
                            <Text className="text-gray-400 text-center mt-4">
                                Recherchez un utilisateur par son pseudo
                            </Text>
                        </View>
                    ) : null
                }
            />
        );
    };

    return (
        <SafeAreaView className="flex-1 bg-black" edges={['top']}>
            {/* Header */}
            <View className="px-4 py-4 border-b border-gray-800">
                <Text className="text-white text-3xl font-bold">Champions</Text>
                <Text className="text-gray-400 mt-1">
                    Découvrez les meilleurs tipsters
                </Text>
            </View>

            {/* Segmented Control */}
            <View className="py-4">
                {renderSegmentedControl()}
            </View>

            {/* Search Input (only in search tab) */}
            {activeTab === 'search' && renderSearchInput()}

            {/* Content */}
            <View className="flex-1">
                {activeTab === 'leaderboard' ? renderLeaderboardTab() : renderSearchTab()}
            </View>
        </SafeAreaView>
    );
}
