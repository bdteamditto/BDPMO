import Script from 'next/script';
export default function Home(){return <><link rel="stylesheet" href="/style.css"/><div id="app"><div className="card login">กำลังเปิด BD PMO…</div></div><div id="message" role="status" aria-live="polite"/><dialog id="dialog"/><Script src="/app.js" strategy="afterInteractive"/></>}
