import '@/components/globals.css'
import type { AppProps } from 'next/app'
import Layout from '@/components/Layout'

/**
 * Used to setup layouts for each page.
 * You can also inject any relevant code per page.
 */
export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <Layout>
      <Component {...pageProps} />
    </Layout>
  )
}
