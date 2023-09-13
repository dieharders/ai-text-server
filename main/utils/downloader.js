/* eslint-disable @typescript-eslint/no-var-requires */

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

/**
 * Save chunk to file stream.
 * @param string path
 * @param ArrayBuffer chunk
 * @returns
 */
const onDownloadProgress = async (path, chunk, handleChunk) => {
  // Save chunks here
  const vec8 = new Uint8Array(chunk)
  const binaryChunk = Array.from(vec8)
  if (!binaryChunk) throw Error('Error reading chunk!')
  // @TODO Save chunk
  await handleChunk(binaryChunk)
  return binaryChunk
}

/**
 * Download a large file in chunks and save to disk as stream.
 * @param {*} options
 * @returns
 */
const downloadChunkedFile = async options => {
  const { url, path, updateProgress, updateProgressState, handleChunk } = options
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
    console.log('@@ response', response.data)
    if (!response) {
      console.log('[Error]: Failed to save chunk.')
      return false
    }
    // Save chunk - Send chunks of a large file to Main Process for writing to disk
    updateProgressState('Saving') // EProgressState.Saving
    await onDownloadProgress(path, response.data, handleChunk)
    // Increment progress after saving chunk
    const chunkProgress = (i + 1) / numChunks
    const progress = Math.floor(chunkProgress * 100)
    console.log('@@ [Downloading] progress:', progress)
    updateProgress(progress)
  }
}

module.exports = { downloadChunkedFile }
