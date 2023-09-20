import { useCallback, useEffect, useMemo, useState } from 'react'
import { IModelCard } from '@/models/models'
import { removeTextModelConfig, setUpdateTextModelConfig } from '@/utils/localStorage'
import { IModelConfig } from './configs'

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
  saveModelConfig: (props: any) => void
}

const useDownloader = ({ modelCard, saveToPath, loadModelConfig, saveModelConfig }: IProps) => {
  const [isInitialized, setIsInitialized] = useState(false)
  const [modelConfig, setModelConfig] = useState<IModelConfig | undefined>(undefined)
  const [progressState, setProgressState] = useState<EProgressState>(EProgressState.None)
  const [downloadProgress, setDownloadProgress] = useState<number | null>(null)
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
        console.log('@@ [Error]:', err)
        return
      }
    },
    [apiPayload, modelCard?.downloadUrl, modelCard?.fileName, modelId, saveModelConfig, saveToPath],
  )
  /**
   * Stop the download and remove the assets.
   * @returns Promise<string>
   */
  const cancelDownload = useCallback(async () => {
    const newState: EProgressState = await window.electron.api('cancel_download', apiPayload)
    return newState
  }, [apiPayload])
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
    // Delete file
    const success = await window.electron.api('delete_file', apiPayload)
    if (success) {
      // Remove config record
      removeTextModelConfig(modelId)
      console.log(`@@ File ${modelId} removed successfully!`)
      // Set the state
      setModelConfig(undefined)
      return true
    }
    console.log('@@ File removal failed!', success)
    return false
  }, [apiPayload, modelCard.name, modelId])

  // Set our local state initially since the backend doesnt know
  useEffect(() => {
    if (!isInitialized) {
      if (modelConfig?.validation === 'success') setProgressState(EProgressState.Completed)
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
            '@@ [UI] "progress" event:',
            payload.eventId,
            'progress:',
            payload.data,
            'modelId:',
            payload.downloadId,
          )
          setDownloadProgress(payload.data)
          break
        case 'download_progress_state':
          console.log('@@ [UI] "progress state" event:', payload.eventId)
          setProgressState(payload.data)
          break
        case 'delete-text-model': {
          setProgressState(payload.data)
          return removeTextModelConfig(modelId)
        }
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
    const progress = c?.progress
    setModelConfig(c)
    setDownloadProgress(progress ?? null)
    console.log('@@ [UI] Updating config data')
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
