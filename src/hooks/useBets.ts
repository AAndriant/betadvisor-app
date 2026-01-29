import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchBets, createBet } from '../services/api';
import { Alert } from 'react-native';
import { useRouter } from 'expo-router';

export const useFeed = () => {
  return useQuery({
    queryKey: ['feed'],
    queryFn: fetchBets,
  });
};

export const useCreateBet = () => {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: createBet,
    onSuccess: () => {
      // Invalide le cache pour rafraîchir le feed et le profil immédiatement
      queryClient.invalidateQueries({ queryKey: ['feed'] });
      queryClient.invalidateQueries({ queryKey: ['myProfile'] });
      Alert.alert("Succès", "Ton pari est en ligne !");
      router.back(); // Ferme la modale
    },
    onError: (error) => {
      console.error(error);
      Alert.alert("Erreur", "Impossible de publier le pari.");
    }
  });
};
