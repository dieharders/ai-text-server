'use client'

import useDownloader, { EProgressState } from './useDownloader'
import { IModelCard } from '@/models/models'
import { useCallback, useEffect, useState } from 'react'
import { IConfigProps, IModelConfig } from './configs'
import { removeTextModelConfig } from '@/utils/localStorage'

interface IProps {
  modelCard: IModelCard
  isLoaded: boolean
  saveToPath: string
  onSelectModel: (modelId: string) => void
  onDownloadComplete: () => void
  getModelConfig: () => IModelConfig | undefined
  setModelConfig: (props: IConfigProps) => void
}

const ModelCard = ({
  modelCard,
  saveToPath,
  isLoaded,
  onSelectModel,
  onDownloadComplete,
  getModelConfig,
  setModelConfig,
}: IProps) => {
  // Vars
  const [startup, setStartup] = useState(false)
  const { id, name, description, fileSize, ramSize, downloadUrl, fileName, license, provider } =
    modelCard
  // Styling
  const sizingStyles = 'lg:static sm:border lg:bg-gray-200 lg:dark:bg-zinc-800/30'
  const colorStyles =
    'border-b border-gray-300 bg-gradient-to-b from-zinc-200 dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit'

  // Downloader Hook
  const {
    hasDownload,
    setHasDownload,
    config,
    setConfig,
    downloadProgress,
    progressState,
    onModelDownload,
    pauseDownload,
    cancelDownload,
    resumeDownload,
  } = useDownloader({
    modelId: id,
    setModelConfig,
  })

  /**
   * This button selects this model for inference
   */
  const LoadButton = () => {
    const textColor = hasDownload && !isLoaded ? 'text-yellow-300' : 'text-gray-400'
    const hoverStyle =
      hasDownload && !isLoaded
        ? 'hover:bg-zinc-700/30 hover:text-white'
        : 'hover:cursor-not-allowed'
    return (
      <button
        className={`h-12 w-full ${sizingStyles} rounded-lg border border-gray-300 text-center dark:border-neutral-800 dark:bg-zinc-800/30 ${hoverStyle} ${textColor}`}
        disabled={isLoaded || !hasDownload}
        onClick={() => onSelectModel(id)}
      >
        <code className="text-md font-mono font-bold">Load</code>
      </button>
    )
  }
  /**
   * Download this ai model from a repository
   */
  const DownloadButton = () => {
    const textColor = hasDownload || downloadProgress !== null ? 'text-gray-400' : 'text-yellow-400'
    return (
      <button
        className={`h-12 w-full rounded-lg px-4 ${colorStyles} ${sizingStyles} ${textColor} text-sm hover:bg-yellow-500 hover:text-yellow-900`}
        onClick={async () => {
          // Download model from huggingface
          const success = await onModelDownload(
            downloadUrl,
            saveToPath,
            fileName,
            modelCard?.sha256,
          )
          if (success) onDownloadComplete()
        }}
      >
        <p className="font-bold">Download</p>
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
   * Stop the download and delete cached file.
   */
  const CancelDownloadButton = () => {
    return (
      <button
        className={`h-12 w-min rounded-lg px-4 ${colorStyles} ${sizingStyles} text-sm text-white hover:bg-red-500 hover:text-white`}
        onClick={cancelDownload}
      >
        <p className="font-bold">Cancel</p>
      </button>
    )
  }
  /**
   * Pause the download
   */
  const PauseButton = () => {
    const textColor = hasDownload || downloadProgress !== null ? 'text-white' : 'text-yellow-400'
    return (
      <button
        className={`h-12 w-min rounded-lg px-4 ${colorStyles} ${sizingStyles} ${textColor} text-sm hover:bg-yellow-500 hover:text-yellow-900`}
        onClick={pauseDownload}
      >
        <p className="font-bold">Pause</p>
      </button>
    )
  }
  /**
   * Resume the download
   */
  const ResumeButton = () => {
    const textColor = hasDownload || downloadProgress !== null ? 'text-gray-400' : 'text-yellow-400'
    return (
      <button
        className={`h-12 w-min rounded-lg px-4 ${colorStyles} ${sizingStyles} ${textColor} text-sm hover:bg-yellow-500 hover:text-yellow-900`}
        onClick={resumeDownload}
      >
        <p className="font-bold">Resume</p>
      </button>
    )
  }
  const deleteAction = useCallback(
    async (id: string) => {
      // Ask user before deleting
      const options = {
        type: 'question',
        buttons: ['Yes', 'Cancel'],
        defaultId: 1,
        title: 'Delete file',
        message: `Do you really want to delete file ${name}?`,
        detail: 'Confirm you want to remove this Ai text model',
      }
      const confirmed = await window.electron.api('showConfirmDialog', options)
      // "No" was pressed
      if (confirmed !== 0) return
      // Delete file
      const success = await window.electron.api('delete_file', { path: config?.savePath })
      if (success) {
        // Remove config record
        removeTextModelConfig(id)
        console.log('@@ File removed successfully!', config?.savePath)
        // Set the state
        setHasDownload(false)
        return true
      }
      console.log('@@ File removal failed!', success)
      return false
    },
    [config, name, setHasDownload],
  )
  /**
   * Remove the model file
   */
  const DeleteButton = ({ id }: { id: string }) => {
    return (
      <button
        className={`h-12 w-full rounded-lg ${colorStyles} ${sizingStyles} text-sm text-red-500 hover:bg-red-500 hover:text-red-900`}
        onClick={async () => deleteAction(id)}
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
  const installedMenu = (
    <div className="flex flex-row gap-4">
      <LoadButton />
      <DeleteButton id={id} />
    </div>
  )
  const uninstalledMenu = (
    <div className="flex flex-row gap-4">
      <DownloadButton />
      <CheckHardware />
    </div>
  )
  const inProgressMenu = (
    <div className="flex flex-row gap-4">
      {progressState === EProgressState.Downloading && <PauseButton />}
      {progressState === EProgressState.Idle && <ResumeButton />}
      <CancelDownloadButton />
      <DownloadProgressBar />
    </div>
  )
  const renderDownloadPane = () => {
    if (hasDownload) return installedMenu
    if (downloadProgress && downloadProgress >= 0) return inProgressMenu
    return uninstalledMenu
  }

  // Determine if we have installed this model already
  useEffect(() => {
    const model = getModelConfig()
    if (!startup) {
      setHasDownload(model ? true : false)
      setStartup(true)
    }
    setConfig(model)
  }, [getModelConfig, setConfig, setHasDownload, hasDownload, startup])

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
