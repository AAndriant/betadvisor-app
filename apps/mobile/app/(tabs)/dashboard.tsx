import { useEffect, useState } from "react";
import { View, Text, FlatList, ActivityIndicator, TextInput, TouchableOpacity } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { getDashboard, updateSubscriptionPrice, DashboardData } from "../../src/services/api";
import { showSuccessToast, showErrorToast } from "../../src/services/toast";

export default function DashboardScreen() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [priceInput, setPriceInput] = useState('');
  const [updatingPrice, setUpdatingPrice] = useState(false);

  const loadDashboard = () => {
    setLoading(true);
    getDashboard()
      .then((d) => {
        setData(d);
        setPriceInput(d.subscription_price || '');
      })
      .catch((error) => console.error("Error fetching dashboard:", error))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const handleUpdatePrice = async () => {
    const price = parseFloat(priceInput);
    if (isNaN(price) || price < 1 || price > 9999) {
      showErrorToast('Le prix doit être entre 1€ et 9999€');
      return;
    }

    setUpdatingPrice(true);
    try {
      const updated = await updateSubscriptionPrice(priceInput);
      setData((prev) => prev ? { ...prev, subscription_price: updated.subscription_price || priceInput } : prev);
      showSuccessToast('Prix d\'abonnement mis à jour !');
    } catch (error: any) {
      showErrorToast('Impossible de mettre à jour le prix.');
    } finally {
      setUpdatingPrice(false);
    }
  };

  if (loading) {
    return (
      <View className="flex-1 bg-slate-950 justify-center">
        <ActivityIndicator size="large" color="#10b981" />
      </View>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-slate-950">
      <View className="px-4 py-4 border-b border-slate-800">
        <Text className="text-white font-bold text-2xl">Dashboard</Text>
      </View>

      <View className="p-4 space-y-4">
        {/* Stats Grid */}
        <View className="flex-row justify-between mb-4">
          <View className="bg-slate-900 flex-1 rounded-2xl p-4 mr-2 border border-slate-800">
            <Text className="text-slate-400 text-sm mb-1">Active Subs</Text>
            <Text className="text-white text-2xl font-bold">{data?.active_subscribers ?? 0}</Text>
          </View>
          <View className="bg-slate-900 flex-1 rounded-2xl p-4 ml-2 border border-slate-800">
            <Text className="text-slate-400 text-sm mb-1">Revenue (Est)</Text>
            <Text className="text-emerald-500 text-2xl font-bold">€{data?.monthly_revenue_estimate ?? 0}</Text>
          </View>
        </View>

        {/* Subscription Price Editor */}
        <View className="bg-slate-900 rounded-2xl p-4 border border-slate-800 mb-4">
          <Text className="text-white font-bold text-lg mb-3">Prix abonnement</Text>
          <Text className="text-slate-400 text-sm mb-3">
            Prix actuel : <Text className="text-emerald-500 font-bold">{data?.subscription_price ?? '—'}€/mois</Text>
          </Text>
          <View className="flex-row items-center">
            <View className="flex-1 mr-3">
              <TextInput
                className="bg-slate-800 text-white p-3 rounded-xl border border-slate-700"
                value={priceInput}
                onChangeText={setPriceInput}
                placeholder="Ex: 9.99"
                placeholderTextColor="#64748b"
                keyboardType="numeric"
              />
            </View>
            <TouchableOpacity
              onPress={handleUpdatePrice}
              disabled={updatingPrice}
              className={`px-5 py-3 rounded-xl ${updatingPrice ? 'bg-slate-700' : 'bg-emerald-500'}`}
            >
              {updatingPrice ? (
                <ActivityIndicator color="white" size="small" />
              ) : (
                <Text className="text-white font-bold">Mettre à jour</Text>
              )}
            </TouchableOpacity>
          </View>
          <Text className="text-slate-600 text-xs mt-2">Min 1€ — Max 9999€</Text>
        </View>

        <Text className="text-white font-bold text-lg mb-2">Recent Subscribers</Text>
        <FlatList
          data={data?.recent_subscriptions}
          keyExtractor={(item, index) => `${item.follower_username}-${index}`}
          renderItem={({ item }) => (
            <View className="bg-slate-900 rounded-xl p-4 mb-2 flex-row justify-between items-center border border-slate-800">
              <View>
                <Text className="text-white font-semibold">{item.follower_username}</Text>
                <Text className="text-slate-400 text-sm">Status: {item.status}</Text>
              </View>
              {item.created_at && (
                <Text className="text-slate-500 text-xs">
                  Since: {new Date(item.created_at).toLocaleDateString()}
                </Text>
              )}
            </View>
          )}
          ListEmptyComponent={
            <Text className="text-slate-500 text-center py-4">No recent subscriptions.</Text>
          }
          contentContainerStyle={{ paddingBottom: 100 }}
        />
      </View>
    </SafeAreaView>
  );
}
