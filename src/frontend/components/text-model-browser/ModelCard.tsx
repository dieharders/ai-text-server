'use client'

import { useEffect, useRef } from 'react'
import { IModelCard } from '../../../../models/models'
import { useModelDownload } from './useModelDownload'
import { EDownloadState } from './useModelDownload'

interface IProps {
  modelCard: IModelCard
  isLoaded: boolean
  saveToPath: string
  onSelectModel: (modelId: string) => void
  getModelConfig: () => boolean // all attributes, install path, etc
  setModelConfig: () => void
}

// command names...delete later
// GetDownloadProgress = "get_download_progress",
// StartDownload = "start_download",
// PauseDownload = "pause_download",
// ResumeDownload = "resume_download",
// whats these ??
// GetCachedIntegrity = "get_cached_integrity",
// ComputeModelIntegrity = "compute_model_integrity",

// @TODO Collapse the props into a `model` prop
const ModelCard = ({
  modelCard,
  saveToPath,
  isLoaded,
  onSelectModel,
  getModelConfig,
  setModelConfig,
}: IProps) => {
  const {
    id,
    name,
    description,
    fileSize,
    ramSize,
    downloadUrl,
    blake3,
    fileName,
    license,
    provider,
  } = modelCard
  const modelPath = useRef<string | null>(null) // track installed path for later retrieval
  const {
    progress,
    downloadState,
    eventId,
    hasDownload,
    setDownloadState,
    setHasDownload,
    pauseDownload,
    resumeDownload,
  } = useModelDownload(modelCard, modelPath.current, setModelConfig)
  // Styling
  const sizingStyles = 'lg:static sm:border lg:bg-gray-200 lg:dark:bg-zinc-800/30'
  const colorStyles =
    'border-b border-gray-300 bg-gradient-to-b from-zinc-200 dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit'

  /**
   * Could also use this: https://github.com/bodaay/HuggingFaceModelDownloader
   */
  const onModelDownload = async (
    url: string,
    filePath: string,
    fileName: string,
    modelId: string,
  ) => {
    let outputPath: string

    try {
      if (!filePath || !url || !fileName)
        throw Error(
          `No arguments provided! filePath: ${filePath} | url: ${url} | fileName: ${fileName}`,
        )

      // Check that file and target path exists, otherwise create one
      const { exists, createDir } = await import('@tauri-apps/api/fs')
      // const fileExists = await exists(`${filePath}\\${fileName}`)
      // if (fileExists) throw Error('File already exists')
      const pathExists = await exists(filePath)
      if (!pathExists) await createDir(filePath)

      // Download model
      setDownloadState(EDownloadState.Downloading)
      const { invoke } = await import('@tauri-apps/api/tauri')
      // @TODO What difference between filePath and saveToPath ??
      console.log('@@ download:', id, 'file', filePath, 'save', saveToPath)

      outputPath = await invoke('start_download', {
        fileName: id,
        downloadUrl: downloadUrl,
        digest: blake3,
        filePath: saveToPath,
      })

      return outputPath
    } catch (e) {
      console.log(`[Error] Failed to download file: ${e}`)
      return null
    }
  }
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
        className={`h-12 rounded-lg border border-gray-300 text-center dark:border-neutral-800 dark:bg-zinc-800/30 ${hoverStyle} ${textColor}`}
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
    const textColor = hasDownload || progress !== null ? 'text-gray-400' : 'text-yellow-400'
    return (
      <button
        className={`h-12 w-full rounded-lg px-4 ${colorStyles} ${sizingStyles} ${textColor} text-sm hover:bg-yellow-500 hover:text-yellow-900`}
        onClick={async () => {
          // Download model from huggingface
          const ouputPath = await onModelDownload(downloadUrl, saveToPath, fileName, id)
          modelPath.current = ouputPath
        }}
      >
        <p className="font-bold">Download</p>
      </button>
    )
  }
  /**
   * Pause the download
   */
  const PauseButton = () => {
    const textColor = hasDownload || progress !== null ? 'text-gray-400' : 'text-yellow-400'
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
    const textColor = hasDownload || progress !== null ? 'text-gray-400' : 'text-yellow-400'
    return (
      <button
        className={`h-12 w-min rounded-lg px-4 ${colorStyles} ${sizingStyles} ${textColor} text-sm hover:bg-yellow-500 hover:text-yellow-900`}
        onClick={resumeDownload}
      >
        <p className="font-bold">Resume</p>
      </button>
    )
  }
  /**
   * Remove the model file
   */
  const DeleteButton = ({ id }: { id: string }) => {
    return (
      <button
        className={`h-12 w-full rounded-lg ${colorStyles} ${sizingStyles} text-sm text-red-500 hover:bg-red-500 hover:text-red-900`}
        onClick={async () => {
          // Ask user before deleting
          const { confirm } = await import('@tauri-apps/api/dialog')
          if (!(await confirm(`Deleting ${name}?`))) {
            return
          }
          // @TODO Add logic to delete file
          const { invoke } = await import('@tauri-apps/api/tauri')
          await invoke('delete_model_file', {
            path: saveToPath,
          })
          console.log('@@ File removed successfully!', id)
        }}
      >
        <p className="font-bold">Remove</p>
      </button>
    )
  }
  /**
   * Render indicator of the total progress of download
   */
  const DownloadProgressBar = ({ downloadProgress }: { downloadProgress: number }) => {
    return (
      <div className="w-full self-end">
        <div className="mb-1 flex justify-between">
          <span className="font-mono text-sm font-medium text-yellow-600">
            <span className="capitalize">{downloadState}</span> {downloadProgress}%
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

  // Determine if we have installed this model already
  useEffect(() => {
    setHasDownload(getModelConfig())
  }, [getModelConfig, setHasDownload])

  return (
    <div className="flex flex-col items-stretch justify-start gap-6 rounded-md border border-gray-300 p-6 dark:border-neutral-800 dark:bg-zinc-900 lg:flex-row">
      <div className="inline-flex w-full shrink-0 flex-col items-stretch justify-start gap-2 break-words p-0 lg:w-72">
        {/* Info/Stats */}
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
        {/* Download | Pause/Resume | Progress */}
        <div className="mb-0 mt-auto">
          {hasDownload ? (
            <DeleteButton id={id} />
          ) : eventId === EDownloadState.Downloading ||
            eventId === EDownloadState.Validating ||
            eventId === EDownloadState.Idle ? (
            <div className="flex flex-row gap-4">
              {eventId === EDownloadState.Downloading && <PauseButton />}
              {eventId === EDownloadState.Idle && <ResumeButton />}
              <DownloadProgressBar downloadProgress={progress} />
            </div>
          ) : (
            <DownloadButton />
          )}
        </div>
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
        <LoadButton />
      </div>
    </div>
  )
}
export default ModelCard
