/**
 * Safe currency formatter for YojnaSetu frontend.
 * Safely handles numbers, numeric strings, null, undefined, NaN, and 0.
 * Returns formatted INR string (e.g. ₹2,00,000) or human fallback (e.g. "Not available").
 */
export const formatCurrency = (
  value: number | string | null | undefined,
  fallback: string = 'Not available'
): string => {
  if (value === null || value === undefined || value === '') {
    return fallback;
  }
  const num = typeof value === 'number' ? value : Number(value);
  if (isNaN(num)) {
    return fallback;
  }
  try {
    return `₹${Math.round(num).toLocaleString('en-IN')}`;
  } catch (err) {
    return fallback;
  }
};

/**
 * Safe percentage formatter for interest rates.
 */
export const formatPercent = (
  value: number | string | null | undefined,
  fallback: string = 'Based on category'
): string => {
  if (value === null || value === undefined || value === '') {
    return fallback;
  }
  const num = typeof value === 'number' ? value : Number(value);
  if (isNaN(num)) {
    return fallback;
  }
  return `${num}% p.a.`;
};

/**
 * Safe date formatter.
 */
export const formatDate = (
  value: string | Date | null | undefined,
  fallback: string = 'Not specified'
): string => {
  if (!value) return fallback;
  try {
    const date = typeof value === 'string' ? new Date(value) : value;
    if (isNaN(date.getTime())) return fallback;
    return date.toLocaleString();
  } catch (err) {
    return fallback;
  }
};
