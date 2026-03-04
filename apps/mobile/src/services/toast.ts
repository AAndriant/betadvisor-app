/**
 * S8-02: Global toast/snackbar service for the BetAdvisor mobile app.
 * Provides success, error, and info toast methods.
 * Integrates with Axios interceptor for automatic error handling.
 */
import Toast from 'react-native-toast-message';

export const showSuccessToast = (message: string, title?: string) => {
    Toast.show({
        type: 'success',
        text1: title || 'Succès',
        text2: message,
        position: 'top',
        visibilityTime: 3000,
        topOffset: 60,
    });
};

export const showErrorToast = (message: string, title?: string) => {
    Toast.show({
        type: 'error',
        text1: title || 'Erreur',
        text2: message,
        position: 'top',
        visibilityTime: 4000,
        topOffset: 60,
    });
};

export const showInfoToast = (message: string, title?: string) => {
    Toast.show({
        type: 'info',
        text1: title || 'Info',
        text2: message,
        position: 'top',
        visibilityTime: 3000,
        topOffset: 60,
    });
};

/**
 * Parse Axios error into a user-friendly message
 */
export const getErrorMessage = (error: any): string => {
    if (!error.response) {
        return 'Erreur réseau. Vérifiez votre connexion internet.';
    }

    const status = error.response.status;
    const data = error.response.data;

    switch (status) {
        case 400:
            if (data?.error) return data.error;
            if (data?.detail) return data.detail;
            return 'Données invalides. Vérifiez votre saisie.';
        case 401:
            return 'Session expirée. Reconnectez-vous.';
        case 403:
            return "Vous n'avez pas les droits pour cette action.";
        case 404:
            return 'Ressource introuvable.';
        case 409:
            return data?.error || 'Conflit — cette action a déjà été effectuée.';
        case 429:
            return 'Trop de requêtes. Patientez un moment.';
        case 500:
            return 'Erreur serveur. Réessayez dans quelques instants.';
        default:
            return data?.error || data?.detail || `Erreur inattendue (${status})`;
    }
};
