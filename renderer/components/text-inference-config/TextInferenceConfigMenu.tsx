'use client'

import { Dispatch, SetStateAction } from 'react'
import { dialogOpen } from '@/components/shared/dialog'
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
  const onStart = async (): Promise<boolean> => {
    // Shutdown
    if (isStarted) {
      try {
        const response = await fetch(`${ip}/v1/services/shutdown`, {
          method: 'GET',
          cache: 'no-cache',
        })

        const result = await response.json()
        if (result?.success) {
          console.log('[TextInference] Shutdown successful:', result)
          setIsStarted(false)
          return true
        } else throw new Error('Shutdown action failed unexpectedly.')
      } catch (error) {
        console.log('[TextInference] Error: Failed to shutdown inference:', error)
        return false
      }
    }

    // Start
    console.log('[TextInference] Starting inference...')

    try {
      // Get installed/stored model configs list and combine
      const storedConfig = getTextModelConfig(currentTextModelId)
      const config = textModels.find(model => model.id === currentTextModelId)
      if (!storedConfig || !config) throw Error('Cannot find text model config data')

      const modelConfig = {
        id: config?.id,
        name: config?.name,
        checksum: storedConfig?.checksum,
        isFavorited: storedConfig?.isFavorited,
        modified: storedConfig?.modified,
        numTimesRun: storedConfig?.numTimesRun,
        savePath: storedConfig?.savePath,
        size: storedConfig?.size,
        description: config?.description,
        licenses: config?.licenses,
        modelType: config?.modelType,
        provider: config?.provider,
        ramSize: config?.ramSize,
        tags: config?.tags,
        promptTemplate: config?.promptTemplate || '{{PROMPT}}',
      }

      const options = { modelConfig }

      const response = await fetch(`${ip}/v1/text/start`, {
        method: 'POST',
        cache: 'no-cache',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options),
      })

      const result = await response.json()
      setIsStarted(result?.success)
      if (result?.success) {
        console.log('[TextInference] "onStart" Success:', result)
        return true
      } else {
        console.log('[TextInference] "onStart" Failed:', result)
        return false
      }
    } catch (error) {
      console.log('[TextInference] Error: Failed to load the model:', error)
      return false
    }
  }

  return (
    <p className={`mr-4 rounded-lg border ${cStyles} text-md lg:text-lg`}>
      <button onClick={onStart} className="p-2 hover:bg-zinc-700/30 hover:text-yellow-300 lg:p-4">
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

  const hoverStyle = isStarted
    ? 'hover:cursor-not-allowed'
    : 'hover:text-yellow-300 hover:bg-zinc-500/30'

  return (
    <>
      {/* Path string */}
      <span className={`text-md lg:text-lg truncate p-2 lg:p-4 ${textColor} ${cStyles} border`}>
        {savePath}
      </span>
      {/* Button */}
      <button
        type="button"
        id="openFolderDialog"
        disabled={isStarted}
        onClick={async () => {
          const options = {
            title: 'Choose one folder to save models',
          }
          const path = await dialogOpen({ isDirMode: true, options })
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
