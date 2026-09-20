import React, { FormEvent, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { BookOpen, CalendarDays, Pencil, Plus, Sparkles, TrendingUp, Trash2, X } from 'lucide-react';
import { blogApi, FinancialBlog, FinancialBlogInput } from '../api/blogApi';
import { useAuth } from '../context/AuthContext';
import { formatLocalizedDate, getLocalizedBlog } from '../utils/civicLocalization';

const blankForm: FinancialBlogInput = { title: '', summary: '', content: '' };

export const Blogs: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { role } = useAuth();
  const isAdmin = role === 'SYSTEM_ADMIN';
  const [blogs, setBlogs] = useState<FinancialBlog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState<FinancialBlog | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [form, setForm] = useState<FinancialBlogInput>(blankForm);
  const [saving, setSaving] = useState(false);

  const loadBlogs = async () => {
    setLoading(true);
    try { setBlogs(await blogApi.list()); setError(''); }
    catch { setError('Financial blogs could not be loaded right now. Please try again shortly.'); }
    finally { setLoading(false); }
  };
  useEffect(() => { loadBlogs(); }, []);

  const openEditor = (blog?: FinancialBlog) => {
    setEditing(blog || null);
    setIsEditorOpen(true);
    setForm(blog ? { title: blog.title, summary: blog.summary, content: blog.content } : blankForm);
    setError('');
  };
  const closeEditor = () => { setEditing(null); setForm(blankForm); setIsEditorOpen(false); };
  const save = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      const saved = editing ? await blogApi.update(editing.blog_id, form) : await blogApi.create(form);
      setBlogs(current => editing ? current.map(blog => blog.blog_id === saved.blog_id ? saved : blog) : [saved, ...current]);
      closeEditor();
    } catch (requestError: any) { setError(requestError?.userFriendlyMessage || 'Unable to save this blog post.'); }
    finally { setSaving(false); }
  };
  const remove = async (blog: FinancialBlog) => {
    if (!window.confirm(`Delete “${blog.title}”? This cannot be undone.`)) return;
    try { await blogApi.remove(blog.blog_id); setBlogs(current => current.filter(item => item.blog_id !== blog.blog_id)); }
    catch (requestError: any) { setError(requestError?.userFriendlyMessage || 'Unable to delete this blog post.'); }
  };

  return <div className="min-h-screen overflow-hidden bg-[#f8f6f1] text-slate-800">
    <section className="relative isolate overflow-hidden bg-[#071b2b] text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_12%_20%,rgba(215,131,45,.42),transparent_24%),radial-gradient(circle_at_85%_15%,rgba(120,35,53,.8),transparent_32%),linear-gradient(125deg,#071b2b_0%,#3c1424_48%,#861823_100%)]" />
      <div className="blog-orb blog-orb-one" /><div className="blog-orb blog-orb-two" />
      <div className="blog-enter relative mx-auto flex min-h-[400px] max-w-7xl flex-col justify-center px-5 py-16 sm:px-8 sm:py-20 lg:px-10">
        <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3.5 py-2 text-[11px] font-extrabold tracking-[.16em] text-amber-200"><Sparkles className="h-3.5 w-3.5" /> {t('blogs.journalTitle', 'YOJNASETU FINANCIAL JOURNAL')}</div>
        <h1 className="mt-6 max-w-3xl text-4xl font-black leading-[1.08] tracking-tight sm:text-6xl">{t('blogs.journalSubtitle', 'Money clarity for everyday India.')}</h1>
        <p className="mt-5 max-w-2xl text-base leading-7 text-white/75 sm:text-lg">{t('blogs.heroSubtitle', 'Thoughtful explainers on savings, credit, loans and government financial support—written to make every next step feel simpler.')}</p>
        <div className="mt-8 flex flex-wrap items-center gap-3 text-sm font-semibold text-white/85"><span className="inline-flex items-center gap-2"><TrendingUp className="h-4 w-4 text-amber-300" /> {t('blogs.practicalLiteracy', 'Practical financial literacy')}</span><span className="h-1 w-1 rounded-full bg-white/50" /><span>{blogs.length} published {blogs.length === 1 ? t('blogs.story', 'story') : t('blogs.stories', 'stories')}</span></div>
      </div>
    </section>
    <section className="max-w-7xl mx-auto px-5 sm:px-8 py-12 lg:px-10">
      <div className="flex items-center justify-between gap-4 mb-7">
        <p className="text-sm text-slate-600">{t('blogs.financialInformationPublished', 'Financial information published by YojnaSetu.')}</p>
        {isAdmin && <button onClick={() => openEditor()} className="inline-flex items-center gap-2 rounded-xl bg-[#861823] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#6f1420]"><Plus className="w-4 h-4" /> {t('blogs.newBlog', 'New blog')}</button>}
      </div>
      {error && <div className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}
      {loading ? <p className="py-12 text-center text-slate-500">{t('blogs.loading', 'Loading financial blogs…')}</p> : blogs.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500">{t('blogs.noBlogsPublished', 'No financial blogs have been published yet.')}</div> : <div className="grid gap-5 md:grid-cols-2">
        {blogs.map(blog => {
          const locBlog = getLocalizedBlog(blog, i18n.language);
          return <article key={blog.blog_id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex justify-between gap-3"><h2 className="text-xl font-extrabold text-slate-900">{locBlog.title}</h2>{isAdmin && <div className="flex shrink-0 gap-1"><button aria-label="Edit blog" onClick={() => openEditor(blog)} className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"><Pencil className="w-4 h-4" /></button><button aria-label="Delete blog" onClick={() => remove(blog)} className="rounded-lg p-2 text-red-600 hover:bg-red-50"><Trash2 className="w-4 h-4" /></button></div>}</div>
            <p className="mt-3 text-sm font-medium text-slate-600">{locBlog.summary}</p><p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-700">{blog.content}</p>
            <div className="mt-5 flex items-center gap-2 border-t pt-4 text-xs text-slate-500"><CalendarDays className="w-4 h-4" /> {formatLocalizedDate(blog.updated_at, i18n.language, { day: 'numeric', month: 'long', year: 'numeric' })} · {blog.author_name}</div>
          </article>;
        })}
      </div>}
    </section>
    {isAdmin && isEditorOpen && <div className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-950/60 p-4"><form onSubmit={save} className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl"><div className="flex items-center justify-between"><h2 className="text-xl font-extrabold">{editing ? 'Edit financial blog' : 'Create financial blog'}</h2><button type="button" onClick={closeEditor} className="rounded-lg p-2 hover:bg-slate-100"><X /></button></div><label className="mt-5 block text-sm font-bold">Title<input required minLength={3} maxLength={180} value={form.title} onChange={event => setForm({ ...form, title: event.target.value })} className="mt-1.5 w-full rounded-xl border border-slate-300 p-3 font-normal" /></label><label className="mt-4 block text-sm font-bold">Summary<input required minLength={10} maxLength={500} value={form.summary} onChange={event => setForm({ ...form, summary: event.target.value })} className="mt-1.5 w-full rounded-xl border border-slate-300 p-3 font-normal" /></label><label className="mt-4 block text-sm font-bold">Financial guidance<textarea required minLength={20} maxLength={50000} rows={10} value={form.content} onChange={event => setForm({ ...form, content: event.target.value })} className="mt-1.5 w-full rounded-xl border border-slate-300 p-3 font-normal" /></label><div className="mt-6 flex justify-end gap-3"><button type="button" onClick={closeEditor} className="rounded-xl border border-slate-300 px-4 py-2.5 font-bold">Cancel</button><button disabled={saving} className="rounded-xl bg-[#861823] px-4 py-2.5 font-bold text-white disabled:opacity-60">{saving ? 'Saving…' : 'Save blog'}</button></div></form></div>}
  </div>;
};
