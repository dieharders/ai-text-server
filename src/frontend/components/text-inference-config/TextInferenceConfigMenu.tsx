'use client'

import { Dispatch, SetStateAction } from 'react'
import textModels from '../../../../models/models'

const cStyles = 'border-gray-300 dark:border-zinc-700 dark:bg-zinc-800/80 dark:from-inherit'

interface IPropsStart {
  isStarted: boolean
  setIsStarted: Dispatch<SetStateAction<boolean>>
  currentTextModelId: string
  modelPath: string
  ip: string
}
/**
 * Start Inference Engine
 */
const StartEngine = ({
  isStarted,
  setIsStarted,
  currentTextModelId,
  modelPath,
  ip,
}: IPropsStart) => {
  const onStart = async () => {
    console.log('@@ Starting inference...')

    try {
      const modelCard = textModels.find(item => item.id === currentTextModelId)

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

  // @TODO Support shutdown of inference server and remove "disabled"
  return (
    <p className={`mr-4 rounded-lg border ${cStyles} text-md lg:text-lg`}>
      <button
        onClick={onStart}
        disabled={isStarted}
        className="p-2 hover:bg-zinc-700/30 hover:text-yellow-300 lg:p-4"
      >
        <code className={`font-mono font-bold ${isStarted ? 'text-red-600' : 'text-yellow-300'}`}>
          {isStarted ? '[ON]' : '[OFF]'}&nbsp;
        </code>
        <code className="font-mono font-bold">{isStarted ? 'Shutdown' : 'Start'}</code>
      </button>
    </p>
  )
}

interface IPropsDisplay {
  isStarted: boolean
  currentTextModelId: string
}
/**
 * Display what ai model is currently loaded
 */
const CurrentModelDisplay = ({ isStarted, currentTextModelId }: IPropsDisplay) => {
  const textColor = isStarted ? 'text-gray-400' : 'text-inherit'
  const model = textModels.find(model => model.id === currentTextModelId)

  return (
    <div
      className={`text-md lg:text-lg rounded-l-lg rounded-r-none lg:p-4 ${textColor} ${cStyles} whitespace-nowrap border p-2`}
    >
      <div className="inline-flex font-mono">
        Ai model:
        <div className="ml-2 font-bold">{model?.name || 'none'}</div>
      </div>
    </div>
  )
}

interface IPropsFilePath {
  isStarted: boolean
  modelPath: string
  ITEM_MODEL_PATH: string
  setModelPath: Dispatch<SetStateAction<string>>
}
/**
 * Choose file path for ai model
 */
const FilePathChooser = ({
  isStarted,
  modelPath,
  ITEM_MODEL_PATH,
  setModelPath,
}: IPropsFilePath) => {
  const textColor = isStarted ? 'text-gray-400' : 'text-inherit'
  const buttonTextColor = isStarted ? 'text-gray-400' : 'text-white-300'

  const fileSelect = async (isDirMode: boolean): Promise<string | null> => {
    const desktopDir = async (): Promise<string> => {
      // @TODO Get cwd
      // ...
      console.log('@@ desktopDir')
      return ''
    }
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

    const dialogOpen = async (properties: any): Promise<Array<any> | null> => {
      // @TODO Open a native OS file explorer
      // ...
      console.log('@@ opened dialogue box', properties)
      return null
    }
    const selected = await dialogOpen(properties)
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

  const hoverStyle = isStarted
    ? 'hover:cursor-not-allowed'
    : 'hover:text-yellow-300 hover:bg-zinc-500/30'

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
        className={`text-md lg:text-lg border ${buttonTextColor} ${cStyles} ${hoverStyle} rounded-l-none rounded-r-lg p-2 lg:p-4`}
      >
        ...
      </button>
    </>
  )
}

interface IProps {
  ITEM_MODEL_PATH: string
  isStarted: boolean
  setIsStarted: Dispatch<SetStateAction<boolean>>
  currentTextModelId: string
  modelPath: string
  setModelPath: Dispatch<SetStateAction<string>>
  ip: string
}
/**
 * Ai Inference config menu
 */
const TextInferenceConfigMenu = ({
  ITEM_MODEL_PATH,
  isStarted,
  setIsStarted,
  currentTextModelId,
  modelPath,
  setModelPath,
  ip,
}: IProps) => {
  return (
    <div className="fixed left-0 top-0 flex w-full justify-center p-4 backdrop-blur dark:border-neutral-900 dark:bg-zinc-800/30 dark:from-inherit">
      <StartEngine
        isStarted={isStarted}
        setIsStarted={setIsStarted}
        currentTextModelId={currentTextModelId}
        modelPath={modelPath}
        ip={ip}
      />
      <CurrentModelDisplay isStarted={isStarted} currentTextModelId={currentTextModelId} />
      <FilePathChooser
        isStarted={isStarted}
        modelPath={modelPath}
        setModelPath={setModelPath}
        ITEM_MODEL_PATH={ITEM_MODEL_PATH}
      />
    </div>
  )
}

export default TextInferenceConfigMenu
