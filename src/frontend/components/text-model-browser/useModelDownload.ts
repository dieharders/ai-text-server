import { useEffect, useState } from 'react'
import { IModelCard } from '../../../../models/models'
import { useInit } from './useInit'

export enum EDownloadState {
  None = 'none',
  Idle = 'idle',
  Downloading = 'downloading',
  Validating = 'validating',
  Completed = 'completed',
  Errored = 'errored',
}

interface IProgressState {
  path: string
  progress: number
  size: number
  eventId: string
  downloadUrl: string
  downloadState: EDownloadState
  digest?: string
  error?: string
}

export const useModelDownload = (
  model: IModelCard,
  modelPath: string | null,
  setModelConfig: () => void,
) => {
  const [progress, setProgress] = useState(0)
  const [eventId, setEventId] = useState<string>(EDownloadState.None)
  const [hasDownload, setHasDownload] = useState<boolean>(false)
  const [downloadState, setDownloadState] = useState<EDownloadState>(EDownloadState.None)

  const syncDownloadState = async () => {
    const { invoke } = await import('@tauri-apps/api/tauri')
    const res = (await invoke('get_download_progress', {
      path: modelPath,
    }).catch<null>(_ => null)) as IProgressState

    if (!res) {
      return
    }

    setEventId(res.eventId)
    setProgress(res.progress)
    setDownloadState(res.downloadState as EDownloadState)
    console.log('@@ [Download Progress]:', res.eventId, res.progress, res.downloadState, res.size)

    // @TODO Check for final download state...
    if (res.downloadState === EDownloadState.Completed) {
      // Mark download completed
      setModelConfig()
      setHasDownload(true)
      // setIsDownloading(false)
      console.log('@@ File saved successfully!')
    }
  }

  // Get progress ??
  useInit(syncDownloadState, [model])

  // Update progress ??
  useEffect(() => {
    if (downloadState !== EDownloadState.Downloading || !eventId) {
      return
    }
    let unlisten: () => void
    const updateProgress = async () => {
      const { appWindow } = await import('@tauri-apps/api/window')
      console.log('@@ update progress', appWindow, eventId)
      // @TODO Do we ned to add window to allow list?
      unlisten = await appWindow.listen<IProgressState>(eventId, ({ payload }) => {
        setProgress(payload.progress)
        // setModelSize(payload.size)

        if (
          payload.downloadState === EDownloadState.Downloading ||
          payload.downloadState === EDownloadState.Validating
        ) {
          return
        }

        if (payload.downloadState === EDownloadState.Errored) {
          alert(payload.error)
        }

        console.log('@@ listening...', payload.downloadState)
        setDownloadState(payload.downloadState)
        unlisten?.()
      })
    }
    updateProgress()
    return () => {
      unlisten?.()
    }
  }, [downloadState, modelPath, eventId])

  const resumeDownload = async () => {
    const { invoke } = await import('@tauri-apps/api/tauri')
    await invoke('resume_download', {
      path: modelPath,
    })

    setDownloadState(EDownloadState.Downloading)
  }

  const pauseDownload = async () => {
    setDownloadState(EDownloadState.Validating)
    const { invoke } = await import('@tauri-apps/api/tauri')
    await invoke('pause_download', {
      path: modelPath,
    })
    setDownloadState(EDownloadState.Idle)
  }

  return {
    progress,
    downloadState,
    hasDownload,
    eventId,
    setDownloadState,
    resumeDownload,
    pauseDownload,
    setHasDownload,
  }
}
