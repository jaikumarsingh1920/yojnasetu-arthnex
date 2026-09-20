import React, { useEffect, useState } from 'react';
import { ArrowLeft, BookOpen, CalendarDays, Clock3, Share2, ShieldCheck, Sparkles, Calculator, MapPin } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { blogApi, FinancialBlog } from '../api/blogApi';
import { formatLocalizedDate, getLocalizedBlog } from '../utils/civicLocalization';

const readingTime = (content: string) => Math.max(1, Math.ceil(content.trim().split(/\s+/).length / 200));

export const BlogReader: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { blogId } = useParams();
  const [blog, setBlog] = useState<FinancialBlog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!blogId) {
      setError(t('blog.storyNotFound'));
      setLoading(false);
      return;
    }

    setLoading(true);
    setError('');
    blogApi.get(blogId)
      .then((data) => {
        setBlog(data);
        if (data?.title) {
          document.title = `${data.title} — YojnaSetu Editorial`;
        }
      })
      .catch(() => setError(t('blog.storyNotFound')))
      .finally(() => setLoading(false));
  }, [blogId, t]);

  const handleShare = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  if (error) return (
    <div className="mx-auto max-w-xl p-12 text-center text-red-700">
      <p className="text-base font-bold">{error}</p>
      <Link to="/blogs" className="mt-4 inline-flex items-center gap-1.5 text-xs font-bold text-[#861823] underline">
        <ArrowLeft className="w-3.5 h-3.5" /> {t('blog.backToAll')}
      </Link>
    </div>
  );

  if (loading) return (
    <div className="mx-auto max-w-xl p-16 text-center text-slate-500">
      <div className="w-8 h-8 mx-auto border-2 border-[#861823] border-t-transparent rounded-full animate-spin mb-4" />
      <p className="text-sm font-medium">{t('blog.loadingGuide')}</p>
    </div>
  );

  if (!blog) return (
    <div className="mx-auto max-w-xl p-12 text-center text-slate-500">
      <p className="text-base">{t('blog.storyNotFound')}</p>
      <Link to="/blogs" className="mt-4 inline-flex items-center gap-1.5 text-xs font-bold text-[#861823] underline">
        <ArrowLeft className="w-3.5 h-3.5" /> {t('blog.backToAll')}
      </Link>
    </div>
  );

  return (
    <article className="min-h-screen bg-[#fef9f3] pb-20 text-slate-900">
      {/* Top Header */}
      <header className="border-b border-[#f0dfe1] bg-white/90 backdrop-blur sticky top-0 z-20">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3.5 sm:px-8">
          <Link to="/blogs" className="inline-flex items-center gap-2 text-xs sm:text-sm font-bold text-[#861823] hover:text-[#6f1420] transition">
            <ArrowLeft className="h-4 w-4" /> {t('blog.backToAll')}
          </Link>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleShare}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#f0dfe1] bg-[#f7e9e9] text-xs font-semibold text-[#861823] hover:bg-[#ebd4d7] transition"
              title="Copy link to guide"
            >
              <Share2 className="h-3.5 w-3.5" />
              <span>{copied ? t('blog.linkCopied') : t('blog.share')}</span>
            </button>
            <BookOpen className="h-5 w-5 text-[#861823]" />
          </div>
        </div>
      </header>

      {/* Article Body */}
      <div className="mx-auto max-w-4xl px-5 pt-10 sm:px-8 lg:px-10">
        <div className="inline-flex items-center gap-2 rounded-full bg-[#f7e9e9] px-3 py-1 text-[11px] font-bold uppercase tracking-[.14em] text-[#861823]">
          <Sparkles className="w-3 h-3" />
          <span>{t('blog.financialGuideBadge')}</span>
        </div>

        {(() => {
          const locBlog = getLocalizedBlog(blog, i18n.language);
          return (
            <>
              <h1 className="mt-4 font-serif text-3xl font-black leading-tight tracking-tight text-slate-900 sm:text-5xl">
                {locBlog.title}
              </h1>
              <p className="mt-4 text-base sm:text-lg leading-relaxed text-slate-600 font-medium">
                {locBlog.summary}
              </p>
            </>
          );
        })()}

        {/* Metadata Bar */}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-y border-[#f0dfe1] py-3.5 text-xs text-slate-500">
          <span className="font-semibold text-slate-700">By {blog.author_name}</span>
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1">
              <CalendarDays className="h-3.5 w-3.5 text-[#861823]" />
              {formatLocalizedDate(blog.updated_at, i18n.language, { day: 'numeric', month: 'long', year: 'numeric' })}
            </span>
            <span className="inline-flex items-center gap-1">
              <Clock3 className="h-3.5 w-3.5 text-[#861823]" />
              {t('blog.readingTime', { count: readingTime(blog.content) })}
            </span>
          </div>
        </div>

        {/* Main Content Render */}
        <div className="mt-8 space-y-4 text-base leading-relaxed text-slate-800 whitespace-pre-wrap font-sans">
          {blog.content}
        </div>

        {/* Citizen Educational Disclaimer */}
        <div className="mt-12 rounded-2xl border border-[#e8d8d2] bg-white p-6 shadow-warm-xs">
          <div className="flex items-start gap-3.5">
            <ShieldCheck className="h-6 w-6 shrink-0 text-[#861823] mt-0.5" />
            <div className="space-y-1 text-xs sm:text-sm text-slate-600 leading-relaxed">
              <p className="font-bold text-slate-900">
                Official Information & Eligibility Disclaimer
              </p>
              <p>
                {t('blog.editorialDisclaimer')}
              </p>
            </div>
          </div>
        </div>

        {/* Related YojnaSetu Civic Tools Strip */}
        <div className="mt-8 rounded-2xl bg-[#f7e9e9]/60 border border-[#f0dfe1] p-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#861823] mb-3">
            Explore Related Civic Tools
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Link
              to="/recommendations"
              className="p-3 bg-white rounded-xl border border-[#e8d8d2] hover:border-[#861823] hover:shadow-warm-xs transition flex items-center gap-2.5 text-xs font-bold text-slate-800"
            >
              <Sparkles className="w-4 h-4 text-[#861823] shrink-0" />
              <span>{t('common.checkEligibility')}</span>
            </Link>
            <Link
              to="/calculator"
              className="p-3 bg-white rounded-xl border border-[#e8d8d2] hover:border-[#861823] hover:shadow-warm-xs transition flex items-center gap-2.5 text-xs font-bold text-slate-800"
            >
              <Calculator className="w-4 h-4 text-[#861823] shrink-0" />
              <span>{t('calculator.title')}</span>
            </Link>
            <Link
              to="/channel-partners"
              className="p-3 bg-white rounded-xl border border-[#e8d8d2] hover:border-[#861823] hover:shadow-warm-xs transition flex items-center gap-2.5 text-xs font-bold text-slate-800"
            >
              <MapPin className="w-4 h-4 text-[#861823] shrink-0" />
              <span>{t('nav.nearbyPartners')}</span>
            </Link>
          </div>
        </div>

        {/* Bottom Back Button */}
        <div className="mt-8 text-center">
          <Link
            to="/blogs"
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-[#861823] hover:bg-[#6f1420] text-white text-xs font-bold shadow-warm-xs transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{t('blog.backToAll')}</span>
          </Link>
        </div>
      </div>
    </article>
  );
};
