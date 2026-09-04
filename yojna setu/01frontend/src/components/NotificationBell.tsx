import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bell, CheckCheck, ExternalLink, ShieldAlert, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';
import { notificationApi } from '../api/notificationApi';
import { NotificationItem } from '../types';

export const NotificationBell: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [recentNotifications, setRecentNotifications] = useState<NotificationItem[]>([]);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 15000); // 15s refetch
    return () => clearInterval(interval);
  }, []);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const res = await notificationApi.getUnreadCount();
      setUnreadCount(res.unread_count);
    } catch (err) {
      // Silent error for polling
    }
  };

  const handleToggleOpen = async () => {
    const nextState = !isOpen;
    setIsOpen(nextState);
    if (nextState) {
      setIsLoading(true);
      try {
        const data = await notificationApi.getNotifications({ page: 1, page_size: 5 });
        setRecentNotifications(data.items);
        setUnreadCount(data.unread_count);
      } catch (err) {
        console.error('Failed to load recent notifications:', err);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleMarkAsRead = async (e: React.MouseEvent, item: NotificationItem) => {
    e.stopPropagation();
    if (item.is_read) return;
    try {
      await notificationApi.markRead(item.notification_id);
      setRecentNotifications(prev =>
        prev.map(n => n.notification_id === item.notification_id ? { ...n, is_read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Mark read error:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationApi.markAllRead();
      setRecentNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Mark all read error:', err);
    }
  };

  const handleNotificationClick = async (item: NotificationItem) => {
    if (!item.is_read) {
      try {
        await notificationApi.markRead(item.notification_id);
        setUnreadCount(prev => Math.max(0, prev - 1));
      } catch (err) {
        // silent
      }
    }
    setIsOpen(false);

    // Extract deep link from metadata or build default
    let targetUrl = `/applications/${item.application_id}`;
    if (item.metadata_json) {
      try {
        const meta = JSON.parse(item.metadata_json);
        if (meta.deep_link) {
          targetUrl = meta.deep_link;
        }
      } catch (e) {
        // fallback
      }
    }
    if (item.application_id) {
      navigate(targetUrl);
    } else {
      navigate('/notifications');
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'URGENT':
        return <span className="bg-rose-100 text-rose-800 text-[9px] font-bold px-1.5 py-0.5 rounded border border-rose-300">{t('notifications.urgent', 'URGENT')}</span>;
      case 'HIGH':
        return <span className="bg-amber-100 text-amber-800 text-[9px] font-bold px-1.5 py-0.5 rounded border border-amber-300">{t('notifications.high', 'HIGH')}</span>;
      default:
        return null;
    }
  };

  return (
    <div className="relative inline-block" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={handleToggleOpen}
        className="relative p-2 text-slate-300 hover:text-white hover:bg-gov-navy rounded-lg transition"
        title={t('notifications.title', 'Notifications')}
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 bg-rose-500 text-white font-extrabold text-[10px] w-4 h-4 rounded-full flex items-center justify-center border-2 border-gov-blue animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-[min(20rem,calc(100vw-1.5rem))] sm:w-96 max-w-[calc(100vw-1.5rem)] bg-white rounded-2xl shadow-xl border border-slate-200 z-50 overflow-hidden text-slate-900 animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="bg-slate-900 text-white p-4 flex justify-between items-center border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-sky-400" />
              <h4 className="font-bold text-sm">{t('notifications.title', 'Notifications')}</h4>
              {unreadCount > 0 && (
                <span className="bg-sky-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
                  {t('notifications.newAlertsCount', '{{count}} New', { count: unreadCount })}
                </span>
              )}
            </div>

            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-[11px] text-sky-300 hover:text-white font-semibold flex items-center gap-1 transition"
              >
                <CheckCheck className="w-3.5 h-3.5" /> {t('notifications.markAllRead', 'Mark all read')}
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
            {isLoading ? (
              <div className="p-6 text-center text-xs text-slate-500">
                <div className="w-5 h-5 border-2 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                {t('notifications.loadingAlerts', 'Loading alerts...')}
              </div>
            ) : recentNotifications.length === 0 ? (
              <div className="p-8 text-center text-slate-500 space-y-1">
                <Bell className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-xs font-bold text-slate-700">{t('notifications.noNotifications', 'No Notifications')}</p>
                <p className="text-[11px] text-slate-400">{t('notifications.allCaughtUp', "You're all caught up with your updates.")}</p>
              </div>
            ) : (
              recentNotifications.map(item => (
                <div
                  key={item.notification_id}
                  onClick={() => handleNotificationClick(item)}
                  className={`p-3.5 hover:bg-slate-50 transition cursor-pointer flex gap-3 items-start relative ${
                    !item.is_read ? 'bg-sky-50/50' : ''
                  }`}
                >
                  {!item.is_read && (
                    <span className="w-2 h-2 rounded-full bg-sky-600 mt-1.5 shrink-0" />
                  )}

                  <div className="flex-1 space-y-1">
                    <div className="flex justify-between items-start gap-2">
                      <h5 className="text-xs font-bold text-slate-900 leading-snug">{item.title}</h5>
                      {getPriorityBadge(item.priority)}
                    </div>
                    <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed">{item.message}</p>
                    <span className="text-[10px] text-slate-400 block font-mono">
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="bg-slate-50 p-2.5 text-center border-t border-slate-200">
            <Link
              to="/notifications"
              onClick={() => setIsOpen(false)}
              className="text-xs font-bold text-sky-700 hover:text-sky-900 flex items-center justify-center gap-1"
            >
              {t('notifications.viewAll', 'View All Notifications')} <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
