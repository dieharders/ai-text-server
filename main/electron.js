/* eslint-disable @typescript-eslint/no-var-requires */

// Modules
const { downloadChunkedFile } = require('./utils/downloader')
const { EProgressState } = require('./utils/downloader')

// Native Modules
const { spawn } = require('child_process')
const { join } = require('path')
const { format } = require('url')
const fs = require('fs')

// Packages
const { BrowserWindow, app, dialog, ipcMain } = require('electron')
const isDev = require('electron-is-dev')
const prepareNext = require('electron-next')

// Start the backend process for the universal api
// https://www.freecodecamp.org/news/node-js-child-processes-everything-you-need-to-know-e69498fe970a/
const apiPath = isDev ? './backends/main.py' : './includes/api/main-x86_64.py'
const universalAPI = spawn('python', [apiPath])

// Prepare the renderer once the app is ready
app.on('ready', async () => {
  // Start frontend
  await prepareNext('./renderer')

  const mainWindow = new BrowserWindow({
    title: 'HomebrewAi',
    width: isDev ? 1280 : 960,
    height: 640,
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: join(__dirname, 'preload.js'),
      enableRemoteModule: false,
    },
  })

  // Open dev tools if in dev env
  if (isDev) mainWindow.webContents.openDevTools()

  const url = isDev
    ? 'http://localhost:8000'
    : format({
        pathname: join(__dirname, '../renderer/out/index.html'),
        protocol: 'file:',
        slashes: true,
      })

  mainWindow.loadURL(url)
})

// Quit the app once all windows are closed
// @TODO Add another logic for macOS since it doesnt close when window closes.
app.on('window-all-closed', app.quit)

// Listen to universal api events
universalAPI.on('spawn', () => {
  console.log('[universal api] started!')
})
universalAPI.on('exit', (code, signal) => {
  console.log('[universal api] exited with ' + `code ${code} and signal ${signal}`)
})
universalAPI.on('message', msg => {
  console.log('[universal api] message:', msg)
})
universalAPI.on('error', err => {
  console.log('[universal api] error:', err)
})
universalAPI.stdout.on('data', data => {
  console.log(`[universal api] stdout:\n${data}`)
})
universalAPI.stderr.on('data', data => {
  console.error(`[universal api] stderr:\n${data}`)
})

// listen the channel `message` and resend the received message to the renderer process
ipcMain.on('message', (event, message) => {
  event.sender.send('message', message)
})

// listen for an api request, then invoke it and send back result
ipcMain.handle('api', async (event, eventName, options) => {
  switch (eventName) {
    case 'showOpenDialog':
      return dialog.showOpenDialog(options)
    case 'getPath':
      return app.getPath(options)
    case 'getAppPath':
      return app.getAppPath()
    // @TODO Implement
    case 'delete_file':
      if (!options?.path) return false
      return true
    // @TODO Implement
    case 'pause_download':
      return
    // @TODO Implement
    case 'resume_download':
      return
    case 'download_chunked_file':
      // @TODO Check that file does not exist and that folder exists and can be written to (priveledges)
      try {
        /**
         * Send ipc command to front-end to update total progress
         * @param {number} progress
         * @returns
         */
        const updateProgress = progress => {
          console.log('@@ [chunk progress]:', progress)
          event.sender.send('message', {
            eventId: 'download_progress',
            downloadId: options.id,
            data: progress,
          })
          return progress
        }
        /**
         * Send ipc command to front-end to update state of progress
         * @param {string} state
         * @returns
         */
        const updateProgressState = state => {
          console.log('@@ [updateProgressState]:', state)
          event.sender.send('message', {
            eventId: 'download_progress_state',
            downloadId: options.id,
            data: state,
          })
          return state
        }
        // Create file stream
        const writePath = join(options.path, options.name)
        console.log('@@ write path:', writePath, 'url:', options.url)
        const fileStream = fs.createWriteStream(writePath)
        /**
         * Save chunk to stream
         * @param {Uint8Array} chunk
         * @returns
         */
        const handleChunk = async chunk => {
          console.log('@@ [saving chunk...]')
          return fileStream.write(chunk)
        }
        // Download file
        const result = await downloadChunkedFile({
          url: options.url,
          updateProgress,
          updateProgressState,
          handleChunk,
        })

        if (result) {
          console.log('@@ File downloaded to path')
          fileStream.end()
          updateProgressState(EProgressState.Completed)
          // @TODO Call a func to verify sha256 hash of file then set 'Completed'
        }
        return result
      } catch (err) {
        console.log('@@ [Error] Writing file to disk', err)
        return false
      }
    default:
      return
  }
})
