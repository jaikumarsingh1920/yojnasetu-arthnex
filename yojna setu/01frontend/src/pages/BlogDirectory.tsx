import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowRight, BookOpen, CalendarDays, Clock3, LayoutDashboard, Search, ShieldCheck, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { blogApi, FinancialBlog } from '../api/blogApi';
import { useAuth } from '../context/AuthContext';

const dateLabel = (date: string) => new Date(date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
const readingTime = (content: string) => Math.max(1, Math.ceil(content.trim().split(/\s+/).length / 200));

export const BlogDirectory: React.FC = () => {
  const { t } = useTranslation();
  const { role } = useAuth();
  const [blogs, setBlogs] = useState<FinancialBlog[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => { blogApi.list().then(setBlogs).catch(() => setError('Stories could not be loaded right now.')).finally(() => setLoading(false)); }, []);
  const visibleBlogs = blogs.filter(blog => `${blog.title} ${blog.summary}`.toLowerCase().includes(query.toLowerCase()));

  return <div className="min-h-screen bg-[#f9f9ff] text-[#111c2d]">
    <section className="border-b border-[#d8e3fb] bg-white/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-5 sm:px-8"><div className="flex items-center gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#006c49] text-white"><BookOpen className="h-5 w-5" /></div><div><p className="font-serif text-xl font-bold tracking-tight">{t('blogs.journalTitle', 'YojnaSetu Journal')}</p><p className="text-xs text-slate-500">{t('blogs.journalSubtitle', 'Financial literacy, made practical')}</p></div></div>{role === 'SYSTEM_ADMIN' && <Link to="/admin/blogs" className="inline-flex items-center gap-2 rounded-full bg-[#e7eeff] px-3.5 py-2 text-xs font-bold text-[#111c2d] transition hover:bg-[#d8e3fb]"><LayoutDashboard className="h-4 w-4" /> Editorial workspace</Link>}</div>
    </section>
    <main className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
      <div className="max-w-2xl"><div className="inline-flex items-center gap-2 rounded-full bg-[#6cf8bb]/20 px-3 py-1.5 text-[11px] font-bold uppercase tracking-[.14em] text-[#006c49]"><Sparkles className="h-3.5 w-3.5" /> {t('blogs.financialGuidance', 'Financial guides')}</div><h1 className="mt-5 font-serif text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">{t('blogs.heroTitle', 'Clearer money decisions begin here.')}</h1><p className="mt-4 text-base leading-7 text-slate-600">{t('blogs.heroSubtitle', 'Short, trustworthy explainers on budgeting, borrowing, savings and government support.')}</p></div>
      <div className="mt-9 flex flex-col gap-3 rounded-2xl bg-[#f0f3ff] p-3 sm:flex-row sm:items-center sm:justify-between"><div className="relative flex-1"><Search className="absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" /><input value={query} onChange={event => setQuery(event.target.value)} placeholder={t('blogs.searchPlaceholder', 'Search financial guides...')} className="w-full rounded-xl border-0 bg-white py-3 pl-11 pr-4 text-sm shadow-sm outline-none ring-[#006c49] focus:ring-2" /></div><p className="px-2 text-xs font-semibold text-slate-500">{visibleBlogs.length} {visibleBlogs.length === 1 ? t('blogs.story', 'story') : t('blogs.stories', 'stories')}</p></div>
      {error && <p className="mt-6 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
      {loading ? <div className="mt-8 grid gap-4 md:grid-cols-2"><div className="h-64 animate-pulse rounded-2xl bg-[#e7eeff]" /><div className="h-64 animate-pulse rounded-2xl bg-[#e7eeff]" /></div> : visibleBlogs.length === 0 ? <div className="mt-8 rounded-2xl border border-dashed border-[#c6c6cd] bg-white px-6 py-20 text-center"><BookOpen className="mx-auto h-8 w-8 text-[#006c49]" /><h2 className="mt-4 font-serif text-2xl font-semibold">{t('blogs.noStoriesFound', 'No stories found')}</h2><p className="mt-2 text-sm text-slate-500">{t('blogs.noStoriesFoundDesc', 'Try a different search or check back when new guides are published.')}</p></div> : <div className="mt-8 grid gap-5 md:grid-cols-2">
        {visibleBlogs.map((blog, index) => <Link key={blog.blog_id} to={`/blogs/${blog.blog_id}`} className={`group rounded-2xl bg-white p-6 shadow-sm ring-1 ring-[#d8e3fb] transition hover:-translate-y-1 hover:shadow-lg ${index === 0 ? 'md:col-span-2' : ''}`}><div className="flex items-start justify-between gap-4"><span className="rounded-full bg-[#6cf8bb]/20 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[.12em] text-[#006c49]">{t('blogs.financialGuidance', 'Financial guide')}</span><span className="inline-flex items-center gap-1 text-xs text-slate-500"><Clock3 className="h-3.5 w-3.5" /> {readingTime(blog.content)} {t('blogs.minRead', 'min read')}</span></div><h2 className={`${index === 0 ? 'mt-5 font-serif text-3xl sm:text-4xl' : 'mt-5 font-serif text-2xl'} font-semibold leading-tight text-[#111c2d]`}>{blog.title}</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">{blog.summary}</p><div className="mt-6 flex items-center justify-between border-t border-[#edf1fb] pt-4 text-xs text-slate-500"><span className="inline-flex items-center gap-1.5"><CalendarDays className="h-3.5 w-3.5 text-[#006c49]" /> {dateLabel(blog.updated_at)}</span><span className="inline-flex items-center gap-1 font-bold text-[#006c49]">{t('blogs.readStory', 'Read story')} <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" /></span></div></Link>)}
      </div>}
      <div className="mt-12 flex items-center gap-3 rounded-2xl bg-[#131b2e] p-6 text-white"><ShieldCheck className="h-7 w-7 shrink-0 text-[#6cf8bb]" /><p className="text-sm leading-6 text-white/75">{t('blogs.editorialDisclaimer', 'Every guide is published by the YojnaSetu editorial team. We focus on plain-language financial education, not personal financial advice.')}</p></div>
    </main>
  </div>;
};
