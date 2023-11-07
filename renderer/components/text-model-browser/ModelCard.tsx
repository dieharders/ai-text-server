'use client'

import useDownloader, { EProgressState } from './useDownloader'
import { IModelCard } from '@/models/models'
import { EValidationState, IModelConfig } from './configs'
import {
  CancelDownloadButton,
  CheckHardware,
  DeleteButton,
  LoadButton,
  PauseButton,
  ResumeButton,
  StartDownloadButton,
} from './ModelCardButtons'

interface IProps {
  modelCard: IModelCard
  isLoaded: boolean
  saveToPath: string
  onSelectModel: (modelId: string) => void
  onDownloadComplete: () => void
  loadModelConfig: () => IModelConfig | undefined
  saveModelConfig: (props: IModelConfig) => void
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
  const { id, name, description, fileSize, ramSize, licenses, provider } = modelCard

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
   * Render indicator of the total progress of download
   */
  const DownloadProgressBar = () => {
    const progress = () => {
      if (downloadProgress && progressState === EProgressState.Downloading)
        return `${downloadProgress}%`
      return null
    }

    let errorMsg
    const isInvalid = modelConfig?.validation === EValidationState.Fail
    const isErrored = progressState === EProgressState.Errored
    if (isInvalid) errorMsg = ' File integrity failed. Please re-download.'
    else if (isErrored)
      errorMsg = 'Something went wrong. Check the target folder has write privileges.'

    const label = (
      <div>
        <span className="capitalize">{progressState}</span> {progress()}
      </div>
    )

    const progressBarComponent = (
      <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
        <div
          className="h-2 rounded-full bg-yellow-400"
          style={{ width: `${downloadProgress}%` }}
        ></div>
      </div>
    )

    return (
      <div className="w-full  self-end">
        <div className="mb-1 flex justify-between">
          <span className="font-mono text-sm font-medium text-yellow-600">
            {/* Show progress label */}
            {!isInvalid && label}
            {/* Show error message */}
            {errorMsg}
          </span>
          {errorMsg && <CancelDownloadButton action={cancelDownload} />}
        </div>
        {!errorMsg && progressBarComponent}
      </div>
    )
  }

  const loadRemoveMenu = (
    <div className="flex flex-row gap-4">
      <LoadButton isLoaded={isLoaded} action={() => onSelectModel(id)} />
      <DeleteButton action={deleteDownload} />
    </div>
  )

  const cancelProgressMenu = (
    <div className="flex flex-row gap-4">
      <CancelDownloadButton action={cancelDownload} />
      <DownloadProgressBar />
    </div>
  )

  const downloadCheckHardwareMenu = (
    <div className="flex flex-row gap-4">
      <StartDownloadButton action={startDownload} onComplete={onDownloadComplete} />
      <CheckHardware />
    </div>
  )

  const inProgressMenu = (
    <div className="flex flex-row gap-4">
      {progressState === EProgressState.Downloading && <PauseButton action={pauseDownload} />}
      {progressState === EProgressState.Idle && (
        <ResumeButton action={() => startDownload(true)} onComplete={onDownloadComplete} />
      )}
      {(progressState === EProgressState.Idle || progressState === EProgressState.None) && (
        <CancelDownloadButton action={cancelDownload} />
      )}
      {(progressState === EProgressState.Idle ||
        progressState === EProgressState.Validating ||
        progressState === EProgressState.Downloading ||
        progressState === EProgressState.Errored) && <DownloadProgressBar />}
    </div>
  )

  const renderDownloadPane = () => {
    if (modelConfig?.validation === EValidationState.Success && downloadProgress === 100)
      return loadRemoveMenu
    if (modelConfig?.validation === EValidationState.Fail) return cancelProgressMenu
    if (progressState === EProgressState.None && downloadProgress === 0)
      return downloadCheckHardwareMenu
    return inProgressMenu
  }

  return (
    <div className="flex flex-col items-stretch justify-start gap-6 rounded-md border border-gray-300 p-6 dark:border-neutral-800 dark:bg-zinc-900 lg:flex-row">
      {/* Info/Stats */}
      <div className="inline-flex w-full shrink-0 flex-col items-stretch justify-start gap-2 break-words p-0 lg:w-72">
        <h1 className="mb-2 text-left text-xl leading-tight">{name}</h1>
        <p className="text-md truncate text-left">Disk: {fileSize} Gb</p>
        {ramSize && <p className="truncate text-left text-sm">RAM: {ramSize} Gb</p>}
        <p className="truncate text-left text-sm">Provider: {provider}</p>
        <p className="truncate text-left text-sm">License: {licenses.join(', ')}</p>
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
