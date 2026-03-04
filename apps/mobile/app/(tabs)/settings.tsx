import React from 'react';
import { View, Text, TouchableOpacity, Alert, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { User, Bell, Shield, LogOut, ChevronRight, Pencil, CreditCard, Camera, FileText } from 'lucide-react-native';
import { logout } from '../../src/services/api';
import { showSuccessToast } from '../../src/services/toast';
import Constants from 'expo-constants';

export default function SettingsScreen() {
  const router = useRouter();

  const handleLogout = () => {
    Alert.alert('Déconnexion', 'Êtes-vous sûr ?', [
      { text: 'Annuler', style: 'cancel' },
      { text: 'Se déconnecter', style: 'destructive', onPress: () => logout() },
    ]);
  };

  const settingsItems = [
    {
      icon: <CreditCard size={20} color="#10b981" />,
      label: 'Mes abonnements',
      subtitle: 'Gérer, annuler',
      onPress: () => router.push('/my-subscriptions'),
    },
    {
      icon: <Pencil size={20} color="#10b981" />,
      label: 'Modifier le profil',
      subtitle: 'Avatar, bio',
      onPress: () => router.push('/edit-profile'),
    },
    {
      icon: <Bell size={20} color="#eab308" />,
      label: 'Notifications',
      subtitle: 'Gérer les alertes push',
      onPress: () => showSuccessToast('Les notifications push sont activées'),
    },
    {
      icon: <Shield size={20} color="#6366f1" />,
      label: 'Sécurité',
      subtitle: 'Mot de passe, sessions',
      onPress: () => router.push('/security'),
    },
    {
      icon: <Camera size={20} color="#3b82f6" />,
      label: 'Mes tickets OCR',
      subtitle: 'Historique uploads',
      onPress: () => router.push('/my-tickets'),
    },
    {
      icon: <FileText size={20} color="#8b5cf6" />,
      label: 'CGU & Mentions',
      subtitle: 'Conditions, confidentialité',
      onPress: () => router.push('/legal'),
    },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        <Text style={styles.title}>Réglages</Text>

        {/* Settings Items */}
        <View style={styles.section}>
          {settingsItems.map((item, index) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.settingsItem,
                index < settingsItems.length - 1 && styles.settingsItemBorder,
              ]}
              onPress={item.onPress}
            >
              <View style={styles.iconContainer}>{item.icon}</View>
              <View style={styles.settingsItemContent}>
                <Text style={styles.settingsItemLabel}>{item.label}</Text>
                <Text style={styles.settingsItemSubtitle}>{item.subtitle}</Text>
              </View>
              <ChevronRight size={20} color="#475569" />
            </TouchableOpacity>
          ))}
        </View>

        {/* Logout */}
        <View style={styles.section}>
          <TouchableOpacity style={styles.logoutItem} onPress={handleLogout}>
            <LogOut size={20} color="#ef4444" />
            <Text style={styles.logoutText}>Se déconnecter</Text>
          </TouchableOpacity>
        </View>

        {/* Version */}
        <Text style={styles.version}>BetAdvisor v{Constants.expoConfig?.version ?? '1.0.0'}</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#020617',
  },
  title: {
    color: '#fff',
    fontSize: 28,
    fontWeight: 'bold',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 24,
  },
  section: {
    backgroundColor: '#0f172a',
    marginHorizontal: 16,
    borderRadius: 16,
    marginBottom: 16,
    overflow: 'hidden',
  },
  settingsItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  settingsItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: '#1e293b',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  settingsItemContent: {
    flex: 1,
  },
  settingsItemLabel: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  settingsItemSubtitle: {
    color: '#64748b',
    fontSize: 13,
    marginTop: 2,
  },
  logoutItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
  },
  logoutText: {
    color: '#ef4444',
    fontSize: 16,
    fontWeight: '600',
  },
  version: {
    color: '#334155',
    textAlign: 'center',
    fontSize: 12,
    marginTop: 24,
    marginBottom: 40,
  },
});
