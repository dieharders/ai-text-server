'use client'

import { Dispatch, SetStateAction } from 'react'
import textModels from '@/models/models'
import { getTextModelConfig } from '@/utils/localStorage'

// Local Storage keys
export const CURRENT_DOWNLOAD_PATH = 'current-download-path'

const cStyles = 'border-gray-300 dark:border-zinc-700 dark:bg-zinc-800/80 dark:from-inherit'

interface IPropsStart {
  isStarted: boolean
  setIsStarted: Dispatch<SetStateAction<boolean>>
  currentTextModelId: string
  ip: string
}
/**
 * Start Inference Engine
 */
const StartEngine = ({ isStarted, setIsStarted, currentTextModelId, ip }: IPropsStart) => {
  const onStart = async () => {
    console.log('@@ Starting inference...')

    try {
      // Get installed model configs list
      const modelConfig = getTextModelConfig(currentTextModelId)

      if (!modelConfig) throw Error('Cannot find text model config data')

      const options = {
        filePath: modelConfig.savePath,
      }

      const response = await fetch(ip + '/v1/text/start', {
        method: 'POST',
        cache: 'no-cache',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options),
      })

      const result = await response.json()
      setIsStarted(result?.success)
      if (result?.success) console.log('[TextInference] "onStart" Success:', result)
      else console.log('[TextInference] "onStart" Failed:', result)
    } catch (error) {
      console.log('[TextInference] Error: Failed to load the model:', error)
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
  savePath: string
  setSavePath: Dispatch<SetStateAction<string>>
}
/**
 * Choose file path for ai model
 */
const FilePathChooser = ({ isStarted, savePath, setSavePath }: IPropsFilePath) => {
  const textColor = isStarted ? 'text-gray-400' : 'text-inherit'
  const buttonTextColor = isStarted ? 'text-gray-400' : 'text-white-300'

  const fileSelect = async (isDirMode: boolean): Promise<string | null> => {
    const desktopDir = async (): Promise<string> => {
      const path = await window.electron.api('getPath', 'desktop')
      return path
    }

    // Open a native OS file explorer to choose a save path
    const dialogOpen = async () => {
      const mode = isDirMode ? 'openDirectory' : 'openFile'
      const cwd = await desktopDir()
      const properties = {
        title: 'Choose folder to save models',
        defaultPath: cwd,
        properties: [mode],
        buttonLabel: 'Choose',
        filters: [
          {
            extensions: ['txt', 'gif', 'bin'],
            name: '*',
          },
        ],
      }
      return window.electron.api('showOpenDialog', properties)
    }

    const selected = await dialogOpen()
    console.log('@@ User opened dialogue box', selected)

    if (selected.canceled) {
      console.log('@@ User cancelled the selection.')
      return null
    } else if (selected.filePaths.length > 1) {
      console.log('@@ Error: user selected multiple files.')
      return null
    } else {
      console.log('@@ User selected a single folder:', selected.filePaths[0])
      return selected.filePaths[0]
    }
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
        {savePath}
      </span>
      {/* Button */}
      <button
        type="button"
        id="openFileDialog"
        disabled={isStarted}
        onClick={async () => {
          const path = await fileSelect(true)
          path && setSavePath(path)
          path && localStorage.setItem(CURRENT_DOWNLOAD_PATH, path)
        }}
        className={`text-md lg:text-lg border ${buttonTextColor} ${cStyles} ${hoverStyle} rounded-l-none rounded-r-lg p-2 lg:p-4`}
      >
        ...
      </button>
    </>
  )
}

interface IProps {
  isStarted: boolean
  setIsStarted: Dispatch<SetStateAction<boolean>>
  currentTextModelId: string
  savePath: string
  setSavePath: Dispatch<SetStateAction<string>>
  ip: string
}
/**
 * Ai Inference config menu
 */
const TextInferenceConfigMenu = ({
  isStarted,
  setIsStarted,
  currentTextModelId,
  savePath,
  setSavePath,
  ip,
}: IProps) => {
  return (
    <div className="fixed left-0 top-0 flex w-full justify-center p-4 backdrop-blur dark:border-neutral-900 dark:bg-zinc-800/30 dark:from-inherit">
      <StartEngine
        isStarted={isStarted}
        setIsStarted={setIsStarted}
        currentTextModelId={currentTextModelId}
        ip={ip}
      />
      <CurrentModelDisplay isStarted={isStarted} currentTextModelId={currentTextModelId} />
      <FilePathChooser isStarted={isStarted} savePath={savePath} setSavePath={setSavePath} />
    </div>
  )
}

export default TextInferenceConfigMenu
