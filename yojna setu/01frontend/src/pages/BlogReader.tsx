import React, { useEffect, useState } from 'react';
import { ArrowLeft, BookOpen, CalendarDays, Clock3, Share2 } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { blogApi, FinancialBlog } from '../api/blogApi';

const readingTime = (content: string) => Math.max(1, Math.ceil(content.trim().split(/\s+/).length / 200));

export const BlogReader: React.FC = () => {
  const { blogId } = useParams();
  const [blog, setBlog] = useState<FinancialBlog | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { if (blogId) blogApi.list().then(items => setBlog(items.find(item => item.blog_id === blogId) || null)).catch(() => setError('This story could not be loaded.')); }, [blogId]);
  if (error) return <div className="mx-auto max-w-xl p-12 text-center text-red-700">{error}</div>;
  if (!blog) return <div className="mx-auto max-w-xl p-12 text-center text-slate-500">Loading story...</div>;
  return <article className="min-h-screen bg-[#fef9f3] pb-20 text-slate-900"><header className="border-b border-[#f0dfe1] bg-white/80 backdrop-blur"><div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8"><Link to="/blogs" className="inline-flex items-center gap-2 text-sm font-bold text-[#861823]"><ArrowLeft className="h-4 w-4" /> All stories</Link><BookOpen className="h-5 w-5 text-[#861823]" /></div></header><div className="mx-auto max-w-5xl px-5 pt-14 sm:px-8 lg:px-10"><span className="rounded-full bg-[#f7e9e9] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[.14em] text-[#861823]">Financial guide</span><h1 className="mt-6 max-w-4xl font-serif text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">{blog.title}</h1><p className="mt-6 max-w-4xl text-lg leading-8 text-slate-600">{blog.summary}</p><div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-y border-[#f0dfe1] py-4 text-xs text-slate-500"><span>By {blog.author_name}</span><span className="flex items-center gap-4"><span className="inline-flex items-center gap-1"><CalendarDays className="h-4 w-4" /> {new Date(blog.updated_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</span><span className="inline-flex items-center gap-1"><Clock3 className="h-4 w-4" /> {readingTime(blog.content)} min</span><Share2 className="h-4 w-4" /></span></div><div className="mt-10 whitespace-pre-wrap font-serif text-lg leading-9 text-slate-700">{blog.content}</div></div></article>;
};
