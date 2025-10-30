export const getCsrfToken = () => {
  if (typeof document === 'undefined') {
    return '';
  }
  const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : '';
};
