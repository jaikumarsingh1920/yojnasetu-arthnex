import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const ROUTE_TITLES: Record<string, string> = {
  '/': 'YojnaSetu — National Welfare & Credit Guidance Portal',
  '/recommendations': 'Smart Scheme Matching — YojnaSetu',
  '/schemes': 'Explore Welfare Schemes — YojnaSetu',
  '/compare': 'Compare Schemes — YojnaSetu',
  '/calculator': 'Financial & Subsidy Calculator — YojnaSetu',
  '/channel-partners': 'Channel Partner Centers & Helpdesks — YojnaSetu',
  '/login': 'Citizen Login — YojnaSetu',
  '/auth/login': 'Citizen Login — YojnaSetu',
  '/register': 'Citizen Registration — YojnaSetu',
  '/auth/register': 'Citizen Registration — YojnaSetu',
  '/profile': 'Citizen Profile — YojnaSetu',
  '/dashboard': 'Beneficiary Dashboard — YojnaSetu',
  '/applications': 'Application Guidance & Checklists — YojnaSetu',
  '/saved-schemes': 'Saved Schemes — YojnaSetu',
  '/notifications': 'Citizen Notifications — YojnaSetu',
  '/partner': 'Partner Review Queue — YojnaSetu',
  '/admin': 'System Admin Dashboard — YojnaSetu',
  '/unauthorized': 'Access Restricted — YojnaSetu',
};

/**
 * Updates document.title dynamically on every route change,
 * ensuring meaningful, route-appropriate browser tab titles across all pages.
 */
export const PageTitleManager: React.FC = () => {
  const { pathname } = useLocation();

  useEffect(() => {
    if (ROUTE_TITLES[pathname]) {
      document.title = ROUTE_TITLES[pathname];
    } else if (pathname.startsWith('/schemes/')) {
      document.title = 'Scheme Details — YojnaSetu';
    } else if (pathname.startsWith('/applications/')) {
      document.title = 'Application Guidance Details — YojnaSetu';
    } else if (pathname.startsWith('/partner/applications/')) {
      document.title = 'Partner Application Review — YojnaSetu';
    } else {
      document.title = '404 Page Not Found — YojnaSetu';
    }
  }, [pathname]);

  return null;
};
