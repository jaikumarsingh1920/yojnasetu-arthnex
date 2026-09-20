import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const ROUTE_TITLES: Record<string, string> = {
  '/': 'YojnaSetu — National Welfare & Citizen Support',
  '/home': 'YojnaSetu — National Welfare & Citizen Support',
  '/about': 'About YojnaSetu — National Welfare & Citizen Support',
  '/blogs': 'Blog — YojnaSetu',
  '/blog': 'Blog — YojnaSetu',
  '/recommendations': 'Smart Matching — YojnaSetu',
  '/schemes': 'Explore Welfare Schemes — YojnaSetu',
  '/explore': 'Explore Welfare Schemes — YojnaSetu',
  '/explore-schemes': 'Explore Welfare Schemes — YojnaSetu',
  '/compare': 'Compare Schemes — YojnaSetu',
  '/calculator': 'Financial Calculator — YojnaSetu',
  '/financial-health': 'Financial Health — YojnaSetu',
  '/channel-partners': 'Channel Partners & Helpdesks — YojnaSetu',
  '/nearby-partners': 'Nearby Partners — YojnaSetu',
  '/resources': 'Resources & Guidelines — YojnaSetu',
  '/faq': 'Frequently Asked Questions — YojnaSetu',
  '/login': 'Login — YojnaSetu',
  '/auth/login': 'Login — YojnaSetu',
  '/signup': 'Signup — YojnaSetu',
  '/register': 'Signup — YojnaSetu',
  '/auth/register': 'Signup — YojnaSetu',
  '/auth/signup': 'Signup — YojnaSetu',
  '/forgot-password': 'Forgot Password — YojnaSetu',
  '/auth/forgot-password': 'Forgot Password — YojnaSetu',
  '/reset-password': 'Reset Password — YojnaSetu',
  '/auth/reset-password': 'Reset Password — YojnaSetu',
  '/profile': 'Citizen Profile — YojnaSetu',
  '/dashboard': 'Beneficiary Dashboard — YojnaSetu',
  '/applications': 'Application Guidance & Checklists — YojnaSetu',
  '/saved-schemes': 'Saved Schemes — YojnaSetu',
  '/notifications': 'Citizen Notifications — YojnaSetu',
  '/partner': 'Partner Review Queue — YojnaSetu',
  '/admin': 'System Admin Dashboard — YojnaSetu',
  '/demo-admin': 'Demo Admin — YojnaSetu',
  '/admin-demo': 'Demo Admin — YojnaSetu',
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
    } else if (pathname.startsWith('/blogs/') || pathname.startsWith('/blog/')) {
      document.title = 'Blog Article — YojnaSetu';
    } else if (pathname.startsWith('/channel-partners/') && pathname.includes('/financial-health')) {
      document.title = 'Channel Partner Financial Health — YojnaSetu';
    } else if (pathname.startsWith('/channel-partners/')) {
      document.title = 'Channel Partner Details — YojnaSetu';
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
