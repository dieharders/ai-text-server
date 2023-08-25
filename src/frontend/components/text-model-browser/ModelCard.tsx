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
  license: string
  provider: string
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
  license,
  provider,
  isLoaded,
  initialHasDownload,
  onSelectModel,
  onDownloadComplete,
}: IProps) => {
  const [downloadProgress, setDownloadProgress] = useState<number | null>(null)
  const [hasDownload, setHasDownload] = useState<boolean>(initialHasDownload)
  // Styling
  const sizingStyles = 'lg:static sm:border lg:bg-gray-200 lg:dark:bg-zinc-800/30'
  const colorStyles =
    'border-b border-gray-300 bg-gradient-to-b from-zinc-200 dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit'

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
    try {
      if (!filePath || !url || !fileName)
        throw Error(
          `No arguments provided! filePath: ${filePath} | url: ${url} | fileName: ${fileName}`,
        )

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
  const renderDownloadButton = () => {
    const textColor = hasDownload || downloadProgress !== null ? 'text-gray-400' : 'text-yellow-300'
    return (
      <button
        className={`mb-0 mt-auto h-12 rounded-lg ${colorStyles} ${sizingStyles} ${textColor} text-sm hover:bg-zinc-700/30 hover:text-white`}
        disabled={hasDownload || downloadProgress !== null}
        onClick={async () => {
          // Download model from huggingface
          const success = await onModelDownload(downloadUrl, saveToPath, fileName, id)
          if (success) console.log('@@ File saved successfully!')
        }}
      >
        <p className="font-bold">Download</p>
      </button>
    )
  }
  /**
   * Render indicator of the total progress of download
   */
  const DownloadProgressBar = ({ progress }: { progress: number }) => {
    return (
      <div className="mb-0 mt-auto">
        <div className="mb-1 flex justify-between">
          <span className="font-mono text-sm font-medium text-blue-700 dark:text-white">
            {progress}% complete
          </span>
        </div>
        <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
          <div className="h-2 rounded-full bg-blue-600" style={{ width: `${progress}%` }}></div>
        </div>
      </div>
    )
  }

  useEffect(() => {
    return () => {
      // @TODO If we unmount, we should delete any in progress file
      if (downloadProgress !== null) console.log('@@ cleanup model card')
    }
  }, [downloadProgress])

  // @TODO Add a remove button to replace "Downloaded" to delete the file.
  return (
    <div className="flex flex-col items-stretch justify-start gap-6 rounded-md border border-gray-300 p-6 dark:border-neutral-800 dark:bg-zinc-900 lg:flex-row">
      {/* Info/Stats & Download */}
      <div className="inline-flex w-full shrink-0 flex-col items-stretch justify-start gap-2 break-words p-0 lg:w-72">
        <h1 className="mb-2 text-left text-xl leading-tight">{name}</h1>
        <p className="text-md overflow-hidden text-ellipsis whitespace-nowrap text-left">
          {fileSize} Gb
        </p>
        <p className="overflow-hidden text-ellipsis whitespace-nowrap text-left text-sm">
          Provider: {provider}
        </p>
        <p className="overflow-hidden text-ellipsis whitespace-nowrap text-left text-sm">
          License: {license}
        </p>
        {hasDownload ? (
          <div className="mb-0 mt-auto">Downloaded</div>
        ) : downloadProgress !== null && downloadProgress >= 0 ? (
          <DownloadProgressBar progress={downloadProgress} />
        ) : (
          renderDownloadButton()
        )}
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
        {renderLoadButton()}
      </div>
    </div>
  )
}
export default ModelCard
