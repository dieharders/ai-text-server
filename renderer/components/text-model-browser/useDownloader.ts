import { useEffect, useState } from 'react'
import { IConfigProps, IModelConfig } from './configs'

export enum EProgressState {
  None = 'none',
  Idle = 'idle',
  Downloading = 'downloading',
  Validating = 'validating',
  Completed = 'completed',
  Errored = 'errored',
}

interface IProps {
  modelId: string
  setModelConfig: (props: IConfigProps) => void
}

const useDownloader = ({ modelId, setModelConfig }: IProps) => {
  const [config, setConfig] = useState<IModelConfig | undefined>(undefined)
  const [progressState, setProgressState] = useState<EProgressState>(EProgressState.None)
  const [downloadProgress, setDownloadProgress] = useState<number | null>(null)
  const [hasDownload, setHasDownload] = useState<boolean>(false)

  /**
   * Start the download of the chosen model.
   * Could use this in the future: https://github.com/bodaay/HuggingFaceModelDownloader
   */
  const onModelDownload = async (
    url: string,
    filePath: string,
    fileName: string,
    signature = '',
  ) => {
    try {
      if (!filePath || !url || !fileName)
        throw Error(
          `No arguments provided! filePath: ${filePath} | url: ${url} | fileName: ${fileName}`,
        )

      // Start download
      setProgressState(EProgressState.Downloading)

      // Download file in Main Process
      const fileOptions = { path: filePath, name: fileName, url, id: modelId, signature }
      const result = await window.electron.api('download_chunked_file', fileOptions)
      if (!result) throw Error('Failed to download file.')

      // Reset downloader state
      setProgressState(EProgressState.None)
      setDownloadProgress(null)

      // Make record of installation in storage
      setModelConfig({
        modelId,
        savePath: result?.savePath,
        modified: result?.modified,
        validation: result?.validation,
        size: result?.size,
        ...(result?.tokenizerPath && { tokenizerPath: result?.tokenizerPath }),
        ...(result?.endByte && { endByte: result?.endByte }),
      })
      setHasDownload(true)

      return true
    } catch (err) {
      console.log('@@ [Error]:', err)
      return
    }
  }

  const cancelDownload = () => {}
  const pauseDownload = () => {}
  const resumeDownload = () => {}

  // Listen to main process for `progress` events
  useEffect(() => {
    const handler = (_event: any, payload: any) => {
      switch (payload.eventId) {
        case 'download_progress':
          if (payload.downloadId === modelId) {
            console.log(
              '@@ [progress] event',
              payload.eventId,
              'progress:',
              payload.data,
              'modelId:',
              payload.downloadId,
            )
            setDownloadProgress(payload.data)
          }
          break
        case 'download_progress_state':
          if (payload.downloadId === modelId) {
            console.log('@@ [Downloader] state:', payload.eventId)
            setProgressState(payload.data)
          }
          break
        default:
          break
      }
    }
    window.electron.message.on(handler)

    return () => {
      window.electron.message.off(handler)
    }
  }, [modelId])

  return {
    hasDownload,
    setHasDownload,
    config,
    setConfig,
    progressState,
    downloadProgress,
    onModelDownload,
    pauseDownload,
    resumeDownload,
    cancelDownload,
  }
}

export default useDownloader
