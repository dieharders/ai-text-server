import type { AppProps } from 'next/app'
import { Inter } from 'next/font/google'
import '@/components/globals.css'

const inter = Inter({ subsets: ['latin'] })

/**
 * Used to setup layouts for each page.
 * You can also inject any relevant code per page.
 */
export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <main className={inter.className}>
      <Component {...pageProps} />
    </main>
  )
}
