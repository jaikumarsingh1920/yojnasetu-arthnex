import { apiClient } from './client';

export interface FinancialBlog {
  blog_id: string;
  title: string;
  summary: string;
  content: string;
  author_name: string;
  created_at: string;
  updated_at: string;
}

export interface FinancialBlogInput {
  title: string;
  summary: string;
  content: string;
}

export const blogApi = {
  list: async (): Promise<FinancialBlog[]> => (await apiClient.get('/blogs')).data,
  create: async (data: FinancialBlogInput): Promise<FinancialBlog> => (await apiClient.post('/admin/blogs', data)).data,
  update: async (blogId: string, data: FinancialBlogInput): Promise<FinancialBlog> => (await apiClient.put(`/admin/blogs/${blogId}`, data)).data,
  remove: async (blogId: string): Promise<void> => { await apiClient.delete(`/admin/blogs/${blogId}`); },
};
