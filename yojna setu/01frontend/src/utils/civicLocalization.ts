/**
 * Civic Localization Helper Utility
 * 
 * Provides robust client-side localization for:
 * 1. Channel partner smart routing explanations & summary banners
 * 2. Channel partner badges & verified financial statuses
 * 3. Seeded financial blogs (titles, summaries, dates)
 * 4. Government ministries and canonical scheme titles
 */

export const LOCALE_MAP: Record<string, string> = {
  hi: 'hi-IN',
  bn: 'bn-IN',
  mr: 'mr-IN',
  ta: 'ta-IN',
  te: 'te-IN',
  gu: 'gu-IN',
  kn: 'kn-IN',
  ml: 'ml-IN',
  pa: 'pa-IN',
  or: 'or-IN',
  as: 'as-IN',
  en: 'en-IN',
};

/**
 * Formats date string into the user's localized Indian script format
 */
export function formatLocalizedDate(
  dateStr: string | null | undefined,
  lang: string,
  options: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short', year: 'numeric' }
): string {
  if (!dateStr) return '';
  try {
    const locale = LOCALE_MAP[lang] || 'en-IN';
    return new Date(dateStr).toLocaleDateString(locale, options);
  } catch {
    return String(dateStr);
  }
}

/**
 * Localizes the smart routing audit summary banner from geo_partner_service.py
 */
export function localizeRoutingSummary(
  summary: string | null | undefined,
  t: (key: string, options?: any) => string,
  lang: string
): string {
  if (!summary) return '';
  if (lang === 'en') return summary;

  // Regex matches: "Evaluated 158 candidate channel partners within 2500.0 km. Recommended 50 active eligible partners after applying statutory prudential restrictions and scheme compatibility rules. Excluded 0 partner(s) due to verified statutory restrictions."
  const match = summary.match(
    /Evaluated\s+(\d+)\s+candidate\s+channel\s+partners\s+within\s+([\d.]+)\s*km\.\s*Recommended\s+(\d+)\s+active\s+eligible\s+partners\s+after\s+applying\s+statutory\s+prudential\s+restrictions\s+and\s+scheme\s+compatibility\s+rules\.\s*Excluded\s+(\d+)\s+partner\(s\)\s+due\s+to\s+verified\s+statutory\s+restrictions\./i
  );

  if (match) {
    const [, total, radius, recommended, excluded] = match;
    return t('partnerLocator.routingSummaryAudited', {
      total,
      radius,
      recommended,
      excluded,
      defaultValue: summary,
    });
  }

  return summary;
}

/**
 * Localizes individual partner suitability reasons & routing rationale bullets
 */
export function localizeRoutingReason(
  reason: string | null | undefined,
  t: (key: string, options?: any) => string,
  lang: string
): string {
  if (!reason) return '';
  if (lang === 'en') return reason;

  // Pattern 1: Official channel partner in government directory [Name]
  const dirMatch = reason.match(/Official\s+channel\s+partner\s+in\s+government\s+directory\s+[\[\(]([^\]\)]+)[\]\)]/i);
  if (dirMatch) {
    return t('partnerLocator.reasonOfficialDirectory', {
      name: dirMatch[1],
      defaultValue: lang === 'hi'
        ? `सरकारी निर्देशिका [${dirMatch[1]}] में आधिकारिक चैनल भागीदार`
        : `সরকারি ডিরেক্টরি [${dirMatch[1]}]-তে অফিশিয়াল চ্যানেল পার্টনার`,
    });
  }

  // Pattern 2: Officially authorized channel partner for selected scheme (Name)
  const authMatch = reason.match(/Officially\s+authorized\s+channel\s+partner\s+for\s+selected\s+scheme\s+[\[\(]([^\]\)]+)[\]\)]/i);
  if (authMatch) {
    return t('partnerLocator.reasonAuthorizedScheme', {
      name: authMatch[1],
      defaultValue: lang === 'hi'
        ? `चयनित योजना (${authMatch[1]}) के लिए आधिकारिक रूप से अधिकृत चैनल भागीदार`
        : `নির্বাচিত প্রকল্পের (${authMatch[1]}) জন্য সরকারিভাবে অনুমোদিত অংশীদার`,
    });
  }

  // Pattern 3: Located {dist} km away with verified branch coordinates ({branch}) or just coordinates
  const locMatch = reason.match(/Located\s+([\d.]+)\s*km\s+away\s+with\s+verified\s+branch\s+coordinates(?:\s+[\[\(]([^\]\)]+)[\]\)])?/i);
  if (locMatch) {
    const dist = locMatch[1];
    const branch = locMatch[2] || '';
    return t('partnerLocator.reasonLocatedBranch', {
      distance: dist,
      branch: branch ? ` (${branch})` : '',
      defaultValue: lang === 'hi'
        ? `सत्यापित शाखा निर्देशांक के साथ ${dist} किमी दूर स्थित${branch ? ` (${branch})` : ''}`
        : `যাচাইকৃত শাখা স্থানাঙ্ক সহ ${dist} কিমি দূরত্বে অবস্থিত${branch ? ` (${branch})` : ''}`,
    });
  }

  // Pattern 4: Officially authorized Scheduled Commercial Bank. Official parent institution regulatory indicators available from RBI (Net NPA {val}% as of {date}). NSFDC RRB Net NPA criterion (< 15%) is not applicable to Scheduled Commercial Banks.
  const rbiMatch = reason.match(/Net\s+NPA\s+([\d.]+)%\s+as\s+of\s+([0-9-]+)/i);
  if (rbiMatch && reason.includes('Scheduled Commercial Bank')) {
    const val = rbiMatch[1];
    const date = rbiMatch[2];
    return t('partnerLocator.reasonScbNpa', {
      npa: val,
      date,
      defaultValue: lang === 'hi'
        ? `आधिकारिक रूप से अधिकृत अनुसूचित वाणिज्यिक बैंक। आरबीआई से मूल संस्थान के आधिकारिक विनियामक संकेतक उपलब्ध हैं (${date} तक शुद्ध एनपीए ${val}%)। एनएसएफडीसी आरआरबी शुद्ध एनपीए मानदंड (< 15%) अनुसूचित वाणिज्यिक बैंकों पर लागू नहीं है।`
        : `সরকারিভাবে অনুমোদিত তফসিলি বাণিজ্যিক ব্যাঙ্ক। আরবিআই থেকে প্রাতিষ্ঠানিক নিয়ন্ত্রক সূচক উপলব্ধ (${date} অনুযায়ী নেট এনপিএ ${val}%)। এনএসএফডিসি আরআরবি নেট এনপিএ মাপকাঠি (< ১৫%) তফসিলি বাণিজ্যিক ব্যাংকে প্রযোজ্য নয়।`,
    });
  }

  // Pattern 5: Current partner-level financial health data is managed internally in Ministry MIS.
  if (reason.includes('financial health data is managed internally in Ministry MIS')) {
    return t('partnerLocator.reasonMisData', {
      defaultValue: lang === 'hi'
        ? 'वर्तमान भागीदार-स्तरीय वित्तीय स्थिति डेटा मंत्रालय के एमआईएस में आंतरिक रूप से प्रबंधित किया जाता है।'
        : 'বর্তমান অংশীদার-স্তরের আর্থিক তথ্য মন্ত্রণালয়ের এমআইএস-এ অভ্যন্তরীণভাবে পরিচালিত হয়।',
    });
  }

  // Pattern 6: Partner-level utilization accounts and overdue ledgers are maintained internally in Ministry MIS and are not on open public portals.
  if (reason.includes('utilization accounts and overdue ledgers are maintained internally in Ministry MIS')) {
    return t('partnerLocator.reasonMisLedgers', {
      defaultValue: lang === 'hi'
        ? 'भागीदार-स्तरीय उपयोग खाते और अतिदेय लेजर मंत्रालय के एमआईएस में रखे जाते हैं और खुले सार्वजनिक पोर्टलों पर नहीं हैं।'
        : 'অংশীদার-স্তরের ব্যবহার খতিয়ান ও বকেয়া লেজার মন্ত্রণালয়ের এমআইএস-এ রক্ষিত এবং উন্মুক্ত পোর্টালে নেই।',
    });
  }

  // Pattern 7: Officially authorized and active channel partner / Officially authorized channel partner
  if (reason.match(/^Officially\s+authorized(?:\s+and\s+active)?\s+channel\s+partner\.?$/i)) {
    return t('partnerLocator.reasonActivePartner', {
      defaultValue: lang === 'hi'
        ? 'आधिकारिक रूप से अधिकृत और सक्रिय चैनल भागीदार।'
        : 'সরকারিভাবে অনুমোদিত ও সক্রিয় চ্যানেল অংশীদার।',
    });
  }

  // Pattern 8: Excluded from routing: {ex}
  const exMatch = reason.match(/^Excluded\s+from\s+routing:\s*(.+)$/i);
  if (exMatch) {
    return t('partnerLocator.reasonExcludedRouting', {
      reason: exMatch[1],
      defaultValue: lang === 'hi'
        ? `रूटिंग से बाहर रखा गया: ${exMatch[1]}`
        : `রুটিন থেকে বাদ দেওয়া হয়েছে: ${exMatch[1]}`,
    });
  }

  return reason;
}

/**
 * Known Seeded Blogs Localization Table
 */
const BLOG_LOCALIZATION: Record<string, Record<string, { title: string; summary: string }>> = {
  'A Practical Guide to Finding the Right Government Scheme for Your Enterprise': {
    hi: {
      title: 'अपने उद्यम के लिए सही सरकारी योजना खोजने की व्यावहारिक मार्गदर्शिका',
      summary: 'पात्रता, वित्तीय साक्षरता, दस्तावेज़ तत्परता और संस्थागत भागीदार समन्वय का संश्लेषण करने वाला एक समग्र रोडमैप।',
    },
    bn: {
      title: 'আপনার উদ্যোগের জন্য সঠিক সরকারি প্রকল্প খোঁজার ব্যবহারিক নির্দেশিকা',
      summary: 'যোগ্যতা, আর্থিক সাক্ষরতা, নথিপত্রের প্রস্তুতি এবং প্রাতিষ্ঠানিক অংশীদারদের সমন্বয়কারী একটি সমন্বিত রূপরেখা।',
    },
  },
  'Credit Guarantee Schemes (CGTMSE): How Collateral-Free Lending Works': {
    hi: {
      title: 'क्रेडिट गारंटी योजनाएं (CGTMSE): संपार्श्विक-मुक्त (बिना गारंटी) ऋण कैसे काम करता है',
      summary: 'समझें कि सूक्ष्म और लघु उद्यमों के लिए क्रेडिट गारंटी फंड ट्रस्ट (CGTMSE) उधारकर्ताओं और ऋणदाताओं की सुरक्षा कैसे करता है।',
    },
    bn: {
      title: 'ক্রেডিট গ্যারান্টি স্কিম (CGTMSE): জামানতবিহীন ঋণ কীভাবে কাজ করে',
      summary: 'ক্ষুদ্র ও ছোট উদ্যোগের জন্য ক্রেডিট গ্যারান্টি ফান্ড ট্রাস্ট (CGTMSE) কীভাবে ঋণগ্রহীতা ও ঋণদাতাদের সুরক্ষা দেয় তা জানুন।',
    },
  },
  'What New Entrepreneurs Must Check in Project Reports Before Bank Submission': {
    hi: {
      title: 'बैंक में जमा करने से पहले नए उद्यमियों को प्रोजेक्ट रिपोर्ट में क्या जांचना चाहिए',
      summary: 'ऋण अस्वीकृति को रोकने के लिए विस्तृत परियोजना रिपोर्ट (डीपीआर), ऋण सेवा कवरेज अनुपात और कार्यशील पूंजी गणना के लिए आवश्यक चेकलिस्ट।',
    },
    bn: {
      title: 'ব্যাঙ্কে জমা দেওয়ার আগে নতুন উদ্যোক্তাদের প্রকল্প প্রতিবেদনে কী পরীক্ষা করা উচিত',
      summary: 'ঋণ প্রত্যাখ্যান প্রতিরোধে বিস্তারিত প্রকল্প প্রতিবেদন (ডিপিআর), ঋণ পরিষেবা কভারেজ অনুপাত এবং কার্যকরী মূলধন গণনার জন্য প্রয়োজনীয় নির্দেশিকা।',
    },
  },
};

/**
 * Returns localized title and summary for a blog post
 */
export function getLocalizedBlog(
  blog: { title: string; summary?: string; content?: string },
  lang: string
): { title: string; summary: string } {
  if (!blog || !blog.title) return { title: '', summary: '' };
  if (lang === 'en') return { title: blog.title, summary: blog.summary || '' };

  const directMatch = BLOG_LOCALIZATION[blog.title]?.[lang];
  if (directMatch) {
    return directMatch;
  }

  // Partial / fuzzy match on title
  for (const [key, trans] of Object.entries(BLOG_LOCALIZATION)) {
    if (blog.title.toLowerCase().includes(key.toLowerCase().substring(0, 30)) && trans[lang]) {
      return trans[lang];
    }
  }

  return { title: blog.title, summary: blog.summary || '' };
}

/**
 * Known Government Ministries & Departments Localization Table
 */
const MINISTRY_MAP: Record<string, Record<string, string>> = {
  'Industries and Commerce Department': {
    hi: 'उद्योग एवं वाणिज्य विभाग',
    bn: 'শিল্প ও বাণিজ্য বিভাগ',
  },
  'District Industries Centre Organization': {
    hi: 'जिला उद्योग केंद्र संगठन',
    bn: 'জেলা শিল্প কেন্দ্র সংস্থা',
  },
  'Tribal Development Department': {
    hi: 'जनजातीय विकास विभाग',
    bn: 'জনজাতি উন্নয়ন বিভাগ',
  },
  'Ministry of Micro, Small and Medium Enterprises': {
    hi: 'सूक्ष्म, लघु एवं मध्यम उद्यम मंत्रालय',
    bn: 'অতিক্ষুদ্র, ক্ষুদ্র ও মাঝারি শিল্প মন্ত্রক',
  },
  'Ministry of Agriculture and Farmers Welfare': {
    hi: 'कृषि एवं किसान कल्याण मंत्रालय',
    bn: 'কৃষি ও কৃষক কল্যাণ মন্ত্রক',
  },
  'Ministry of Social Justice and Empowerment': {
    hi: 'सामाजिक न्याय और अधिकारिता मंत्रालय',
    bn: 'সামাজিক ন্যায় ও ক্ষমতায়ন মন্ত্রক',
  },
  'Ministry of Finance': {
    hi: 'वित्त मंत्रालय',
    bn: 'অর্থ মন্ত্রক',
  },
  'Ministry of Rural Development': {
    hi: 'ग्रामीण विकास मंत्रालय',
    bn: 'গ্রামীণ উন্নয়ন মন্ত্রক',
  },
  'Ministry of Education': {
    hi: 'शिक्षा मंत्रालय',
    bn: 'শিক্ষা মন্ত্রক',
  },
  'Ministry of Housing and Urban Affairs': {
    hi: 'आवासन और शहरी कार्य मंत्रालय',
    bn: 'আবাসন ও নগর বিষয়ক মন্ত্রক',
  },
};

/**
 * Localizes government ministry or implementing agency
 */
export function localizeGovMinistry(
  ministry: string | null | undefined,
  lang: string
): string {
  if (!ministry) return '';
  if (lang === 'en') return ministry;

  const trimmed = ministry.trim();
  const direct = MINISTRY_MAP[trimmed]?.[lang];
  if (direct) return direct;

  for (const [key, trans] of Object.entries(MINISTRY_MAP)) {
    if (trimmed.toLowerCase().includes(key.toLowerCase()) && trans[lang]) {
      return trans[lang];
    }
  }

  return ministry;
}

/**
 * Canonical Scheme Titles Localization Table
 */
const SCHEME_TITLE_MAP: Record<string, Record<string, { title: string; desc?: string }>> = {
  'Capital Investment Subsidy: Information Technology (IT) / Information Technology Enabled Services (ITES) Industries': {
    hi: {
      title: 'पूंजी निवेश सब्सिडी: सूचना प्रौद्योगिकी (आईटी) / सूचना प्रौद्योगिकी सक्षम सेवाएं (आईटीईएस) उद्योग',
      desc: 'आईटी और आईटीईएस उद्योगों की स्थापना और विस्तार के लिए प्रोत्साहन और वित्तीय सहायता प्रदान करने वाला घटक।',
    },
    bn: {
      title: 'মূলধন বিনিয়োগ ভর্তুকি: তথ্য প্রযুক্তি (আইটি) / তথ্য প্রযুক্তি সক্ষম সেবা (আইটিইএস) শিল্প',
      desc: 'আইটি এবং আইটিইএস শিল্পের প্রতিষ্ঠা ও সম্প্রসারণের জন্য প্রণোদনা ও আর্থিক সহায়তা প্রদানকারী উপাদান।',
    },
  },
  'Capital Investment Subsidy: SC/ST/Women Entrepreneurs': {
    hi: {
      title: 'पूंजी निवेश सब्सिडी: अनुसूचित जाति/अनुसूचित जनजाति/महिला उद्यमी',
      desc: 'उद्यम स्थापित करने के लिए एससी, एसटी और महिला उद्यमियों के लिए विशेष पूंजी निवेश प्रोत्साहन योजना।',
    },
    bn: {
      title: 'মূলধন বিনিয়োগ ভর্তুকি: এসসি/এসটি/মহিলা উদ্যোক্তা',
      desc: 'উদ্যোগ স্থাপনের জন্য এসসি, এসটি এবং মহিলা উদ্যোক্তাদের জন্য বিশেষ মূলধন বিনিয়োগ প্রণোদনা প্রকল্প।',
    },
  },
  'Grant of Margin Money for Availing the Capital Loan': {
    hi: {
      title: 'पूंजीगत ऋण प्राप्त करने के लिए मार्जिन मनी का अनुदान',
      desc: 'रेशम उद्योग और संबंधित इकाइयों के विकास के लिए पूंजीगत ऋण पर मार्जिन मनी सहायता।',
    },
    bn: {
      title: 'মূলধন ঋণ গ্রহণের জন্য মার্জিন মানির অনুদান',
      desc: 'রেশম শিল্প এবং সংশ্লিষ্ট ইউনিটের উন্নয়নের জন্য মূলধন ঋণের উপর মার্জিন মানি সহায়তা।',
    },
  },
  'Interest Subsidy (For Micro, Small, Medium and Large New Industries)': {
    hi: {
      title: 'ब्याज सब्सिडी (सूक्ष्म, लघु, मध्यम और बड़े नए उद्योगों के लिए)',
      desc: 'नए उद्योगों की स्थापना और प्रोत्साहन के लिए सावधि ऋणों पर ब्याज रियायत और वित्तीय सहायता।',
    },
    bn: {
      title: 'সুদ ভর্তুকি (অতিক্ষুদ্র, ক্ষুদ্র, মাঝারি এবং বৃহৎ নতুন শিল্পের জন্য)',
      desc: 'নতুন শিল্পের প্রতিষ্ঠা ও প্রসারের জন্য মেয়াদি ঋণের সুদের হারে আর্থিক রেয়াত।',
    },
  },
  'Interest Subsidy under Motivation of Entrepreneurs to Start Industries and Fiscal Assistance to Industries': {
    hi: {
      title: 'उद्योग शुरू करने के लिए उद्यमियों को प्रोत्साहन एवं वित्तीय सहायता के तहत ब्याज सब्सिडी',
      desc: 'औद्योगिक निवेश और रोजगार सृजन को बढ़ावा देने के लिए राज्य समर्थित वित्तीय प्रोत्साहन।',
    },
    bn: {
      title: 'শিল্প স্থাপনে উদ্যোক্তাদের উৎসাহ ও আর্থিক সহায়তার আওতায় সুদ ভর্তুকি',
      desc: 'শিল্প বিনিয়োগ এবং কর্মসংস্থান সৃষ্টিতে উৎসাহ দিতে রাষ্ট্রীয় আর্থিক প্রণোদনা।',
    },
  },
  '6% Interest Subsidy on Loans taken through Banks for Study Abroad': {
    hi: {
      title: 'विदेश में अध्ययन के लिए बैंकों के माध्यम से लिए गए ऋण पर 6% ब्याज सब्सिडी',
      desc: 'विदेश में उच्च शिक्षा प्राप्त करने वाले पात्र छात्रों के लिए बैंक शिक्षा ऋण पर 6% ब्याज सब्सिडी।',
    },
    bn: {
      title: 'বিদেশে উচ্চশিক্ষার জন্য ব্যাঙ্ক থেকে নেওয়া ঋণে ৬% সুদ ভর্তুকি',
      desc: 'বিদেশে উচ্চশিক্ষার জন্য যোগ্য শিক্ষার্থীদের ব্যাঙ্ক শিক্ষা ঋণের সুদের হারে ৬% বিশেষ ভর্তুকি।',
    },
  },
};

/**
 * Localizes scheme name if matched with canonical scheme database
 */
export function localizeGovSchemeTitle(
  schemeName: string | null | undefined,
  lang: string
): string {
  if (!schemeName) return '';
  if (lang === 'en') return schemeName;

  const trimmed = schemeName.trim();
  const direct = SCHEME_TITLE_MAP[trimmed]?.[lang];
  if (direct) return direct.title;

  for (const [key, trans] of Object.entries(SCHEME_TITLE_MAP)) {
    if (trimmed.toLowerCase().includes(key.toLowerCase().substring(0, 35)) && trans[lang]) {
      return trans[lang].title;
    }
  }

  return schemeName;
}

/**
 * Localizes scheme description if matched
 */
export function localizeGovDescription(
  desc: string | null | undefined,
  schemeName: string | null | undefined,
  lang: string
): string {
  if (!desc) return '';
  if (lang === 'en') return desc;

  if (schemeName) {
    const trimmed = schemeName.trim();
    for (const [key, trans] of Object.entries(SCHEME_TITLE_MAP)) {
      if (trimmed.toLowerCase().includes(key.toLowerCase().substring(0, 35)) && trans[lang]?.desc) {
        return trans[lang].desc!;
      }
    }
  }

  return desc;
}
