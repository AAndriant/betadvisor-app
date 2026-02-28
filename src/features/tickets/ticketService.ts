import { api } from '../../services/api';

export const uploadTicket = async (imageUri: string) => {
    const formData = new FormData();

    // React Native specific FormData handling
    const filename = imageUri.split('/').pop();
    const match = /\.(\w+)$/.exec(filename || '');
    const type = match ? `image/${match[1]}` : 'image/jpeg';

    formData.append('image', {
        uri: imageUri,
        name: filename || 'ticket.jpg',
        type,
    } as any);

    const response = await api.post('/api/tickets/', formData);

    return response.data;
};
