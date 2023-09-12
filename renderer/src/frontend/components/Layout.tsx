import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'HomebrewAi',
  description: 'Ai inference engine.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <main className={inter.className}>{children}</main>
}
