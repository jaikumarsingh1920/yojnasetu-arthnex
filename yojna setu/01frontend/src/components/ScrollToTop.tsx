import React, { useEffect, useRef } from 'react';
import { useLocation, useNavigationType } from 'react-router-dom';

/**
 * ScrollToTop ensures consistent, reliable scroll behavior across all YojnaSetu routes:
 * 1. On route navigation (PUSH/REPLACE), resets the viewport cleanly to the top (0, 0).
 * 2. If a hash anchor exists (e.g. #calculator or #scheme-results), scrolls smoothly to that element
 *    with proper fixed navbar offset (85px) so the heading is never hidden behind the navbar.
 * 3. Does not break browser back/forward history restoration (POP navigation).
 */
export const ScrollToTop: React.FC = () => {
  const { pathname, hash, search } = useLocation();
  const navType = useNavigationType();
  const prevPathRef = useRef<string>(pathname);

  useEffect(() => {
    const isNewRoute = prevPathRef.current !== pathname;
    prevPathRef.current = pathname;

    // 1. If an in-page hash anchor is specified (e.g., #calculator)
    if (hash) {
      const targetId = hash.replace('#', '');
      const scrollToAnchor = () => {
        const element = document.getElementById(targetId);
        if (element) {
          const navOffset = 85;
          const elementPosition = element.getBoundingClientRect().top;
          const offsetPosition = elementPosition + window.pageYOffset - navOffset;

          window.scrollTo({
            top: Math.max(0, offsetPosition),
            behavior: 'smooth'
          });
        }
      };

      // Try immediately, or after microtask if dynamic content is rendering
      scrollToAnchor();
      const timer = setTimeout(scrollToAnchor, 100);
      return () => clearTimeout(timer);
    }

    // 2. On standard forward navigations (PUSH or REPLACE) to a new route,
    // ensure the page always begins from the top (0, 0).
    if (isNewRoute && navType !== 'POP') {
      window.scrollTo({
        top: 0,
        left: 0,
        behavior: 'instant'
      });
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
    }
  }, [pathname, hash, search, navType]);

  return null;
};
