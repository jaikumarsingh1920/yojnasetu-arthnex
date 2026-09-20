import React, { FormEvent, useEffect, useState } from 'react';
import { ArrowRight, BookOpen, CalendarDays, Clock3, Pencil, Plus, Search, ShieldCheck, Sparkles, Trash2, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { blogApi, FinancialBlog, FinancialBlogInput } from '../api/blogApi';
import { useAuth } from '../context/AuthContext';
import { formatLocalizedDate, getLocalizedBlog } from '../utils/civicLocalization';

const blankForm: FinancialBlogInput = { title: '', summary: '', content: '' };
const dateLabel = (date: string) => new Date(date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
const readingTime = (content: string) => Math.max(1, Math.ceil(content.trim().split(/\s+/).length / 200));

const CATEGORIES = [
  'All',
  'Eligibility & Rules',
  'Financial Literacy',
  'Loans & Subsidies',
  'Women & SHGs',
  'Students & Education',
  'Farmers & Rural',
  'MSME & Business',
  'Documents & Applications',
] as const;

const matchesCategory = (blog: FinancialBlog, category: string): boolean => {
  if (category === 'All') return true;
  const text = `${blog.title} ${blog.summary} ${blog.content}`.toLowerCase();
  switch (category) {
    case 'Eligibility & Rules':
      return text.includes('eligib') || text.includes('criteri') || text.includes('qualif') || text.includes('rule');
    case 'Financial Literacy':
      return text.includes('npa') || text.includes('crar') || text.includes('interest rate') || text.includes('financial literacy') || text.includes('repayment');
    case 'Loans & Subsidies':
      return text.includes('subsidy') || text.includes('subvention') || text.includes('margin money') || text.includes('capital subsidy');
    case 'Women & SHGs':
      return text.includes('women') || text.includes('shg') || text.includes('self-help') || text.includes('female');
    case 'Students & Education':
      return text.includes('student') || text.includes('scholarship') || text.includes('education') || text.includes('matric') || text.includes('csis');
    case 'Farmers & Rural':
      return text.includes('farmer') || text.includes('agri') || text.includes('rural') || text.includes('kisan') || text.includes('rrb') || text.includes('dairy');
    case 'MSME & Business':
      return text.includes('msme') || text.includes('mudra') || text.includes('pmegp') || text.includes('entrepreneur') || text.includes('business') || text.includes('cgtmse');
    case 'Documents & Applications':
      return text.includes('document') || text.includes('aadhaar') || text.includes('income certificate') || text.includes('caste') || text.includes('dbt') || text.includes('portal') || text.includes('application');
    default:
      return true;
  }
};

export const BlogsLanding: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { role } = useAuth();
  const isAdmin = role === 'SYSTEM_ADMIN';
  const [blogs, setBlogs] = useState<FinancialBlog[]>([]);
  const [query, setQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState<FinancialBlog | null>(null);
  const [form, setForm] = useState<FinancialBlogInput>(blankForm);
  const [editorOpen, setEditorOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = async () => { setLoading(true); try { setBlogs(await blogApi.list()); setError(''); } catch { setError('Stories could not be loaded right now.'); } finally { setLoading(false); } };
  useEffect(() => {
    document.title = 'Blog — YojnaSetu';
    load();
  }, []);
  const openEditor = (blog?: FinancialBlog) => { setEditing(blog || null); setForm(blog ? { title: blog.title, summary: blog.summary, content: blog.content } : blankForm); setEditorOpen(true); };
  const closeEditor = () => { setEditing(null); setForm(blankForm); setEditorOpen(false); };
  const save = async (event: FormEvent) => { event.preventDefault(); setSaving(true); try { const saved = editing ? await blogApi.update(editing.blog_id, form) : await blogApi.create(form); setBlogs(items => editing ? items.map(item => item.blog_id === saved.blog_id ? saved : item) : [saved, ...items]); closeEditor(); } catch (requestError: any) { setError(requestError?.userFriendlyMessage || 'Unable to save this story.'); } finally { setSaving(false); } };
  const remove = async (blog: FinancialBlog) => { if (!window.confirm(`Delete "${blog.title}"? This cannot be undone.`)) return; try { await blogApi.remove(blog.blog_id); setBlogs(items => items.filter(item => item.blog_id !== blog.blog_id)); } catch (requestError: any) { setError(requestError?.userFriendlyMessage || 'Unable to delete this story.'); } };
  
  const getCategoryLabel = (cat: string) => {
    switch (cat) {
      case 'All': return t('blog.allCategories');
      case 'Eligibility & Rules': return t('blog.catEligibility');
      case 'Financial Literacy': return t('blog.catFinancialLiteracy');
      case 'Loans & Subsidies': return t('blog.catLoansSubsidies');
      case 'Women & SHGs': return t('blog.catWomen');
      case 'Students & Education': return t('blog.catStudents');
      case 'Farmers & Rural': return t('blog.catFarmers');
      case 'MSME & Business': return t('blog.catMsme');
      case 'Documents & Applications': return t('blog.catDocuments');
      default: return cat;
    }
  };

  const visibleBlogs = blogs.filter(blog => {
    const matchesCat = matchesCategory(blog, selectedCategory);
    const q = query.trim().toLowerCase();
    const matchesQuery = !q || `${blog.title} ${blog.summary} ${blog.content}`.toLowerCase().includes(q);
    return matchesCat && matchesQuery;
  });

  return <div className="blog-page min-h-screen overflow-hidden bg-[#f8f6f1] text-slate-900">
    <section className="relative isolate overflow-hidden bg-[#861823] text-white"><div className="absolute inset-0 bg-[radial-gradient(circle_at_85%_10%,rgba(215,131,45,.35),transparent_24%),radial-gradient(circle_at_10%_90%,rgba(255,255,255,.12),transparent_28%)]" /><div className="relative mx-auto max-w-6xl px-5 py-16 sm:px-8 sm:py-20"><div className="max-w-3xl"><div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-[11px] font-bold uppercase tracking-[.15em] text-amber-200"><Sparkles className="h-3.5 w-3.5" /> {t('blog.editorialGuides')}</div><h1 className="mt-6 font-serif text-4xl font-semibold leading-tight sm:text-6xl">{t('blog.heroTitle')}</h1><p className="mt-5 max-w-2xl text-base leading-7 text-white/80 sm:text-lg">{t('blog.heroSubtitle')}</p>{isAdmin && <div className="mt-7 inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-xs text-white/85"><ShieldCheck className="h-4 w-4 text-amber-200" /> {t('blog.adminPrivileges')}</div>}</div></div></section>
    <main className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[.16em] text-[#861823]">{t('blog.latestStories')}</p><h2 className="mt-2 font-serif text-3xl font-semibold">{t('blog.subHeading')}</h2></div>{isAdmin && <button onClick={() => openEditor()} className="inline-flex items-center gap-2 rounded-full bg-[#861823] px-4 py-2.5 text-sm font-bold text-white shadow-md transition hover:bg-[#6f1420]"><Plus className="h-4 w-4" /> {t('blog.newStory')}</button>}</div>
      <div className="mt-6 flex flex-wrap gap-2">
        {CATEGORIES.map(category => (
          <button
            key={category}
            type="button"
            onClick={() => setSelectedCategory(category)}
            className={`px-3 py-1.5 rounded-full text-xs font-bold transition ${
              selectedCategory === category
                ? 'bg-[#861823] text-white shadow-sm'
                : 'bg-[#f7e9e9] text-[#861823] hover:bg-[#ebd4d7]'
            }`}
          >
            {getCategoryLabel(category)}
          </button>
        ))}
      </div>
      <div className="mt-6 flex flex-col gap-3 rounded-2xl bg-[#f7e9e9] p-3 sm:flex-row sm:items-center"><div className="relative flex-1"><Search className="absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" /><input value={query} onChange={event => setQuery(event.target.value)} placeholder={t('blog.searchPlaceholder')} className="w-full rounded-xl border-0 bg-white py-3 pl-11 pr-4 text-sm shadow-sm outline-none ring-[#861823] focus:ring-2" /></div><p className="px-2 text-xs font-semibold text-slate-500">{visibleBlogs.length === 1 ? t('blog.storyCount_one', { count: visibleBlogs.length }) : t('blog.storyCount_other', { count: visibleBlogs.length })}</p></div>
      {error && <p className="mt-6 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
      {loading ? <div className="mt-8 space-y-5"><div className="h-52 animate-pulse rounded-2xl bg-[#f2dddd]" /><div className="h-52 animate-pulse rounded-2xl bg-[#f2dddd]" /></div> : visibleBlogs.length === 0 ? <div className="mt-8 rounded-2xl border border-dashed border-[#c99da2] bg-white px-6 py-20 text-center"><BookOpen className="mx-auto h-8 w-8 text-[#861823]" /><h3 className="mt-4 font-serif text-2xl font-semibold">{t('blog.noStoriesFound')}</h3><p className="mt-2 text-sm text-slate-500">{t('blog.noStoriesDesc')}</p></div> : <div className="mt-8 space-y-5">{visibleBlogs.map(blog => {
        const locBlog = getLocalizedBlog(blog, i18n.language);
        return <article key={blog.blog_id} className="group w-full rounded-2xl bg-white p-6 shadow-sm ring-1 ring-[#f0dfe1] transition hover:-translate-y-0.5 hover:shadow-md sm:p-7"><div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between"><Link to={`/blogs/${blog.blog_id}`} className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-3"><span className="rounded-full bg-[#f7e9e9] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[.12em] text-[#861823]">{t('blog.financialGuideBadge')}</span><span className="inline-flex items-center gap-1 text-xs text-slate-500"><Clock3 className="h-3.5 w-3.5" /> {t('blog.readingTime', { count: readingTime(blog.content) })}</span></div><h3 className="mt-5 font-serif text-2xl font-semibold leading-tight text-slate-900 sm:text-3xl">{locBlog.title}</h3><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{locBlog.summary}</p><div className="mt-6 flex items-center justify-between border-t border-[#f5ebec] pt-4 text-xs text-slate-500"><span className="inline-flex items-center gap-1.5"><CalendarDays className="h-3.5 w-3.5 text-[#861823]" /> {formatLocalizedDate(blog.updated_at, i18n.language)}</span><span className="inline-flex items-center gap-1 font-bold text-[#861823]">{t('blog.readStory')} <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" /></span></div></Link>{isAdmin && <div className="flex shrink-0 gap-2 border-t border-[#f5ebec] pt-4 sm:border-l sm:border-t-0 sm:pl-5 sm:pt-0"><button aria-label="Edit story" onClick={() => openEditor(blog)} className="rounded-full bg-[#f7e9e9] p-2.5 text-[#861823] transition hover:bg-[#efd4d7]"><Pencil className="h-4 w-4" /></button><button aria-label="Delete story" onClick={() => remove(blog)} className="rounded-full bg-red-50 p-2.5 text-red-700 transition hover:bg-red-100"><Trash2 className="h-4 w-4" /></button></div>}</div></article>;
      })}</div>}
      <div className="mt-12 flex items-center gap-3 rounded-2xl bg-[#3c1424] p-6 text-white"><ShieldCheck className="h-7 w-7 shrink-0 text-amber-300" /><p className="text-sm leading-6 text-white/75">{t('blog.editorialDisclaimer')}</p></div>
    </main>
    {isAdmin && editorOpen && <div className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-950/60 p-4"><form onSubmit={save} className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl"><div className="flex items-center justify-between"><h2 className="font-serif text-2xl font-semibold">{editing ? t('blog.editStory') : t('blog.newStory')}</h2><button type="button" onClick={closeEditor} className="rounded-full p-2 hover:bg-slate-100"><X className="h-5 w-5" /></button></div><label className="mt-5 block text-sm font-bold">{t('common.title', 'Title')}<input required minLength={3} maxLength={180} value={form.title} onChange={event => setForm({ ...form, title: event.target.value })} className="mt-1.5 w-full rounded-xl border border-slate-300 p-3 font-normal" /></label><label className="mt-4 block text-sm font-bold">{t('common.summary', 'Summary')}<input required minLength={10} maxLength={500} value={form.summary} onChange={event => setForm({ ...form, summary: event.target.value })} className="mt-1.5 w-full rounded-xl border border-slate-300 p-3 font-normal" /></label><label className="mt-4 block text-sm font-bold">{t('blogs.financialGuidance', 'Financial guidance')}<textarea required minLength={20} maxLength={50000} rows={10} value={form.content} onChange={event => setForm({ ...form, content: event.target.value })} className="mt-1.5 w-full rounded-xl border border-slate-300 p-3 font-normal" /></label><div className="mt-6 flex justify-end gap-3"><button type="button" onClick={closeEditor} className="rounded-full border border-slate-300 px-4 py-2.5 font-bold">{t('common.cancel', 'Cancel')}</button><button disabled={saving} className="rounded-full bg-[#861823] px-5 py-2.5 font-bold text-white disabled:opacity-60">{saving ? t('common.saving', 'Saving...') : t('common.save', 'Save story')}</button></div></form></div>}
  </div>;
};
