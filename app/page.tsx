'use client'
// @TODO Remove above and put all child components below in their own files so this can be a server component...

import { useState } from 'react'

// import Image from "next/image";
// import Link from "next/link";

export default function Home() {
  const appLink = 'https://brain-dump-dieharders.vercel.app/'
  const ip = 'http://localhost:8008'
  const [isLoaded, setIsLoaded] = useState(false)
  const [isStarted, setIsStarted] = useState(false)

  const onLoadModel = async () => {
    console.log('@@ Loading model...')

    const options = {
      modelId: 'llama7b',
    }

    try {
      const response = await fetch(ip + '/api/text/v1/inference/load', {
        method: 'POST',
        // mode: "no-cors", // no-cors, *cors, same-origin
        cache: 'no-cache',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options),
      })

      const result = await response.json()
      setIsLoaded(result?.success)
      console.log('@@ [onLoadModel] Success:', result)
    } catch (error) {
      console.log('@@ [Error] Failed to load the model:', error)
    }
  }
  const onStart = async () => {
    console.log('@@ Starting inference...')

    try {
      const response = await fetch(ip + '/api/text/v1/inference/start', {
        method: 'GET',
        cache: 'no-cache',
      })

      const result = await response.json()
      setIsStarted(result?.success)
      console.log('@@ [onStart] Success:', result)
    } catch (error) {
      console.log('@@ [Error] Failed to load the model:', error)
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
        {/* Load Model */}
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto  lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
          {isLoaded ? '[llama7b]' : '[empty]'}&nbsp;
          <button onClick={onLoadModel}>
            <code
              className="font-mono font-bold"
              style={{ color: `${isLoaded ? 'lime' : 'yellow'}` }}
            >
              Load Model
            </code>
          </button>
        </p>
        {/* Start Inference */}
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto  lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
          {isStarted ? '[ON]' : '[OFF]'}&nbsp;
          <button onClick={onStart}>
            <code
              className="font-mono font-bold"
              style={{ color: `${isStarted ? 'lime' : 'yellow'}` }}
            >
              Start Engine
            </code>
          </button>
        </p>

        <div className="fixed bottom-0 left-0 flex h-48 w-full items-end justify-center bg-gradient-to-t from-white via-white dark:from-black dark:via-black lg:static lg:h-auto lg:w-auto lg:bg-none">
          <a
            className="pointer-events-none flex place-items-center gap-2 p-8 lg:pointer-events-auto lg:p-0"
            href={appLink}
            target="_blank"
            rel="noopener noreferrer"
          >
            By{' '}
            {/* <Image
              src="/vercel.svg"
              alt="Vercel Logo"
              className="dark:invert"
              width={100}
              height={24}
              priority
            /> */}
            <h2 className="text-md">Spread Shot Studios</h2>
          </a>
        </div>
      </div>

      <div className="relative flex place-items-center before:absolute before:h-[300px] before:w-[480px] before:-translate-x-1/2 before:rounded-full before:bg-gradient-radial before:from-white before:to-transparent before:blur-2xl before:content-[''] after:absolute after:-z-20 after:h-[180px] after:w-[240px] after:translate-x-1/3 after:bg-gradient-conic after:from-sky-200 after:via-blue-200 after:blur-2xl after:content-[''] before:dark:bg-gradient-to-br before:dark:from-transparent before:dark:to-blue-700 before:dark:opacity-10 after:dark:from-sky-900 after:dark:via-[#0141ff] after:dark:opacity-40 before:lg:h-[360px]">
        {/* <Image
          className="relative dark:drop-shadow-[0_0_0.3rem_#ffffff70] dark:invert"
          src="/next.svg"
          alt="Next.js Logo"
          width={180}
          height={37}
          priority
        /> */}
        <h1 className="text-4xl">🍺HomebrewAi</h1>
      </div>

      {/* Browse Apps */}
      <div className="mb-32 grid text-center lg:mb-0 lg:grid-cols-4 lg:text-left">
        <a
          href={appLink}
          className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30"
          target="_blank"
          rel="noopener noreferrer"
        >
          <h2 className="mb-3 text-xl font-semibold">
            Learn{' '}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Find in-depth information and share it. Search and analyze private data with agents.
          </p>
        </a>

        <a
          href={appLink}
          className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800 hover:dark:bg-opacity-30"
          target="_blank"
          rel="noopener noreferrer"
        >
          <h2 className="mb-3 text-xl font-semibold">
            Create{' '}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Find inspiration, kick-off a project or just toss ideas around with a creative
            avatar.
          </p>
        </a>

        <a
          href={appLink}
          className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30"
          target="_blank"
          rel="noopener noreferrer"
        >
          <h2 className="mb-3 text-xl font-semibold">
            Heal{' '}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Explore your mind then reflect on your journey with an ai buddy by your side.
          </p>
        </a>

        <a
          href={appLink}
          className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30"
          target="_blank"
          rel="noopener noreferrer"
        >
          <h2 className="mb-3 text-xl font-semibold">
            Grow{' '}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Plan, adapt, enact. Take advantage of critical thinking processes to reach
            your goals.
          </p>
        </a>
      </div>
    </main>
  )
}
