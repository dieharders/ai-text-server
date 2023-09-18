/* eslint-disable @typescript-eslint/no-var-requires */

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
const fetchChunk = async ({ url, start, end }) =>
  await axios({
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
 * Send ipc command to front-end to update total progress
 * @param {function} send
 * @param {number} progress
 * @param {object} options
 * @returns
 */
const updateProgress = (event, progress, options) => {
  console.log('@@ [chunk progress]:', progress, options)
  event.sender.send('message', {
    eventId: 'download_progress',
    downloadId: options?.id,
    data: progress,
  })
  return progress
}

/**
 * Send ipc command to front-end to update state of progress
 * @param {function} send
 * @param {string} state
 * @param {object} options
 * @returns
 */
const updateProgressState = (event, state, options) => {
  console.log('@@ [updateProgressState]:', state, options)
  event.sender.send('message', {
    eventId: 'download_progress_state',
    downloadId: options?.id,
    data: state,
  })
  return state
}

/**
 * Read a file from disk and create a hash for comparison to a verified signature.
 * @param {string} filePath
 * @param {string} signature
 * @returns Promise<boolean>
 */
const hashFileSignature = async (filePath, signature) => {
  const crypto = require('crypto')
  const hash = crypto.createHash('sha256').setEncoding('hex')
  let fileHash = ''

  return new Promise((resolve, _reject) => {
    const fs = require('fs')

    fs.createReadStream(filePath)
      .pipe(hash)
      .on('finish', () => {
        fileHash = hash.read()
        console.log(`Filehash calculated: ${fileHash} | ${signature}.`)
        // Verified
        if (fileHash === signature) resolve(true)
        else resolve(false)
      })
  })
}

/**
 * Download a large file in chunks and save to disk as stream.
 * @param {any} props
 * @returns
 */
const downloadChunkedFile = async props => {
  const { url, updateProgress, updateProgressState, handleChunk } = props
  const { size = 1000000000, modified } = await fetchTotalSize(url) // find file size

  // @TODO check if file is out of date by comparing `modified` to stored model's data.
  console.log('@@ file last modified:', modified, 'size:', size)

  const chunkSize = 1024 * 1024 * 10 // 10MB
  const numChunks = Math.ceil(size / chunkSize)
  for (let i = 0; i < numChunks; i++) {
    const start = i * chunkSize
    const end = Math.min(start + chunkSize - 1, size)
    // Download chunk
    const response = await fetchChunk({
      url,
      start,
      end,
    })

    if (!response) {
      console.log('[Error]: Failed to save chunk.')
      return false
    }

    // Send chunks of a large file to Main Process for writing to disk
    updateProgressState(EProgressState.Downloading)
    await onDownloadProgress(response.data, handleChunk)
    // Increment progress after saving chunk
    const chunkProgress = (i + 1) / numChunks
    const progress = Math.floor(chunkProgress * 100)
    console.log('@@ [Downloading] progress:', progress)
    updateProgress(progress)
  }

  return {
    modified,
    size,
  }
}

module.exports = {
  downloadChunkedFile,
  EProgressState,
  updateProgress,
  updateProgressState,
  hashFileSignature,
}
