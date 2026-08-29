import { apiClient } from './client';
import { TokenResponse, LoginRequest, RegisterRequest, User } from '../types';

export const authApi = {
  login: async (credentials: LoginRequest): Promise<TokenResponse> => {
    const payload = {
      identifier: credentials.identifier || credentials.username,
      password: credentials.password,
    };
    const response = await apiClient.post<TokenResponse>('/auth/login', payload);
    return response.data;
  },

  register: async (payload: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>('/auth/register', payload);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },
};
