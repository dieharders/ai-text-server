'use client'

import { useEffect, useState } from 'react'
import ModelCard from '../src/frontend/components/text-model-browser/ModelCard'
import textModels, { IModelCard } from '../models/models'
import AppsBrowser from '../src/frontend/components/AppsBrowser'

export default function Home() {
  // Local Storage keys
  const ITEM_MODEL_PATH = 'model-path' // string
  const ITEM_CURRENT_MODEL = 'current-text-model' // string
  const ITEM_TEXT_MODELS = 'text-models-list' // array<string>
  // App vars
  const ip = 'http://localhost:8008'
  const [isStarted, setIsStarted] = useState(false)
  const [modelPath, setModelPath] = useState<string>(localStorage.getItem(ITEM_MODEL_PATH) || '')
  const [currentTextModel, setCurrentTextModel] = useState<string>(
    localStorage.getItem(ITEM_CURRENT_MODEL) || '',
  )
  // Handlers
  const onSelectTextModel = (val: string) => {
    console.log('@@ Set current text model:', val)
    setCurrentTextModel(val)
    localStorage.setItem(ITEM_CURRENT_MODEL, val)
  }
  const onDownloadComplete = (modelId: string) => {
    const data = localStorage.getItem(ITEM_TEXT_MODELS)
    if (!data) return ''

    const list = JSON.parse(data)
    list.push(modelId)
    localStorage.setItem(ITEM_TEXT_MODELS, list)
  }
  const checkHasDownload = (modelId: string): boolean => {
    const data = localStorage.getItem(ITEM_TEXT_MODELS)
    if (!data) return false

    const list = JSON.parse(data)
    const matched = list.find((item: string) => item === modelId)
    return matched
  }
  const onTestInference = async () => {
    console.log('@@ Testing inference...')

    const options = {
      prompt: 'Whats your name',
    }

    try {
      const response = await fetch(ip + '/v1/completions', {
        method: 'POST',
        mode: 'cors', // must be enabled otherwise wont redirect
        redirect: 'follow', // we want to follow the re-direct automatically
        cache: 'no-cache',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options),
      })
      const result = await response.json()
      console.log('@@ [onLoadModel] Result:', result)
    } catch (error) {
      console.log('@@ [Error] Failed to connect to backend:', error)
    }
  }
  const onStart = async () => {
    console.log('@@ Starting inference...')

    try {
      const modelCard = textModels.find(item => item.id === currentTextModel)

      if (!modelCard) throw Error('Cannot find text model card data')

      const options = {
        filePath: `${modelPath}/${modelCard.fileName}`,
      }

      const response = await fetch(ip + '/api/text/v1/inference/start', {
        method: 'POST',
        cache: 'no-cache',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options),
      })

      const result = await response.json()
      setIsStarted(result?.success)
      console.log('@@ [onStart] Success:', result)
    } catch (error) {
      console.log('@@ [Error] Failed to load the model:', error)
    }
  }
  const fileSelect = async (isDirMode: boolean): Promise<string | null> => {
    // If you cant or wont import @tauri-apps/api/* then you can use window.__TAURI__.*
    const { desktopDir } = await import('@tauri-apps/api/path')
    const cwd = await desktopDir()
    const properties = {
      defaultPath: cwd,
      directory: isDirMode,
      filters: [
        {
          extensions: ['txt', 'gif'],
          name: '*',
        },
      ],
    }

    const { open } = await import('@tauri-apps/api/dialog')
    const selected = await open(properties)
    if (Array.isArray(selected)) {
      console.log('@@ Error: user selected multiple files.')
      return null
    } else if (selected === null) {
      console.log('@@ User cancelled the selection.')
    } else {
      console.log('@@ User selected a single file:', selected)
    }
    return selected
  }
  // Render components
  const cStyles = 'border-gray-300 dark:border-zinc-700 dark:bg-zinc-800/80 dark:from-inherit'

  /**
   * Choose file path for ai model
   */
  const renderFilePathChooser = () => {
    const textColor = isStarted ? 'text-gray-400' : 'text-inherit'
    const buttonTextColor = isStarted ? 'text-gray-400' : 'text-white-300'

    return (
      <>
        {/* Path string */}
        <span
          className={`text-md lg:text-lg overflow-hidden text-ellipsis whitespace-nowrap p-2 lg:p-4 ${textColor} ${cStyles} border`}
        >
          {modelPath}
        </span>
        {/* Button */}
        <button
          type="button"
          id="openFileDialog"
          disabled={isStarted}
          onClick={async () => {
            const path = await fileSelect(true)
            path && setModelPath(path)
            path && localStorage.setItem(ITEM_MODEL_PATH, path)
          }}
          className={`text-md lg:text-lg border ${buttonTextColor} ${cStyles} rounded-l-none rounded-r-lg p-2 lg:p-4`}
        >
          ...
        </button>
      </>
    )
  }
  /**
   * Start Inference Engine
   */
  const renderStartEngine = () => {
    // @TODO Support shutdown of inference server and remove "disabled"
    return (
      <p className={`mr-4 rounded-lg border ${cStyles} text-md lg:text-lg`}>
        <button onClick={onStart} disabled={isStarted} className="p-2 lg:p-4">
          <code
            className={` font-mono font-bold ${isStarted ? 'text-red-600' : 'text-yellow-300'}`}
          >
            {isStarted ? '[ON]' : '[OFF]'}&nbsp;
          </code>
          <code className="font-mono font-bold">{isStarted ? 'Shutdown' : 'Start'}</code>
        </button>
      </p>
    )
  }
  /**
   * Display what ai model is currently loaded
   */
  const renderModelChooser = () => {
    const textColor = isStarted ? 'text-gray-400' : 'text-inherit'

    return (
      <div
        className={`text-md lg:text-lg rounded-l-lg rounded-r-none lg:p-4 ${textColor} ${cStyles} whitespace-nowrap border p-2`}
      >
        <div className="inline-flex font-mono">
          Ai model:
          <div className="ml-2 font-bold">{currentTextModel || 'none'}</div>
        </div>
      </div>
    )
  }
  // Company credits (built by)
  const renderCredits = () => {
    return (
      <div className="fixed bottom-0 left-0 z-30 flex h-48 w-full items-end justify-center bg-gradient-to-t from-white via-white font-mono text-sm dark:from-black dark:via-black lg:static lg:h-auto lg:w-auto lg:bg-none">
        <button
          // onClick={onTestInference}
          className="pointer-events-none flex place-items-center gap-2 p-8 lg:pointer-events-auto lg:p-0"
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
        </button>
      </div>
    )
  }
  // Show the text inference config menu
  const renderConfigMenu = () => {
    return (
      <div className="fixed left-0 top-0 flex w-full justify-center p-4 backdrop-blur dark:border-neutral-900 dark:bg-zinc-800/30 dark:from-inherit">
        {renderStartEngine()}
        {renderModelChooser()}
        {renderFilePathChooser()}
      </div>
    )
  }
  // List of curated text inference models
  const TextModelBrowserMenu = ({ data }: { data: Array<IModelCard> }) => {
    const cards = data?.map(item => {
      return (
        <ModelCard
          key={item.id}
          id={item.id}
          name={item.name}
          description={item.description}
          fileSize={item.fileSize}
          provider={item.provider}
          license={item.license}
          downloadUrl={item.downloadUrl}
          saveToPath={modelPath}
          fileName={item.fileName}
          isLoaded={currentTextModel === item.id}
          initialHasDownload={checkHasDownload(item.id)}
          onSelectModel={onSelectTextModel}
          onDownloadComplete={onDownloadComplete}
        ></ModelCard>
      )
    })

    return (
      <div className="z-5 mt-16 flex h-full w-full flex-col justify-center gap-8 rounded-xl border-b border-gray-300 bg-gray-200 p-6 backdrop-blur-sm dark:border-neutral-800 dark:bg-zinc-800/30 lg:mb-0 lg:mt-52 lg:w-10/12 2xl:w-3/6">
        {cards}
      </div>
    )
  }

  // Intialize default model path if non selected/stored
  useEffect(() => {
    const saveDefault = async () => {
      const { desktopDir } = await import('@tauri-apps/api/path')
      const path = await desktopDir()
      if (path) {
        setModelPath(path)
        localStorage.setItem(ITEM_MODEL_PATH, path)
      }
    }
    if (modelPath === '') saveDefault()
  }, [modelPath])

  return (
    <main className="xs:p-0 flex min-h-screen flex-col items-center justify-between overflow-x-hidden lg:p-24">
      {/* Ai Inference config menu */}
      <div className="text-md z-10 w-full items-center justify-center font-mono lg:flex">
        {renderConfigMenu()}
      </div>

      {/* Background flare */}
      <div className={`-z-100 relative ${!isStarted && 'm-16'}`}>
        <div className="before:absolute before:-z-20 before:h-[300px] before:w-[480px] before:-translate-x-1/2 before:rounded-full before:bg-gradient-radial before:from-white before:to-transparent before:blur-2xl before:content-[''] after:absolute after:-z-20 after:h-[180px] after:w-[240px] after:translate-x-1/4 after:bg-gradient-conic after:from-sky-200 after:via-blue-200 after:blur-2xl after:content-[''] before:dark:bg-gradient-to-br before:dark:from-transparent before:dark:to-blue-700 before:dark:opacity-10 after:dark:from-sky-900 after:dark:via-[#0141ff] after:dark:opacity-40 before:lg:h-[360px]"></div>
      </div>
      {/* Title and Credits */}
      <div className="relative flex-col place-items-center">
        {/* <Image
          className="relative dark:drop-shadow-[0_0_0.3rem_#ffffff70] dark:invert"
          src="/next.svg"
          alt="Next.js Logo"
          width={180}
          height={37}
          priority
        /> */}
        <h1 className="text-center text-4xl">🍺HomebrewAi</h1>
        {renderCredits()}
      </div>

      {/* Footer menus */}
      {isStarted ? <AppsBrowser /> : <TextModelBrowserMenu data={textModels} />}
    </main>
  )
}
