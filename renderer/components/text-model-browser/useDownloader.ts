import { useEffect, useState } from 'react'

enum EProgressState {
  Idle = 'Idle',
  Downloading = 'Downloading',
  Saving = 'Saving',
  Validating = 'Validating',
  Completed = 'Completed',
}

interface IProps {
  initialHasDownload: boolean
  modelId: string
}

const useDownloader = ({ initialHasDownload, modelId }: IProps) => {
  const [progressState, setProgressState] = useState<EProgressState>(EProgressState.Idle)
  const [downloadProgress, setDownloadProgress] = useState<number | null>(null)
  const [hasDownload, setHasDownload] = useState<boolean>(initialHasDownload)

  /**
   * Start the download of the chosen model.
   * Could use this in the future: https://github.com/bodaay/HuggingFaceModelDownloader
   */
  const onModelDownload = async (url: string, filePath: string, fileName: string) => {
    try {
      if (!filePath || !url || !fileName)
        throw Error(
          `No arguments provided! filePath: ${filePath} | url: ${url} | fileName: ${fileName}`,
        )

      const exists = async (path: string) => {
        // @TODO Implement from electron
        // ...
        console.log('@@ exists?', path)
        return false
      }
      const createDir = async (path: string) => {
        // @TODO Implement from electron
        // ...
        console.log('@@ createDir', path)
        return
      }
      // Check that file and target path exists
      const path = `${filePath}\\${fileName}` // @TODO Need to join the paths correctly
      const fileExists = await exists(path)
      if (fileExists) throw Error('File already exists')
      // const pathExists = await exists(filePath)
      // if (!pathExists) await createDir(filePath)

      // Start download
      setProgressState(EProgressState.Downloading)

      // Download file in Main Process
      const fileOptions = { path: filePath, name: fileName, url, id: modelId }
      const downloadStarted = await window.electron.api('download_chunked_file', fileOptions)
      if (!downloadStarted) throw Error('Failed to download file.')
      console.log('@@ DL started', downloadStarted)

      // Mark download completed
      // setProgressState(EProgressState.Idle)
      // setDownloadProgress(0)
      // setHasDownload(true)

      return true
    } catch (err) {
      console.log('@@ [Error]:', err)
      return
    }
  }

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
            console.log('@@ [state] event', payload.eventId)
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
    progressState,
    downloadProgress,
    onModelDownload,
  }
}

export default useDownloader
