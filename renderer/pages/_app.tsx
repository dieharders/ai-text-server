import '@/components/globals.css'
import type { AppProps } from 'next/app'
import Layout from '@/components/Layout'

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <Layout>
      <Component {...pageProps} />
    </Layout>
  )
}
