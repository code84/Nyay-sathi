/* eslint-disable @next/next/no-page-custom-font */
// React 19 moves these <link> tags into <head>. Closest free match to the reference: Playfair Display + Inter.
export default function Fonts() {
  return (
    <>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link rel="stylesheet" precedence="default"
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Merriweather:wght@700&family=Noto+Sans+Devanagari:wght@400;500;600&family=Noto+Serif+Devanagari:wght@600;700&display=swap" />
    </>
  );
}
