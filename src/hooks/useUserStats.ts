import { useQuery } from '@tanstack/react-query';
import { fetchMyProfile } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const useUserStats = () => {
  const { accessToken } = useAuth();

  return useQuery({
    queryKey: ['myProfile'],
    queryFn: fetchMyProfile,
    retry: 1, // On ne réessaie qu'une fois en cas d'erreur
    enabled: !!accessToken, // Ne lance la requête que si l'utilisateur est authentifié
  });
};
