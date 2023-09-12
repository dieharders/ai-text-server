import Home from './home'
import Head from 'next/head'

const Layout = () => {
  return (
    <>
      <Head>
        <title>HomebrewAi</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Home />
    </>
  )
}

export default Layout
