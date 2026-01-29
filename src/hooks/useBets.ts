import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchBets, createBet, uploadTicketImage, pollTicketStatus } from '../services/api';
import { Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { useState } from 'react';

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

export const useAnalyzeTicket = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const analyze = async (formData: FormData) => {
    setIsAnalyzing(true);
    try {
      // 1. Upload
      const { ticket_id } = await uploadTicketImage(formData);

      // 2. Polling (boucle simple pour l'exemple)
      let attempts = 0;
      while (attempts < 10) { // Max 20 secondes
        await new Promise(r => setTimeout(r, 2000)); // Attendre 2s
        const statusData = await pollTicketStatus(ticket_id);

        if (statusData.status === 'VALIDATED') {
          setIsAnalyzing(false);
          return statusData.ocr_data; // { match: "Real vs Barça", odds: 1.80 ... }
        }
        if (statusData.status === 'REJECTED') {
          setIsAnalyzing(false);
          throw new Error("Analyse échouée");
        }
        attempts++;
      }
      setIsAnalyzing(false);
      throw new Error("Délai d'attente dépassé");
    } catch (e) {
      setIsAnalyzing(false);
      throw e;
    }
  };

  return { analyze, isAnalyzing };
};
