/**
 * Resolves avatar URL by ensuring relative paths point to the backend server origin.
 */
export function resolveAvatarUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  const serverOrigin = import.meta.env.VITE_API_URL?.replace('/api/v1', '') || 'http://localhost:8000';
  return `${serverOrigin}${url}`;
}
