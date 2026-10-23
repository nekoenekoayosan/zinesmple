// GitHub Pagesの /zinesmple/ 配下でも、ローカルでも同じ素材設定を使う。
export function assetUrl(path) {
  if (!path || /^(https?:|data:|blob:)/.test(path)) return path;
  const base = import.meta.env?.BASE_URL || '/';
  if (base !== '/' && path.startsWith(base)) return path;
  return base + path.replace(/^\/+/, '');
}
