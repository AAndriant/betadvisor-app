import { useQuery } from '@tanstack/react-query';
import { fetchMyProfile } from '../services/api';

export const useUserStats = () => {
  return useQuery({
    queryKey: ['myProfile'],
    queryFn: fetchMyProfile,
    retry: 1, // On ne réessaie qu'une fois en cas d'erreur
  });
};
