import React from 'react';
import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ArrowLeft, ChevronRight } from 'lucide-react-native';

/**
 * Design Catalog — Navigable index of ALL screens in the app.
 *
 * This page is used to:
 * 1. Test every screen during development
 * 2. Generate screenshots for v0.dev redesign
 * 3. Serve as a QA checklist
 *
 * Access: /design-catalog
 */

interface ScreenEntry {
    name: string;
    route: string;
    category: string;
    description: string;
}

const SCREENS: ScreenEntry[] = [
    // Auth
    { name: 'Login', route: '/login', category: 'Auth', description: 'Connexion avec email/mdp' },
    { name: 'Signup', route: '/signup', category: 'Auth', description: 'Création de compte' },
    { name: 'Forgot Password', route: '/forgot-password', category: 'Auth', description: 'Réinitialisation mdp (2 étapes)' },

    // Tabs
    { name: 'Feed', route: '/(tabs)/feed', category: 'Tabs', description: 'Flux de paris (filtres, like, share, report)' },
    { name: 'Search', route: '/(tabs)/search', category: 'Tabs', description: 'Recherche utilisateurs + Leaderboard' },
    { name: 'Post Bet', route: '/(tabs)/post', category: 'Tabs', description: 'Publier un pari (formulaire)' },
    { name: 'Notifications', route: '/(tabs)/notifications', category: 'Tabs', description: 'Centre de notifications (badge, mark read)' },
    { name: 'Profile', route: '/(tabs)/profile', category: 'Tabs', description: 'Profil perso (stats, badges, halo, bets, sport stats)' },
    { name: 'Dashboard', route: '/(tabs)/dashboard', category: 'Tabs', description: 'Dashboard tipster (revenus, abonnés, prix)' },

    // Detail
    { name: 'Comments', route: '/comments/test-id', category: 'Detail', description: 'Thread de commentaires sur un pari' },
    { name: 'User Profile', route: '/user/1', category: 'Detail', description: 'Profil public (follow, subscribe, bets)' },

    // Onboarding & Stripe
    { name: 'Tipster Onboarding', route: '/tipster-onboarding', category: 'Stripe', description: 'Devenir Tipster via Stripe Connect' },
    { name: 'Subscribe', route: '/subscribe', category: 'Stripe', description: 'S\'abonner à un Tipster (Stripe Checkout)' },

    // Settings & Legal
    { name: 'Edit Profile', route: '/edit-profile', category: 'Settings', description: 'Modifier avatar + bio' },
    { name: 'Settings', route: '/settings', category: 'Settings', description: 'Paramètres (logout, etc.)' },
    { name: 'Legal', route: '/settings/legal', category: 'Settings', description: 'CGU, Privacy Policy, Mentions légales' },

    // Ticket OCR
    { name: 'Upload Ticket', route: '/ticket-upload', category: 'OCR', description: 'Upload d\'un ticket pour OCR Gemini' },
    { name: 'Ticket History', route: '/ticket-history', category: 'OCR', description: 'Historique des tickets scannés' },
];

const CATEGORIES = ['Auth', 'Tabs', 'Detail', 'Stripe', 'Settings', 'OCR'];

const CATEGORY_COLORS: Record<string, string> = {
    Auth: '#f59e0b',
    Tabs: '#10b981',
    Detail: '#6366f1',
    Stripe: '#8b5cf6',
    Settings: '#64748b',
    OCR: '#06b6d4',
};

export default function DesignCatalogScreen() {
    const router = useRouter();

    return (
        <SafeAreaView className="flex-1 bg-slate-950">
            <View className="px-4 py-4 border-b border-slate-800 flex-row items-center">
                <TouchableOpacity onPress={() => router.back()} className="mr-3">
                    <ArrowLeft size={24} color="#fff" />
                </TouchableOpacity>
                <View>
                    <Text className="text-white font-bold text-xl">🎨 Design Catalog</Text>
                    <Text className="text-slate-400 text-xs">
                        {SCREENS.length} écrans · Tap pour naviguer
                    </Text>
                </View>
            </View>

            <ScrollView className="flex-1" contentContainerStyle={{ paddingBottom: 100 }}>
                {CATEGORIES.map(category => {
                    const screens = SCREENS.filter(s => s.category === category);
                    const color = CATEGORY_COLORS[category] || '#64748b';

                    return (
                        <View key={category} className="mb-2">
                            {/* Category Header */}
                            <View className="px-4 py-3 flex-row items-center">
                                <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: color, marginRight: 8 }} />
                                <Text className="text-white font-bold text-base">{category}</Text>
                                <Text className="text-slate-500 text-xs ml-2">({screens.length})</Text>
                            </View>

                            {/* Screen Items */}
                            {screens.map(screen => (
                                <TouchableOpacity
                                    key={screen.route}
                                    onPress={() => {
                                        try {
                                            router.push(screen.route as any);
                                        } catch {
                                            // Route might not exist yet
                                        }
                                    }}
                                    className="mx-4 mb-2 bg-slate-900 border border-slate-800 rounded-xl p-4 flex-row items-center"
                                    activeOpacity={0.7}
                                >
                                    <View className="flex-1">
                                        <Text className="text-white font-semibold text-sm">{screen.name}</Text>
                                        <Text className="text-slate-400 text-xs mt-0.5">{screen.description}</Text>
                                        <Text className="text-slate-600 text-xs mt-1 font-mono">{screen.route}</Text>
                                    </View>
                                    <ChevronRight size={18} color="#64748b" />
                                </TouchableOpacity>
                            ))}
                        </View>
                    );
                })}

                {/* Test Accounts Info */}
                <View className="mx-4 mt-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4">
                    <Text className="text-emerald-400 font-bold text-sm mb-2">🔑 Comptes de test</Text>
                    <Text className="text-slate-300 text-xs font-mono">
                        demo_tipster1 / demo1234  (TIPSTER){'\n'}
                        demo_tipster2 / demo1234  (TIPSTER){'\n'}
                        demo_punter1  / demo1234  (PUNTER){'\n'}
                        demo_punter2  / demo1234  (PUNTER){'\n'}
                        demo_punter3  / demo1234  (PUNTER)
                    </Text>
                    <Text className="text-slate-500 text-xs mt-2">
                        Exécuter : python manage.py seed_demo
                    </Text>
                </View>

                {/* Design Notes */}
                <View className="mx-4 mt-3 bg-slate-900 border border-slate-800 rounded-xl p-4 mb-8">
                    <Text className="text-amber-400 font-bold text-sm mb-2">📝 Notes Design (v0.dev)</Text>
                    <Text className="text-slate-400 text-xs leading-5">
                        1. Capture chaque écran (light = screenshot){'\n'}
                        2. Importer dans v0.dev comme référence{'\n'}
                        3. Demander un redesign premium (glassmorphism, gradients){'\n'}
                        4. Exporter le React Native / CSS{'\n'}
                        5. Appliquer les styles dans NativeWind
                    </Text>
                </View>
            </ScrollView>
        </SafeAreaView>
    );
}
