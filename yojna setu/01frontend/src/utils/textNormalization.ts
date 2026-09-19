/**
 * Centralized Government Text Normalization & Display Transformation Utility
 *
 * Cleans scraped, double-encoded, or raw HTML/markdown strings into accessible,
 * clean citizen-facing copy across the YojnaSetu platform.
 *
 * Guarantees:
 * 1. Multi-pass HTML entity decoding (&quot; -> ", &amp; -> &, etc.)
 * 2. Safe stripping and normalization of raw HTML tags (<br>, <p>, etc.)
 * 3. Removal of Markdown artifacts (**bold**, __italic__, hashes)
 * 4. Whitespace, linebreak, and separator normalization
 * 5. Preservation of official government meaning and numbers
 * 6. Never modifies canonical stored source data
 */

const HTML_ENTITY_MAP: Record<string, string> = {
  '&quot;': '"',
  '&apos;': "'",
  '&#39;': "'",
  '&#x27;': "'",
  '&amp;': '&',
  '&lt;': '<',
  '&gt;': '>',
  '&nbsp;': ' ',
  '&#160;': ' ',
  '&copy;': '©',
  '&reg;': '®',
  '&trade;': '™',
  '&mdash;': '—',
  '&ndash;': '–',
  '&hellip;': '...',
  '&#8216;': "'",
  '&#8217;': "'",
  '&#8220;': '"',
  '&#8221;': '"',
  '&#8211;': '–',
  '&#8212;': '—',
  '&#8230;': '...',
};

/**
 * Recursively decodes HTML entities across up to 3 passes
 * (handles double-encoded entities like &amp;quot;, &amp;amp;, etc.)
 */
export function decodeHtmlEntities(str: string): string {
  if (!str) return '';
  let cur = str;
  for (let pass = 0; pass < 3; pass++) {
    let replaced = false;
    for (const [entity, replacement] of Object.entries(HTML_ENTITY_MAP)) {
      if (cur.includes(entity)) {
        cur = cur.replaceAll(entity, replacement);
        replaced = true;
      }
    }
    // Also handle numeric entities &#nnn; or &#xhhh;
    if (cur.includes('&#')) {
      cur = cur.replace(/&#(\d+);/g, (_, dec) => {
        try {
          return String.fromCharCode(parseInt(dec, 10));
        } catch {
          return '';
        }
      });
      cur = cur.replace(/&#x([0-9a-f]+);/gi, (_, hex) => {
        try {
          return String.fromCharCode(parseInt(hex, 16));
        } catch {
          return '';
        }
      });
      replaced = true;
    }
    if (!replaced) break;
  }
  return cur;
}

/**
 * Comprehensive civic text normalization
 */
export function normalizeGovText(text: string | null | undefined): string {
  if (!text) return '';

  let cur = String(text);

  // 1. Convert <br> and paragraph tags to appropriate spacing
  cur = cur.replace(/<br\s*\/?>/gi, ' ');
  cur = cur.replace(/<\/?p\s*>/gi, '\n');
  cur = cur.replace(/<\/?div\s*>/gi, '\n');
  // Strip any remaining actual HTML tags safely (requires tag name to start with letter or !)
  cur = cur.replace(/<(?:\/?[a-zA-Z][a-zA-Z0-9]*|!--)[^>]*>/g, ' ');

  // 2. Decode entities multi-pass (after stripping tags so <= or > are preserved)
  cur = decodeHtmlEntities(cur);

  // 3. Replace unicode replacement artifacts (\ufffd) or stray control chars
  cur = cur.replace(/\ufffd/g, "'");
  cur = cur.replace(/[\u2018\u2019]/g, "'");
  cur = cur.replace(/[\u201c\u201d]/g, '"');
  cur = cur.replace(/[\u2013\u2014]/g, '-');
  cur = cur.replace(/\u00a0/g, ' ');

  // 4. Remove markdown bold/italic/stars/headers
  cur = cur.replace(/\*\*([^*]+)\*\*/g, '$1');
  cur = cur.replace(/__([^_]+)__/g, '$1');
  cur = cur.replaceAll('**', '').replaceAll('__', '');
  cur = cur.replace(/^\s*#+\s*/gm, '');

  // 5. Clean repeated whitespace and blank lines
  cur = cur.replace(/[ \t]+/g, ' ');
  cur = cur.replace(/\n\s*\n+/g, '\n\n');

  return cur.trim();
}

/**
 * Normalizes and formats a scheme or partner title.
 * Strips redundant wrapping quotes if the whole title is enclosed in quotes.
 */
export function cleanGovTitle(title: string | null | undefined): string {
  let cleaned = normalizeGovText(title);
  if (!cleaned) return '';

  // If the entire title is wrapped in matched outer quotes, unwrap
  if (
    (cleaned.startsWith('"') && cleaned.endsWith('"')) ||
    (cleaned.startsWith("'") && cleaned.endsWith("'"))
  ) {
    if (cleaned.length > 2) {
      cleaned = cleaned.slice(1, -1).trim();
    }
  }

  // Strip accidental double quotes at edges: e.g. ""Title""
  cleaned = cleaned.replace(/^"+|"+$/g, '').trim();

  return cleaned;
}

/**
 * Normalizes description with optional clean truncation at word boundary.
 */
export function cleanGovDescription(
  desc: string | null | undefined,
  maxWords?: number
): string {
  const cleaned = normalizeGovText(desc);
  if (!cleaned) return '';

  if (maxWords && maxWords > 0) {
    const words = cleaned.split(/\s+/);
    if (words.length > maxWords) {
      return words.slice(0, maxWords).join(' ') + '...';
    }
  }

  return cleaned;
}

/**
 * Splits a long government description into a concise overview paragraph
 * and the remaining full details text for progressive disclosure.
 */
export function splitOverviewAndDetails(
  text: string | null | undefined,
  targetWords: number = 35
): { overview: string; fullDetails: string; hasMore: boolean } {
  const cleaned = normalizeGovText(text);
  if (!cleaned) {
    return { overview: '', fullDetails: '', hasMore: false };
  }

  const words = cleaned.split(/\s+/);
  if (words.length <= targetWords) {
    return { overview: cleaned, fullDetails: cleaned, hasMore: false };
  }

  // Find a sentence boundary near targetWords
  const sentences = cleaned.split(/(?<=[.!?])\s+/);
  const overviewSentences: string[] = [];
  let count = 0;

  for (const s of sentences) {
    const sWords = s.split(/\s+/).length;
    if (count + sWords <= targetWords + 12 || overviewSentences.length === 0) {
      overviewSentences.push(s);
      count += sWords;
    } else {
      break;
    }
  }

  const overview = overviewSentences.join(' ').trim();
  const hasMore = overview.length < cleaned.length;

  return {
    overview,
    fullDetails: cleaned,
    hasMore,
  };
}
