'use client'

import { useState } from 'react'
import useDownloader, { EProgressState } from './useDownloader'
import { IModelCard } from '@/models/models'
import { IModelConfig } from './configs'

interface IProps {
  modelCard: IModelCard
  isLoaded: boolean
  saveToPath: string
  onSelectModel: (modelId: string) => void
  onDownloadComplete: () => void
  loadModelConfig: () => IModelConfig | undefined
  saveModelConfig: (props: any) => void
}

const ModelCard = ({
  modelCard,
  saveToPath,
  isLoaded,
  onSelectModel,
  onDownloadComplete,
  loadModelConfig,
  saveModelConfig,
}: IProps) => {
  // Vars
  const { id, name, description, fileSize, ramSize, license, provider } = modelCard
  // Styling
  const sizingStyles = 'lg:static sm:border lg:bg-gray-200 lg:dark:bg-zinc-800/30'
  const colorStyles =
    'border-b border-gray-300 bg-gradient-to-b from-zinc-200 dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit'

  // Downloader Hook
  const {
    modelConfig,
    downloadProgress,
    progressState,
    startDownload,
    pauseDownload,
    cancelDownload,
    deleteDownload,
  } = useDownloader({ modelCard, saveToPath, loadModelConfig, saveModelConfig })

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
   * This button selects this model for inference
   */
  const LoadButton = () => {
    const textColor = !isLoaded ? 'text-yellow-300' : 'text-gray-400'
    const hoverStyle = !isLoaded
      ? 'hover:bg-zinc-700/30 hover:text-white'
      : 'hover:cursor-not-allowed'
    return (
      <button
        className={`h-12 w-full ${sizingStyles} rounded-lg border border-gray-300 text-center dark:border-neutral-800 dark:bg-zinc-800/30 ${hoverStyle} ${textColor}`}
        disabled={isLoaded}
        onClick={() => onSelectModel(id)}
      >
        <code className="text-md font-mono font-bold">Load</code>
      </button>
    )
  }
  /**
   * Download this ai model from a repository
   */
  const StartDownloadButton = () => {
    const [isDisabled, setIsDisabled] = useState(false)
    const textColor = isDisabled ? 'text-gray-400 hover:text-gray-400' : 'text-yellow-400'

    return (
      <button
        className={`h-12 w-full rounded-lg px-4 ${colorStyles} ${sizingStyles} ${textColor} text-sm hover:bg-yellow-500 hover:text-yellow-900`}
        disabled={isDisabled}
        onClick={async () => {
          setIsDisabled(true)
          const success = await startDownload()
          if (success) {
            onDownloadComplete()
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
  const CancelDownloadButton = () => {
    const [isDisabled, setIsDisabled] = useState(false)
    return (
      <button
        className={`h-12 w-min rounded-lg px-4 ${colorStyles} ${sizingStyles} text-sm text-white hover:bg-red-500 hover:text-white`}
        disabled={isDisabled}
        onClick={async () => {
          setIsDisabled(true)
          await cancelDownload()
          setIsDisabled(false)
          return
        }}
      >
        <p className="font-bold">Cancel</p>
      </button>
    )
  }
  /**
   * Pause the download
   */
  const PauseButton = () => {
    const [isDisabled, setIsDisabled] = useState(false)
    const textColor = downloadProgress !== null || !isDisabled ? 'text-white' : 'text-gray-400'

    return (
      <button
        className={`h-12 w-min rounded-lg px-4 ${colorStyles} ${sizingStyles} ${textColor} text-sm hover:bg-blue-500 hover:text-blue-100`}
        disabled={isDisabled}
        onClick={async () => {
          setIsDisabled(true)
          await pauseDownload()
          setIsDisabled(false)
          return
        }}
      >
        <p className="font-bold">Pause</p>
      </button>
    )
  }
  /**
   * Resume the download
   */
  const ResumeButton = () => {
    const [isDisabled, setIsDisabled] = useState(false)
    const textColor = isDisabled ? 'text-gray-400' : 'text-yellow-400'
    return (
      <button
        className={`h-12 w-min rounded-lg px-4 ${colorStyles} ${sizingStyles} ${textColor} text-sm hover:bg-yellow-500 hover:text-yellow-900`}
        disabled={isDisabled}
        onClick={async () => {
          setIsDisabled(true)
          const success = await startDownload(true)
          if (success) onDownloadComplete()
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
  const DeleteButton = () => {
    return (
      <button
        className={`h-12 w-full rounded-lg ${colorStyles} ${sizingStyles} text-sm text-red-500 hover:bg-red-500 hover:text-red-900`}
        onClick={deleteDownload}
      >
        <p className="font-bold">Remove</p>
      </button>
    )
  }
  /**
   * Render indicator of the total progress of download
   */
  const DownloadProgressBar = () => {
    const progress = downloadProgress && `${downloadProgress}%`
    return (
      <div className="w-full  self-end">
        <div className="mb-1 flex justify-between">
          <span className="font-mono text-sm font-medium text-yellow-600">
            <span className="capitalize">{progressState}</span> {progress}
          </span>
        </div>
        <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            className="h-2 rounded-full bg-yellow-400"
            style={{ width: `${downloadProgress}%` }}
          ></div>
        </div>
      </div>
    )
  }
  const loadRemoveMenu = (
    <div className="flex flex-row gap-4">
      <LoadButton />
      <DeleteButton />
    </div>
  )
  const downloadCheckHardwareMenu = (
    <div className="flex flex-row gap-4">
      <StartDownloadButton />
      <CheckHardware />
    </div>
  )
  const inProgressMenu = (
    <div className="flex flex-row gap-4">
      {progressState === EProgressState.Downloading && <PauseButton />}
      {(progressState === EProgressState.Idle || progressState === EProgressState.None) && (
        <ResumeButton />
      )}
      <CancelDownloadButton />
      <DownloadProgressBar />
    </div>
  )
  const renderDownloadPane = () => {
    if (modelConfig && downloadProgress === null) return loadRemoveMenu
    if (downloadProgress && downloadProgress >= 0) return inProgressMenu
    return downloadCheckHardwareMenu
  }

  return (
    <div className="flex flex-col items-stretch justify-start gap-6 rounded-md border border-gray-300 p-6 dark:border-neutral-800 dark:bg-zinc-900 lg:flex-row">
      {/* Info/Stats */}
      <div className="inline-flex w-full shrink-0 flex-col items-stretch justify-start gap-2 break-words p-0 lg:w-72">
        <h1 className="mb-2 text-left text-xl leading-tight">{name}</h1>
        <p className="text-md overflow-hidden text-ellipsis whitespace-nowrap text-left">
          Disk: {fileSize} Gb
        </p>
        {ramSize && (
          <p className="overflow-hidden text-ellipsis whitespace-nowrap text-left text-sm">
            RAM: {ramSize} Gb
          </p>
        )}
        <p className="overflow-hidden text-ellipsis whitespace-nowrap text-left text-sm">
          Provider: {provider}
        </p>
        <p className="overflow-hidden text-ellipsis whitespace-nowrap text-left text-sm">
          License: {license}
        </p>
      </div>
      {/* Description & Load */}
      <div className="grow-1 inline-flex w-full flex-col items-stretch justify-between gap-4 p-0">
        <div className="h-48 overflow-hidden">
          {/* Text */}
          <p className="h-full overflow-hidden leading-normal">{description}</p>
          {/* Text Gradient Overlay, "bottom-[n]" must match "h-[n]" of parent container */}
          <div className="relative h-full">
            <div className="absolute bottom-48 left-0 h-full w-full bg-gradient-to-t from-zinc-900 from-10% to-transparent to-35%"></div>
          </div>
        </div>
        {/* Load | Download | Progress */}
        <div className="mb-0 mt-auto">{renderDownloadPane()}</div>
      </div>
    </div>
  )
}
export default ModelCard
