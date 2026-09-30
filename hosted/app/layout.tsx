import type {Metadata} from 'next';
export const metadata:Metadata={title:'BD PMO · Project Control',description:'บริหารโครงการตั้งแต่เริ่มงาน ส่งมอบ ถึงปิดโครงการ',icons:{icon:'/favicon.svg'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="th"><body>{children}</body></html>}
