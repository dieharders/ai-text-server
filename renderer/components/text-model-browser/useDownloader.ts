import { useCallback, useEffect, useMemo, useState } from 'react'
import { IModelCard } from '@/models/models'
import { removeTextModelConfig, setUpdateTextModelConfig } from '@/utils/localStorage'
import { EValidationState, IModelConfig } from './configs'

export enum EProgressState {
  None = 'none',
  Idle = 'idle',
  Downloading = 'downloading',
  Validating = 'validating',
  Completed = 'completed',
  Errored = 'errored',
}

interface IProps {
  saveToPath: string
  modelCard: IModelCard
  loadModelConfig: () => IModelConfig | undefined
  saveModelConfig: (props: IModelConfig) => void
}

const useDownloader = ({ modelCard, saveToPath, loadModelConfig, saveModelConfig }: IProps) => {
  const [isInitialized, setIsInitialized] = useState(false)
  const [modelConfig, setModelConfig] = useState<IModelConfig | undefined>(undefined)
  const [progressState, setProgressState] = useState<EProgressState>(EProgressState.None)
  const [downloadProgress, setDownloadProgress] = useState<number>(0)
  const { id: modelId } = modelCard
  const apiPayload = useMemo(
    () => ({ config: modelConfig, modelCard, filePath: saveToPath }),
    [modelCard, modelConfig, saveToPath],
  )

  /**
   * Start the download of the chosen model from huggingface.
   * Could use this in the future: https://github.com/bodaay/HuggingFaceModelDownloader
   */
  const startDownload = useCallback(
    async (resume = false) => {
      const url = modelCard?.downloadUrl
      const fileName = modelCard?.fileName

      try {
        if (!saveToPath || !url || !fileName)
          throw Error(
            `No arguments provided! filePath: ${saveToPath} | url: ${url} | fileName: ${fileName}`,
          )

        // Download file in Main Process
        const eventName = resume ? 'resume_download' : 'start_download'
        const result = await window.electron.api(eventName, apiPayload)
        if (!result) throw Error('Failed to download file.')

        // Make record of installation in storage
        const newConfig = {
          modelId,
          ...result,
        }

        saveModelConfig(newConfig) // persistent storage
        setModelConfig(newConfig) // local (component) state

        return true
      } catch (err) {
        console.log('[Downloader] Error:', err)
        return false
      }
    },
    [apiPayload, modelCard?.downloadUrl, modelCard?.fileName, modelId, saveModelConfig, saveToPath],
  )
  // Remove config record
  const deleteConfig = useCallback(() => {
    removeTextModelConfig(modelId)
    console.log(`[Downloader] Config ${modelId} removed successfully!`)
  }, [modelId])
  // Delete file
  const deleteFile = useCallback(async () => {
    const success = await window.electron.api('delete_file', apiPayload)

    if (success) {
      console.log('[Downloader] Model file removed successfully!')
      deleteConfig()
      // Set the state
      setModelConfig(undefined)
      return true
    }

    console.log('[Downloader] File removal failed!', success)
    return false
  }, [apiPayload, deleteConfig])
  /**
   * Stop the download and remove the assets.
   * @returns Promise<boolean>
   */
  const cancelDownload = useCallback(async () => {
    return deleteFile()
  }, [deleteFile])
  /**
   * Stop the download but allow to resume.
   * @returns Promise<string>
   */
  const pauseDownload = useCallback(async () => {
    const newState: EProgressState = await window.electron.api('pause_download', apiPayload)
    return newState
  }, [apiPayload])
  /**
   * Remove the download assets from disk and state.
   * @returns Promise<boolean>
   */
  const deleteDownload = useCallback(async () => {
    // Ask user before deleting
    const options = {
      type: 'question',
      buttons: ['Yes', 'Cancel'],
      defaultId: 1,
      title: 'Delete file',
      message: `Do you really want to delete the file "${modelCard.name}" ?`,
      detail: 'Confirm you want to remove this Ai text model',
    }
    const confirmed = await window.electron.api('showConfirmDialog', options)
    // "No" was pressed
    if (confirmed !== 0) return false

    return deleteFile()
  }, [deleteFile, modelCard.name])

  // Set our local state initially since the backend doesnt know
  useEffect(() => {
    if (!isInitialized) {
      if (modelConfig?.validation === EValidationState.Success)
        setProgressState(EProgressState.Completed)
      setIsInitialized(true)
    }
  }, [isInitialized, modelConfig?.validation])

  // Listen to main process for `progress` events
  useEffect(() => {
    const handler = (_event: any, payload: any) => {
      if (payload.downloadId !== modelId) return

      switch (payload.eventId) {
        case 'download_progress':
          console.log(
            '[Downloader] "progress" event:',
            payload.eventId,
            'progress:',
            payload.data,
            'modelId:',
            payload.downloadId,
          )
          setDownloadProgress(payload.data)
          break
        case 'download_progress_state':
          console.log('[Downloader] "progress state" event:', payload.eventId)
          setProgressState(payload.data)
          break
        case 'update-text-model': {
          return setUpdateTextModelConfig(payload.id, payload.data)
        }
        default:
          break
      }
    }

    window.electron.message.on(handler)

    return () => {
      window.electron.message.off(handler)
    }
  }, [modelId])

  // Load and update model config from storage whenever progress state changes
  useEffect(() => {
    const c = loadModelConfig()
    if (!c) return

    const progress = c?.progress ?? 0
    setModelConfig(c)
    // We shouldnt have to do this here but the backend has no access to initial `config` state.
    // This allows UI to display correctly when restoring from previous download.
    if (progressState === EProgressState.None && progress > 0) setProgressState(EProgressState.Idle)
    setDownloadProgress(progress)
    console.log('[Downloader] Updating config data', c?.id)
  }, [loadModelConfig, progressState])

  return {
    modelConfig,
    progressState,
    downloadProgress,
    startDownload,
    pauseDownload,
    cancelDownload,
    deleteDownload,
  }
}

export default useDownloader
