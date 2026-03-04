import React from 'react';
import { View, Text, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { ArrowLeft } from 'lucide-react-native';

export default function LegalScreen() {
    const router = useRouter();

    return (
        <SafeAreaView className="flex-1 bg-slate-950">
            {/* Header */}
            <View className="flex-row items-center px-4 py-3 border-b border-slate-800">
                <TouchableOpacity onPress={() => router.back()} className="mr-3 p-1">
                    <ArrowLeft size={24} color="#fff" />
                </TouchableOpacity>
                <Text className="text-white font-bold text-xl">Mentions légales</Text>
            </View>

            <ScrollView className="flex-1 px-4 py-6" contentContainerStyle={{ paddingBottom: 60 }}>
                {/* CGU */}
                <Text className="text-emerald-500 font-bold text-lg mb-3">
                    Conditions Générales d'Utilisation
                </Text>
                <Text className="text-slate-300 text-sm leading-6 mb-4">
                    BetAdvisor est une plateforme de partage d'analyses sportives entre tipsters et abonnés.
                    En utilisant l'application, vous acceptez les présentes conditions.
                </Text>
                <Text className="text-slate-300 text-sm leading-6 mb-4">
                    L'utilisation de BetAdvisor est réservée aux personnes majeures. Les analyses partagées
                    sur la plateforme sont des opinions personnelles des tipsters et ne constituent en aucun
                    cas des conseils financiers. BetAdvisor ne saurait être tenu responsable des pertes
                    financières résultant de l'utilisation des informations publiées sur la plateforme.
                </Text>
                <Text className="text-slate-300 text-sm leading-6 mb-4">
                    Les utilisateurs s'engagent à ne pas publier de contenu illicite, offensant ou trompeur.
                    BetAdvisor se réserve le droit de suspendre ou supprimer tout compte ne respectant pas
                    ces conditions.
                </Text>
                <Text className="text-slate-300 text-sm leading-6 mb-6">
                    Les abonnements sont facturés mensuellement via Stripe. Les remboursements sont traités
                    au cas par cas. L'annulation prend effet à la fin de la période de facturation en cours.
                </Text>

                {/* Privacy */}
                <Text className="text-emerald-500 font-bold text-lg mb-3">
                    Politique de Confidentialité
                </Text>
                <Text className="text-slate-300 text-sm leading-6 mb-4">
                    BetAdvisor collecte et traite vos données personnelles conformément au RGPD.
                    Les données collectées incluent : nom d'utilisateur, adresse email, avatar,
                    données de paiement (traitées par Stripe), et statistiques d'utilisation.
                </Text>
                <Text className="text-slate-300 text-sm leading-6 mb-4">
                    Vos données de paiement sont gérées exclusivement par Stripe et ne sont jamais
                    stockées sur nos serveurs. Les données d'utilisation peuvent être analysées à des
                    fins d'amélioration du service via des outils d'analytics anonymisés.
                </Text>
                <Text className="text-slate-300 text-sm leading-6 mb-6">
                    Vous disposez d'un droit d'accès, de modification et de suppression de vos données
                    personnelles. Pour exercer ces droits, contactez-nous à l'adresse ci-dessous.
                </Text>

                {/* Contact */}
                <Text className="text-emerald-500 font-bold text-lg mb-3">
                    Contact
                </Text>
                <Text className="text-slate-300 text-sm leading-6 mb-2">
                    Pour toute question relative aux conditions d'utilisation ou à la politique de
                    confidentialité, vous pouvez nous contacter :
                </Text>
                <Text className="text-white font-medium text-sm mb-6">
                    📧 support@betadvisor.app
                </Text>
            </ScrollView>
        </SafeAreaView>
    );
}
