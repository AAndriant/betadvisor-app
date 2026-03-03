import { useEffect, useState } from "react";
import { View, Text, FlatList, ActivityIndicator } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { getDashboard, DashboardData } from "../../src/services/api";

export default function DashboardScreen() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((error) => console.error("Error fetching dashboard:", error))
      .finally(() => setLoading(false));
  }, []);

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

        <Text className="text-white font-bold text-lg mb-2">Recent Subscribers</Text>
        <FlatList
          data={data?.recent_subscriptions}
          keyExtractor={(item, index) => `${item.tipster}-${index}`}
          renderItem={({ item }) => (
            <View className="bg-slate-900 rounded-xl p-4 mb-2 flex-row justify-between items-center border border-slate-800">
              <View>
                <Text className="text-white font-semibold">Tipster ID: {item.tipster}</Text>
                <Text className="text-slate-400 text-sm">Status: {item.status}</Text>
              </View>
              {item.current_period_end && (
                 <Text className="text-slate-500 text-xs">
                    Ends: {new Date(item.current_period_end).toLocaleDateString()}
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
