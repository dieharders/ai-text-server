'use client'

import useDownloader from './useDownloader'

interface IProps {
  id: string
  name: string
  description: string
  fileSize: number
  ramSize?: number
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
  ramSize,
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
  // Styling
  const sizingStyles = 'lg:static sm:border lg:bg-gray-200 lg:dark:bg-zinc-800/30'
  const colorStyles =
    'border-b border-gray-300 bg-gradient-to-b from-zinc-200 dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit'

  // Downloader Hook
  const { hasDownload, downloadProgress, progressState, onModelDownload } = useDownloader({
    initialHasDownload,
    modelId: id,
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
    const textColor = hasDownload || downloadProgress !== null ? 'text-gray-400' : 'text-yellow-400'
    return (
      <button
        className={`h-12 w-full rounded-lg px-4 ${colorStyles} ${sizingStyles} ${textColor} text-sm hover:bg-yellow-500 hover:text-yellow-900`}
        onClick={async () => {
          // Download model from huggingface
          const success = await onModelDownload(downloadUrl, saveToPath, fileName)
          if (success) {
            // onDownloadComplete(id)
            console.log('@@ File saved successfully!')
          }
        }}
      >
        <p className="font-bold">Download</p>
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
          // @TODO Add logic to delete file
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
  const DownloadProgressBar = ({ progress }: { progress: number }) => {
    return (
      <div className="w-full">
        <div className="mb-1 flex justify-between">
          <span className="font-mono text-sm font-medium text-yellow-600">
            {`${progress}% ${progressState}`}
          </span>
        </div>
        <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
          <div className="h-2 rounded-full bg-yellow-400" style={{ width: `${progress}%` }}></div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-stretch justify-start gap-6 rounded-md border border-gray-300 p-6 dark:border-neutral-800 dark:bg-zinc-900 lg:flex-row">
      {/* Info/Stats & Download */}
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
        <div className="mb-0 mt-auto">
          {hasDownload ? (
            <DeleteButton id={id} />
          ) : downloadProgress !== null && downloadProgress >= 0 ? (
            <DownloadProgressBar progress={downloadProgress} />
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
