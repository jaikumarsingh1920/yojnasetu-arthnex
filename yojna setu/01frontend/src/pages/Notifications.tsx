import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bell, CheckCheck, Filter, ArrowRight, Settings, CheckCircle2, ShieldCheck, Mail, Phone, MessageSquare, Smartphone } from 'lucide-react';
import { notificationApi } from '../api/notificationApi';
import { NotificationItem, NotificationPreference } from '../types';
import { Alert } from '../components/Alert';

export const Notifications: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const urlTab = (searchParams.get('tab') as 'ALL' | 'UNREAD' | 'READ') || 'ALL';
  const urlType = searchParams.get('type') || '';
  const urlPage = parseInt(searchParams.get('page') || '1', 10);

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [page, setPage] = useState<number>(urlPage);
  const [tabFilter, setTabFilter] = useState<'ALL' | 'UNREAD' | 'READ'>(urlTab);
  const [typeFilter, setTypeFilter] = useState<string>(urlType);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    setTabFilter(urlTab);
    setTypeFilter(urlType);
    setPage(urlPage);
  }, [urlTab, urlType, urlPage]);

  const updateParams = (updates: { tab?: string; type?: string; page?: number }) => {
    const current = new URLSearchParams(searchParams);
    if ('tab' in updates) {
      if (updates.tab && updates.tab !== 'ALL') current.set('tab', updates.tab);
      else current.delete('tab');
    }
    if ('type' in updates) {
      if (updates.type) current.set('type', updates.type);
      else current.delete('type');
    }
    if ('page' in updates) {
      if (updates.page && updates.page > 1) current.set('page', String(updates.page));
      else current.delete('page');
    }
    setSearchParams(current, { replace: true });
  };

  // Preference state
  const [preferences, setPreferences] = useState<NotificationPreference | null>(null);
  const [isPrefModalOpen, setIsPrefModalOpen] = useState<boolean>(false);
  const [savingPref, setSavingPref] = useState<boolean>(false);

  useEffect(() => {
    fetchNotifications();
  }, [page, tabFilter, typeFilter]);

  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchNotifications = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      let isReadParam: boolean | undefined = undefined;
      if (tabFilter === 'UNREAD') isReadParam = false;
      if (tabFilter === 'READ') isReadParam = true;

      const data = await notificationApi.getNotifications({
        is_read: isReadParam,
        notification_type: typeFilter || undefined,
        page,
        page_size: 15
      });
      setNotifications(data.items);
      setTotalCount(data.total);
      setUnreadCount(data.unread_count);
    } catch (err: any) {
      setErrorMsg('Failed to load notifications. ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPreferences = async () => {
    try {
      const prefs = await notificationApi.getPreferences();
      setPreferences(prefs);
    } catch (err) {
      console.error('Failed to load preferences:', err);
    }
  };

  const handleMarkRead = async (item: NotificationItem) => {
    if (item.is_read) return;
    try {
      await notificationApi.markRead(item.notification_id);
      setNotifications(prev => prev.map(n => n.notification_id === item.notification_id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Mark read error:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationApi.markAllRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      setErrorMsg('Failed to mark all notifications as read.');
    }
  };

  const handleNotificationClick = async (item: NotificationItem) => {
    await handleMarkRead(item);
    let targetUrl = item.application_id ? `/applications/${item.application_id}` : '/notifications';
    if (item.metadata_json) {
      try {
        const meta = JSON.parse(item.metadata_json);
        if (meta.deep_link) targetUrl = meta.deep_link;
      } catch (e) {}
    }
    if (item.application_id) {
      navigate(targetUrl);
    }
  };

  const handleTogglePref = async (key: keyof NotificationPreference) => {
    if (!preferences) return;
    const updated = { ...preferences, [key]: !preferences[key] };
    setPreferences(updated);
    setSavingPref(true);
    try {
      await notificationApi.updatePreferences({ [key]: updated[key] });
    } catch (err) {
      console.error('Preference update failed:', err);
    } finally {
      setSavingPref(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#4A2525] via-[#3B2522] to-[#4A2525] text-white p-6 sm:p-8 rounded-2xl shadow-warm-md border border-[#E8D8D2]/20 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="inline-flex items-center gap-2 bg-[#FFF4EC]/15 text-[#FFD0CA] text-xs font-bold px-3 py-1 rounded-full mb-2 border border-[#FFD0CA]/20">
            <Bell className="w-4 h-4 text-[#F7AE56]" />
            {t('notifications.centerBadge', 'Communication & Notification Center')}
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">{t('notifications.title', 'Notifications & Application Alerts')}</h1>
          <p className="text-xs sm:text-sm text-[#FFD0CA] mt-1">
            {t('notifications.subtitle', 'Real-time status updates for applications, document verification results, and authority reviews.')}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full md:w-auto">
          <button
            onClick={() => setIsPrefModalOpen(true)}
            className="bg-white/10 hover:bg-white/20 text-white text-xs font-bold px-4 py-2.5 rounded-xl border border-white/20 shadow-warm-xs transition flex items-center justify-center gap-1.5 min-h-[44px]"
          >
            <Settings className="w-4 h-4 text-[#F7AE56]" /> {t('notifications.deliveryPreferences', 'Delivery Preferences')}
          </button>

          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-warm-xs transition flex items-center justify-center gap-1.5 min-h-[44px]"
            >
              <CheckCheck className="w-4 h-4" /> {t('notifications.markAllRead', 'Mark All as Read')}
            </button>
          )}
        </div>
      </div>

      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* Main Grid */}
      <div className="bg-white p-4 sm:p-6 rounded-2xl border border-[#E8D8D2] shadow-warm-xs space-y-5 sm:space-y-6">
        {/* Controls & Filter Bar */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-[#E8D8D2] pb-4">
          {/* Status Tabs */}
          <div className="flex gap-2">
            {(['ALL', 'UNREAD', 'READ'] as const).map(st => (
              <button
                key={st}
                onClick={() => { setTabFilter(st); setPage(1); updateParams({ tab: st, page: 1 }); }}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                  tabFilter === st ? 'bg-[#4A2525] text-white shadow-warm-xs' : 'bg-[#FFF4EC] text-[#765E59] hover:bg-[#FFD0CA]/40'
                }`}
              >
                {st === 'ALL' ? t('common.all', 'ALL') : st === 'UNREAD' ? t('common.unread', 'UNREAD') : t('common.read', 'READ')}
                {st === 'UNREAD' && unreadCount > 0 && (
                  <span className="bg-[#EA717B] text-white text-[10px] px-1.5 py-0.2 rounded-full font-extrabold">
                    {unreadCount}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Type Filter Dropdown */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-[#765E59]" />
            <select
              value={typeFilter}
              onChange={(e) => {
                const val = e.target.value;
                setTypeFilter(val);
                setPage(1);
                updateParams({ type: val, page: 1 });
              }}
              className="px-3 py-2 rounded-xl border border-[#E8D8D2] text-xs font-bold bg-white text-[#3B2522] outline-none focus:ring-2 focus:ring-[#EA717B]/20 focus:border-[#EA717B]"
            >
              <option value="">{t('notifications.allTypes', 'All Notification Types')}</option>
              <option value="APPLICATION_SUBMITTED">{t('notifications.submitted', 'Submitted')}</option>
              <option value="APPLICATION_UNDER_REVIEW">{t('notifications.underReview', 'Under Review')}</option>
              <option value="DOCUMENT_VERIFIED">{t('notifications.docVerified', 'Document Verified')}</option>
              <option value="DOCUMENT_REJECTED">{t('notifications.docRejected', 'Document Rejected')}</option>
              <option value="CORRECTION_REQUIRED">{t('notifications.correctionReq', 'Correction Required')}</option>
              <option value="APPLICATION_RESUBMITTED">{t('notifications.resubmitted', 'Resubmitted')}</option>
              <option value="APPLICATION_APPROVED">{t('notifications.approved', 'Approved')}</option>
              <option value="APPLICATION_REJECTED">{t('notifications.rejected', 'Rejected')}</option>
            </select>
          </div>
        </div>

        {/* List */}
        {isLoading ? (
          <div className="py-16 text-center">
            <div className="w-8 h-8 border-4 border-[#EA717B] border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs text-[#765E59] mt-2 font-medium">{t('notifications.loading', 'Loading notifications...')}</p>
          </div>
        ) : notifications.length === 0 ? (
          <div className="py-16 text-center space-y-2">
            <Bell className="w-12 h-12 text-[#E8D8D2] mx-auto mb-2" />
            <h3 className="text-base font-bold text-[#3B2522]">{t('notifications.noNotifications', 'No Notifications Found')}</h3>
            <p className="text-xs text-[#765E59] max-w-sm mx-auto">
              {t('notifications.allCaughtUp', "You're all caught up with your updates.")}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {notifications.map((item) => (
              <div
                key={item.notification_id}
                onClick={() => handleNotificationClick(item)}
                className={`p-5 rounded-2xl border transition flex flex-col md:flex-row justify-between items-start md:items-center gap-4 cursor-pointer ${
                  !item.is_read
                    ? 'bg-[#FFF4EC]/70 border-[#EA717B]/40 shadow-warm-xs'
                    : 'bg-white border-[#E8D8D2] hover:bg-[#FFFBF0]'
                }`}
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2">
                    {!item.is_read && (
                      <span className="w-2.5 h-2.5 rounded-full bg-[#EA717B] shrink-0" />
                    )}
                    <h3 className="text-sm font-bold text-[#3B2522]">{item.title}</h3>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded-lg border uppercase ${
                      item.priority === 'URGENT'
                        ? 'bg-[#FFD0CA] text-[#4A2525] border-[#EA717B]/30'
                        : item.priority === 'HIGH'
                        ? 'bg-[#F7AE56]/20 text-[#4A2525] border-[#F7AE56]/40'
                        : 'bg-[#FFF4EC] text-[#765E59] border-[#E8D8D2]'
                    }`}>
                      {item.priority === 'URGENT' ? t('notifications.urgent', 'URGENT') : item.priority === 'HIGH' ? t('notifications.high', 'HIGH') : item.priority}
                    </span>
                  </div>

                  <p className="text-xs text-[#765E59] leading-relaxed">{item.message}</p>

                  <div className="flex items-center gap-3 text-[11px] text-[#765E59]/70 font-mono pt-1">
                    <span>{new Date(item.created_at).toLocaleString()}</span>
                    <span>Channel: {item.channel}</span>
                    {item.application_id && <span>App ID: {item.application_id}</span>}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {item.application_id && (
                    <button className="bg-[#EA717B] hover:bg-[#d65f69] text-white text-xs font-bold px-4 py-2 rounded-xl transition shadow-warm-xs flex items-center gap-1">
                      {t('common.openDetails', 'Open Details')} <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Preferences Modal */}
      {isPrefModalOpen && preferences && (
        <div className="fixed inset-0 bg-[#3B2522]/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-2xl max-w-md w-full space-y-6 shadow-warm-xl border border-[#E8D8D2] text-[#3B2522]">
            <div className="flex justify-between items-center border-b border-[#E8D8D2] pb-3">
              <h3 className="text-base font-bold flex items-center gap-2 text-[#3B2522]">
                <Settings className="w-5 h-5 text-[#EA717B]" />
                {t('notifications.deliveryPreferences', 'Notification Delivery Preferences')}
              </h3>
              <button
                onClick={() => setIsPrefModalOpen(false)}
                className="text-[#765E59] hover:text-[#3B2522] font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-[#765E59]">
              {t('notifications.prefModalDesc', 'Configure delivery channels for real-time application updates and verification alerts.')}
            </p>

            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-[#FFFBF0] rounded-xl border border-[#E8D8D2]">
                <div className="flex items-center gap-3">
                  <Bell className="w-4 h-4 text-[#EA717B]" />
                  <div>
                    <p className="text-xs font-bold text-[#3B2522]">{t('notifications.inAppTitle', 'In-App Notifications')}</p>
                    <p className="text-[10px] text-[#765E59]">{t('notifications.inAppDesc', 'Header bell & portal alerts')}</p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.in_app_enabled}
                  onChange={() => handleTogglePref('in_app_enabled')}
                  className="w-4 h-4 accent-[#EA717B] cursor-pointer"
                />
              </div>

              <div className="flex justify-between items-center p-3 bg-[#FFFBF0] rounded-xl border border-[#E8D8D2]">
                <div className="flex items-center gap-3">
                  <Mail className="w-4 h-4 text-[#F7AE56]" />
                  <div>
                    <p className="text-xs font-bold text-[#3B2522]">{t('notifications.emailTitle', 'Email Notifications')}</p>
                    <p className="text-[10px] text-[#765E59]">{t('notifications.emailDesc', 'Email status updates (Adapter ready)')}</p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.email_enabled}
                  onChange={() => handleTogglePref('email_enabled')}
                  className="w-4 h-4 accent-[#EA717B] cursor-pointer"
                />
              </div>

              <div className="flex justify-between items-center p-3 bg-[#FFFBF0] rounded-xl border border-[#E8D8D2]">
                <div className="flex items-center gap-3">
                  <Phone className="w-4 h-4 text-emerald-600" />
                  <div>
                    <p className="text-xs font-bold text-[#3B2522]">{t('notifications.smsTitle', 'SMS Alerts')}</p>
                    <p className="text-[10px] text-[#765E59]">{t('notifications.smsDesc', 'Mobile SMS alerts (Adapter ready)')}</p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.sms_enabled}
                  onChange={() => handleTogglePref('sms_enabled')}
                  className="w-4 h-4 accent-[#EA717B] cursor-pointer"
                />
              </div>

              <div className="flex justify-between items-center p-3 bg-[#FFFBF0] rounded-xl border border-[#E8D8D2]">
                <div className="flex items-center gap-3">
                  <MessageSquare className="w-4 h-4 text-emerald-600" />
                  <div>
                    <p className="text-xs font-bold text-[#3B2522]">{t('notifications.whatsAppTitle', 'WhatsApp Updates')}</p>
                    <p className="text-[10px] text-[#765E59]">{t('notifications.whatsAppDesc', 'WhatsApp Business notifications')}</p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.whatsapp_enabled}
                  onChange={() => handleTogglePref('whatsapp_enabled')}
                  className="w-4 h-4 accent-[#EA717B] cursor-pointer"
                />
              </div>

              <div className="flex justify-between items-center p-3 bg-[#FFFBF0] rounded-xl border border-[#E8D8D2]">
                <div className="flex items-center gap-3">
                  <Smartphone className="w-4 h-4 text-[#EA717B]" />
                  <div>
                    <p className="text-xs font-bold text-[#3B2522]">{t('notifications.mobilePushTitle', 'Mobile Push')}</p>
                    <p className="text-[10px] text-[#765E59]">{t('notifications.mobilePushDesc', 'Device push notifications')}</p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.push_enabled}
                  onChange={() => handleTogglePref('push_enabled')}
                  className="w-4 h-4 accent-[#EA717B] cursor-pointer"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-[#E8D8D2]">
              <button
                onClick={() => setIsPrefModalOpen(false)}
                className="bg-[#EA717B] hover:bg-[#d65f69] text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-warm-xs transition"
              >
                {t('notifications.savePreferences', 'Close & Save Preferences')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
