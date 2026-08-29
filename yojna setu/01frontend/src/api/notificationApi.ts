import { apiClient } from './client';
import {
  NotificationItem,
  PaginatedNotificationListResponse,
  NotificationPreference,
} from '../types';

export const notificationApi = {
  getNotifications: async (params?: { is_read?: boolean; notification_type?: string; page?: number; page_size?: number }): Promise<PaginatedNotificationListResponse> => {
    const response = await apiClient.get<PaginatedNotificationListResponse>('/notifications', { params });
    return response.data;
  },

  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    const response = await apiClient.get<{ unread_count: number }>('/notifications/unread-count');
    return response.data;
  },

  markRead: async (notificationId: string): Promise<NotificationItem> => {
    const response = await apiClient.post<NotificationItem>(`/notifications/${notificationId}/read`);
    return response.data;
  },

  markAllRead: async (): Promise<{ message: string; count: number }> => {
    const response = await apiClient.post<{ message: string; count: number }>('/notifications/read-all');
    return response.data;
  },

  getNotificationDetail: async (notificationId: string): Promise<NotificationItem> => {
    const response = await apiClient.get<NotificationItem>(`/notifications/${notificationId}`);
    return response.data;
  },

  getPreferences: async (): Promise<NotificationPreference> => {
    const response = await apiClient.get<NotificationPreference>('/notifications/preferences');
    return response.data;
  },

  updatePreferences: async (payload: Partial<NotificationPreference>): Promise<NotificationPreference> => {
    const response = await apiClient.put<NotificationPreference>('/notifications/preferences', payload);
    return response.data;
  },
};
