'use client'

import axios from 'axios'
import { useEffect, useState } from 'react'

interface IProps {
  id: string
  name: string
  description: string
  fileSize: number
  downloadUrl: string
  saveToPath: string
  fileName: string
  isLoaded: boolean
  initialHasDownload: boolean
  onSelectModel: (modelId: string) => void
  onDownloadComplete: (modelId: string) => void
}

const ModelCard = ({
  id,
  name,
  description,
  fileSize,
  downloadUrl,
  saveToPath,
  fileName,
  isLoaded,
  initialHasDownload,
  onSelectModel,
  onDownloadComplete,
}: IProps) => {
  const [downloadProgress, setDownloadProgress] = useState<number | null>(null)
  const [hasDownload, setHasDownload] = useState<boolean>(initialHasDownload)
  const sizingStyles = 'lg:static lg:w-auto sm:border lg:bg-gray-200 sm:p-4 lg:dark:bg-zinc-800/30'
  const colorStyles =
    'border-b border-gray-300 bg-gradient-to-b from-zinc-200 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit'

  /**
   * This will do for now...
   * But we could use this in the future: https://github.com/bodaay/HuggingFaceModelDownloader
   */
  const onModelDownload = async (
    url: string,
    filePath: string,
    fileName: string,
    modelId: string,
  ) => {
    if (!filePath || !url || !fileName) throw Error('No arguments provided!')

    try {
      const response = await axios({
        url,
        method: 'GET',
        responseType: 'arraybuffer', // 'blob' | 'stream' | 'arraybuffer' | 'json'
        withCredentials: false,
        onDownloadProgress: progressEvent => {
          const total = progressEvent.total || 1000000000
          const percentCompleted = Math.round((progressEvent.loaded * 100) / total)
          // Handle file progress
          console.log('@@ file progress:', percentCompleted)
          setDownloadProgress(percentCompleted)
        },
      })

      // Write response.data to file
      const { writeBinaryFile, exists, createDir } = await import('@tauri-apps/api/fs')

      // Check that file and target path exists
      const fileExists = await exists(`${filePath}\\${fileName}`)
      if (fileExists) throw Error('File already exists')
      const pathExists = await exists(filePath)
      if (!pathExists) await createDir(filePath)

      // In order to write to chosen path (w/o user action) on subsequent restarts, we need to use plugin-persisted-scope
      // When a user chooses a path, it is added dynamically to `fs: scope: []` but only for that session.
      await writeBinaryFile({
        path: `${filePath}\\${fileName}`,
        contents: response.data,
      })

      // Mark download completed
      onDownloadComplete(modelId)
      setHasDownload(true)

      return true
    } catch (err) {
      console.log('@@ [Error] Failed to download file:', err)
      return
    }
  }

  /**
   * This button selects this model for inference
   */
  const renderLoadButton = () => {
    return (
      <div className={`rounded-l-xl rounded-r-none ${colorStyles} ${sizingStyles}`}>
        <button disabled={isLoaded || !hasDownload} onClick={() => onSelectModel(id)}>
          <code
            className="font-mono font-bold"
            style={{ color: `${hasDownload ? 'yellow' : 'grey'}` }}
          >
            Download
          </code>
        </button>
      </div>
    )
  }
  /**
   * Download this ai model from a repository
   */
  const renderDownloadButton = () => {
    return (
      <div className={`rounded-l-xl rounded-r-none ${colorStyles} ${sizingStyles}`}>
        <button
          disabled={hasDownload || downloadProgress !== null}
          onClick={async () => {
            // Download model from huggingface
            const success = await onModelDownload(downloadUrl, saveToPath, fileName, id)
            if (success) console.log('@@ File saved successfully!')
          }}
        >
          <code
            className="font-mono font-bold"
            style={{ color: `${hasDownload || downloadProgress !== null ? 'grey' : 'yellow'}` }}
          >
            Download
          </code>
        </button>
      </div>
    )
  }

  useEffect(() => {
    return () => {
      // @TODO If we unmount, we should delete any in progress file
      if (downloadProgress !== null) console.log('@@ cleanup model card')
    }
  }, [downloadProgress])

  return (
    <div className="w-full flex-row">
      <h1>
        {name}--size:{fileSize} bytes
      </h1>
      <p>{description}</p>
      <div className="inline-flex">
        {renderLoadButton()}
        {renderDownloadButton()}
      </div>
      {downloadProgress !== null && downloadProgress >= 0 && <span>{downloadProgress}%</span>}
    </div>
  )
}
export default ModelCard
