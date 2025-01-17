/* eslint-disable @typescript-eslint/no-var-requires */

// This module is not currently used. Here for ref.

const EValidationState = Object.freeze({
  Success: 'success',
  Fail: 'fail',
  None: 'none',
})

const EProgressState = Object.freeze({
  None: 'none',
  Idle: 'idle',
  Downloading: 'downloading',
  Validating: 'validating',
  Completed: 'completed',
  Errored: 'errored',
})

// 3rd party Modules
const axios = require('axios')

/**
 * Query the server to determine the total size and modified date of file.
 * @param {string} url
 * @returns
 */
const fetchTotalSize = async url => {
  console.log('[Downloader] Fetching headers...')
  const response = await axios({
    url,
    method: 'HEAD',
  })
  return {
    size: response?.headers?.['content-length'],
    modified: response?.headers?.['last-modified'],
  }
}

/**
 * Download a chunk in range {start, end}
 * @param string url
 * @param number start
 * @param number end
 * @returns Promise<AxiosResponse<any, any>>
 */
const fetchChunk = async ({ url, start = 0, end }) => {
  if (!url || !end) return

  const response = await axios({
    url,
    method: 'GET',
    headers: {
      Accept: 'application/octet-stream, application/json, text/plain, */*',
      Range: `bytes=${start}-${end}`, // used to get partial file from specific range in data: bytes=0-1023
    },
    responseType: 'arraybuffer', // 'blob' | 'stream' | 'arraybuffer' | 'json'
    withCredentials: false,
    maxContentLength: Infinity,
    maxBodyLength: Infinity,
  })

  return response
}

const _createBinaryChunk = data => {
  const vec8 = new Uint8Array(data)
  const binaryChunk = Array.from(vec8)
  if (!binaryChunk) throw Error('Error creating binary chunk!')
  return binaryChunk
}

const createUint8ArrayChunk = data => {
  const vec8 = new Uint8Array(data)
  if (!vec8) throw Error('Error creating Uint8Array chunk!')
  return vec8
}

/**
 * Save chunk to file stream.
 * @param ArrayBuffer chunk
 * @param Function handler
 * @returns
 */
const onDownloadProgress = async (chunk, handleChunk) => {
  // Handle data conversion
  const data = createUint8ArrayChunk(chunk)
  // Save chunks here
  await handleChunk(data)
  return data
}

/**
 * Return a size in bytes
 * @param {string} filePath
 * @returns number
 */
const createFileSize = filePath => {
  const fs = require('fs')
  const stats = fs.statSync(filePath)
  return stats.size
}

/**
 * Read a file from disk and create a hash for comparison to a verified signature.
 * @param {string} filePath
 * @param {string} signature
 * @returns Promise<string>
 */
const hashEntireFile = async filePath => {
  const crypto = require('crypto')
  const hs = crypto.createHash('sha256').setEncoding('hex')
  let fileHash = ''

  return new Promise((resolve, _reject) => {
    const fs = require('fs')

    fs.createReadStream(filePath)
      .pipe(hs)
      .on('finish', () => {
        fileHash = hs.read()
        console.log(`[Downloader] Filehash calculated: ${fileHash}`)
        // Verified
        if (fileHash) resolve(fileHash)
        else resolve('')
      })
  })
}

/**
 * Create a new instance (closure) of a downloader service which will
 * hand back callbacks for consumers to use to change its state (pause, etc.)
 */
const downloader = payload => {
  // Card info
  const modelCard = payload?.modelCard
  const filePath = payload?.filePath
  const fileName = modelCard?.fileName
  const signature = modelCard?.sha256
  const downloadUrl = modelCard?.downloadUrl
  const id = modelCard?.id
  // Config data (local state)
  const config = payload?.config
  let validation = config?.validation
  let lastModified = config?.modified
  let savePath = config?.savePath
  let progress = config?.progress ?? 0
  let endChunk = config?.endChunk
  // Other
  let fileStream
  let hash // object used to create checksum from chunks
  let state = progress > 0 ? EProgressState.Idle : EProgressState.None
  const ipcEvent = payload?.event

  /**
   * Send ipc command to front-end to update total progress
   * @param {number} amount
   * @returns
   */
  const updateProgress = amount => {
    console.log('[Downloader] Download progress:', amount)
    ipcEvent.sender.send('message', {
      eventId: 'download_progress',
      downloadId: id,
      data: amount,
    })
    return amount
  }
  /**
   * Send ipc command to front-end to update state of progress
   * @param {string} val
   * @returns
   */
  const updateProgressState = val => {
    console.log('[Downloader] updateProgressState:', val)
    state = val
    ipcEvent.sender.send('message', {
      eventId: 'download_progress_state',
      downloadId: id,
      data: val,
    })
    return val
  }
  /**
   * Download in chunks, create checksum and save model file to disk.
   * @param {object} isResume
   * @returns IConfigProps
   */
  const writeStreamFile = async (isResume = false) => {
    const fs = require('fs')
    const { join } = require('path')
    const startChunk = endChunk
    // Create file stream, if this is resume, set stream to append from supplied `start`
    const writePath = join(filePath, fileName)
    savePath = writePath
    console.log(
      '[Downloader] Created write stream, startChunk:',
      startChunk,
      'writePath:',
      writePath,
      'url:',
      downloadUrl,
    )
    const options = startChunk > 0 ? { flags: 'a' } : null
    // Open handler
    fileStream = fs.createWriteStream(writePath, options)
    // Create crypto hash object and update with each chunk.
    // Dont create a chunked hash if we are resuming from cold boot.
    const shouldCreateChunkedHashing =
      signature &&
      !hash &&
      progress === 0 &&
      (validation === undefined || validation === EValidationState.None)

    if (shouldCreateChunkedHashing) {
      const crypto = require('crypto')
      hash = crypto.createHash('sha256')
    }
    /**
     * Save chunk to stream
     * @param {Uint8Array} chunk
     * @returns
     */
    const handleChunk = async chunk => {
      // Update the hash with chunk content
      if (hash) hash.update(chunk, 'binary')
      // Save chunk to disk
      console.log('[Downloader] Saving chunk...chunk:', endChunk)
      return fileStream.write(chunk)
    }
    // Download file
    const result = await downloadChunkedFile({ handleChunk, startChunk })
    // Close stream
    fileStream.end()
    // Finish up
    return new Promise((resolve, reject) => {
      // Check download result
      if (result && !result?.error) {
        console.log('[Downloader] File download finished and saved to disk successfully')
      } else {
        console.log('[Downloader] File failed to download or was cancelled')
        reject(null)
      }
      // Stream closed event, return config
      fileStream.on('finish', async () => {
        console.log('[Downloader] Stream finished: endChunk:', endChunk)
        // Create a checksum from completed file only
        let checksum
        const createChecksum = async () => {
          if (isResume && !hash) {
            checksum = await hashEntireFile(writePath)
            return { checksum }
          }
          checksum = hash.digest('hex')
          hash = null
          return { checksum }
        }
        const shouldCreateChecksum = signature && progress === 100
        if (shouldCreateChecksum) {
          updateProgressState(EProgressState.Validating) // Notify state change
          checksum = await createChecksum()
        } else checksum = {}
        // Send the config data to UI to save to storage
        resolve({
          ...result,
          ...checksum,
          savePath: writePath,
          endChunk,
          progress,
        })
      })
      // Error in stream
      fileStream.on('error', err => {
        console.log('[Downloader] File failed to save:', err)
        reject(null)
      })
    })
  }
  /**
   * Permanently removes a file from disk
   * @returns boolean
   */
  const onDelete = async () => {
    const path = savePath

    if (!path) {
      console.log('[Downloader] No path passed')
      return false
    }

    try {
      const fsp = require('fs/promises')
      // Remove double slashes
      const parsePath = path.replace(/\\\\/g, '\\')
      await fsp.unlink(parsePath)
      console.log('[Downloader] Deleted file from:', path)
      updateProgress(0)
      updateProgressState(EProgressState.None)
      return true
    } catch (err) {
      console.log(`[Downloader] Failed to delete file from ${path}: ${err}`)
      return false
    }
  }
  const onPause = async () => {
    // Record new state
    const newState = EProgressState.Idle
    updateProgressState(newState)
    // Inform frontend of state change
    return newState
  }
  /**
   * Start the download.
   */
  const onStart = async (isResume = false) => {
    try {
      console.log('[Downloader] Starting download...')
      updateProgressState(EProgressState.Downloading)
      // Download large file in chunks and return a checksum for validation
      const streamFileConfig = await writeStreamFile(isResume)
      // In-progress downloads skip validation
      if (progress < 100) {
        console.log('[Downloader] Halted downloading. Validation skipped.')
        updateProgressState(EProgressState.Idle)
        validation = EValidationState.None
        return { ...streamFileConfig, validation }
      }
      // Verify downloaded file hash for integrity
      const downloadedFileHash = streamFileConfig?.checksum
      const validated = downloadedFileHash === signature
      // Error validating, skip validation if no signature supplied
      if (signature && !validated) {
        updateProgressState(EProgressState.Errored)
        console.log('[Downloader] Failed to verify file integrity.', streamFileConfig)
        validation = EValidationState.Fail
        return { ...streamFileConfig, validation }
      }
      // Done
      updateProgressState(EProgressState.Completed)
      const integrityMsg = signature
        ? `File integrity verified [${validated}], ${downloadedFileHash} against ${signature}.`
        : 'File integrity verification skipped.'
      console.log(`[Downloader] Finished downloading. ${integrityMsg}`)
      validation = EValidationState.Success
      return { ...streamFileConfig, validation }
    } catch (err) {
      console.log('[Downloader] Failed writing file to disk, Error:', err)
      updateProgressState(EProgressState.Errored)
      // Close the file
      fileStream && fileStream.end()
      return false
    }
  }
  /**
   * Create a config for a previously downloaded file
   */
  const onImport = async () => {
    try {
      const importedFilePath = payload?.importedFilePath
      // Verify the known hash if one exists
      const fileHash = await hashEntireFile(importedFilePath)
      if (signature && fileHash !== signature)
        throw Error('Imported file checksum does not match config signature')
      // Create date string in the desired format
      const currentDate = new Date()
      const date = currentDate.toUTCString()
      // Calc file size
      const fileSize = createFileSize(importedFilePath)
      // Record in the model config
      const config = {
        id: modelCard.id,
        modified: date, // current date of import (today)
        size: fileSize, // calc in bytes
        checksum: fileHash, // create a hash from the selected file
        savePath: importedFilePath,
        endChunk: 1, // doesnt matter
        progress: 100,
        validation: EValidationState.Success,
        numTimesRun: 0,
        isFavorited: false,
      }
      return config
    } catch (err) {
      console.log('[Downloader] Error importing file', err)
      // @TODO Should rly display a toast message for user
      return null
    }
  }

  /**
   * Download a large file in chunks and save to disk as stream.
   * @param {any} props
   */
  const downloadChunkedFile = async props => {
    let error = false
    const { handleChunk, startChunk = 0 } = props
    const { size = 1000000000, modified } = await fetchTotalSize(downloadUrl)
    lastModified = modified

    // If resuming, check if file is out of date by comparing current file modified date to stored data's date.
    if (startChunk > 0) {
      console.log(
        `[Downloader] Chunk last modified: ${modified}, file last modified: ${lastModified}, size: ${size}`,
      )
      if (modified !== lastModified) {
        console.log(
          '[Downloader] File out of date, cancel the download, delete the file and restart download.',
        )
        return { error: true }
      }
    }

    const chunkSize = 1024 * 1024 * 10 // 10MB
    const numChunks = Math.ceil(size / chunkSize)
    for (let i = startChunk; i < numChunks; i++) {
      // Stop if state changes
      const isHaltState = state !== EProgressState.Downloading
      if (isHaltState) {
        console.log('[Downloader] Event: Download halted by user:', state)
        // If this is a cancel then we dont want to save in-progress info
        if (state === EProgressState.None) error = true
        break
      }

      // Download chunk
      const start = i * chunkSize
      const end = Math.min(start + chunkSize - 1, size)
      const response = await fetchChunk({
        url: downloadUrl,
        start,
        end,
      })

      // Handle errors
      if (!response) {
        console.log('[Downloader] Error: Failed to receive chunk.')
        error = true
        break
      }

      // Send chunks of a large file to Main Process for writing to disk
      await onDownloadProgress(response.data, handleChunk)
      endChunk = i + 1 // record last chunk downloaded

      // Increment progress after saving chunk
      const chunkProgress = (i + 1) / numChunks
      progress = Math.floor(chunkProgress * 100)
      updateProgress(progress)
    }

    if (error) return { error: true }
    return {
      modified,
      size,
    }
  }

  return {
    onImport,
    onStart,
    onPause,
    onDelete,
  }
}

module.exports = { EProgressState, downloader }
