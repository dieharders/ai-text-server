import { useState } from 'react'
import { EProgressState } from './useDownloader'
import { EValidationState, IModelConfig } from './configs'
import { dialogOpen } from '@/components/shared/dialog'
import { IModelCard } from '@/models/models'

// Styling
const sizingStyles = 'lg:static sm:border lg:bg-gray-200 lg:dark:bg-zinc-800/30'
const colorStyles =
  'border-b border-gray-300 bg-gradient-to-b from-zinc-200 dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit'

/**
 * Pause the download
 */
const PauseButton = ({ action }: { action: () => Promise<EProgressState> }) => {
  const [isDisabled, setIsDisabled] = useState(false)
  const textColor = isDisabled ? 'text-gray-400' : 'text-white'

  return (
    <button
      className={`h-12 w-min rounded-lg px-4 ${colorStyles} ${sizingStyles} ${textColor} text-sm hover:bg-blue-500 hover:text-blue-100`}
      disabled={isDisabled}
      onClick={async () => {
        setIsDisabled(true)
        await action()
        setIsDisabled(false)
        return
      }}
    >
      <p className="font-bold">Pause</p>
    </button>
  )
}

/**
 * Check the user's hardware specs to see if they can run the specified model.
 */
const CheckHardware = () => {
  return (
    <button
      className={`h-12 w-min rounded-lg px-4 ${colorStyles} ${sizingStyles} text-sm text-blue-400 hover:bg-blue-500 hover:text-white`}
      onClick={() => {
        return true
      }}
    >
      <p className="font-bold">Check</p>
    </button>
  )
}

/**
 * Import an already downloaded model file
 */
interface IImportModelProps {
  onComplete: () => void
  action: (filePath: string) => void
}
const ImportModel = ({ onComplete, action }: IImportModelProps) => {
  return (
    <button
      type="button"
      id="openFileDialog"
      className={`h-12 w-min rounded-lg px-4 ${colorStyles} ${sizingStyles} text-sm text-blue-400 hover:bg-blue-500 hover:text-white`}
      onClick={async () => {
        const options = {
          title: 'Choose a model file to import',
          filterExtensions: ['gguf'],
        }
        const filePath = await dialogOpen({ isDirMode: false, options })
        if (!filePath) return

        action(filePath)
        // Done
        onComplete()
      }}
    >
      <p className="font-bold">Import</p>
    </button>
  )
}

/**
 * This button selects this model for inference
 */
interface ILoadProps {
  action: () => void
  isLoaded: boolean
}
const LoadButton = ({ action, isLoaded }: ILoadProps) => {
  const textColor = !isLoaded ? 'text-yellow-300' : 'text-gray-400'
  const hoverStyle = !isLoaded
    ? 'hover:bg-zinc-700/30 hover:text-white'
    : 'hover:cursor-not-allowed'
  return (
    <button
      className={`h-12 w-full ${sizingStyles} rounded-lg border border-gray-300 text-center dark:border-neutral-800 dark:bg-zinc-800/30 ${hoverStyle} ${textColor}`}
      disabled={isLoaded}
      onClick={action}
    >
      <code className="text-md font-mono font-bold">Load</code>
    </button>
  )
}

/**
 * Download this ai model from a repository
 */
interface IStartDownloadProps {
  action: () => Promise<boolean>
  onComplete: () => void
}
const StartDownloadButton = ({ action, onComplete }: IStartDownloadProps) => {
  const [isDisabled, setIsDisabled] = useState(false)
  const textColor = isDisabled ? 'text-gray-400 hover:text-gray-400' : 'text-yellow-400'

  return (
    <button
      className={`h-12 w-full rounded-lg px-4 ${colorStyles} ${sizingStyles} ${textColor} text-sm hover:bg-yellow-500 hover:text-yellow-900`}
      disabled={isDisabled}
      onClick={async () => {
        setIsDisabled(true)
        const success = await action()
        if (success) {
          onComplete()
          return true
        }
        setIsDisabled(false)
        return
      }}
    >
      <p className="font-bold">Download</p>
    </button>
  )
}

/**
 * Stop the download and delete cached file.
 */
const CancelDownloadButton = ({ action }: { action: () => Promise<boolean> }) => {
  const [isDisabled, setIsDisabled] = useState(false)
  return (
    <button
      className={`h-12 w-min rounded-lg px-4 ${colorStyles} ${sizingStyles} text-sm text-white hover:bg-red-500 hover:text-white`}
      disabled={isDisabled}
      onClick={async () => {
        setIsDisabled(true)
        await action()
        setIsDisabled(false)
        return
      }}
    >
      <p className="font-bold">Cancel</p>
    </button>
  )
}

/**
 * Resume the download
 */
interface IResumeDownloadProps {
  action: () => Promise<boolean>
  onComplete: () => void
}
const ResumeButton = ({ action, onComplete }: IResumeDownloadProps) => {
  const [isDisabled, setIsDisabled] = useState(false)
  const textColor = isDisabled ? 'text-gray-400' : 'text-yellow-400'
  return (
    <button
      className={`h-12 w-min rounded-lg px-4 ${colorStyles} ${sizingStyles} ${textColor} text-sm hover:bg-yellow-500 hover:text-yellow-900`}
      disabled={isDisabled}
      onClick={async () => {
        setIsDisabled(true)
        const success = await action()
        if (success) onComplete()
        setIsDisabled(false)
        return
      }}
    >
      <p className="font-bold">Resume</p>
    </button>
  )
}

/**
 * Remove the model file
 */
const DeleteButton = ({ action }: { action: () => Promise<boolean> }) => {
  const [isDisabled, setIsDisabled] = useState(false)

  return (
    <button
      className={`h-12 w-full rounded-lg ${colorStyles} ${sizingStyles} text-sm text-red-500 hover:bg-red-500 hover:text-red-900`}
      disabled={isDisabled}
      onClick={async () => {
        setIsDisabled(true)
        await action()
        setIsDisabled(false)
        return
      }}
    >
      <p className="font-bold">Remove</p>
    </button>
  )
}

export {
  StartDownloadButton,
  CancelDownloadButton,
  LoadButton,
  ResumeButton,
  PauseButton,
  DeleteButton,
  CheckHardware,
  ImportModel,
}
