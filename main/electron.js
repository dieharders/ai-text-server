/* eslint-disable @typescript-eslint/no-var-requires */

// Modules
const { downloadChunkedFile } = require('./utils/downloader')

// Native Modules
const { join } = require('path')
const { format } = require('url')
const fs = require('fs')

// Packages
const { BrowserWindow, app, dialog, ipcMain } = require('electron')
const isDev = require('electron-is-dev')
const prepareNext = require('electron-next')

// Prepare the renderer once the app is ready
app.on('ready', async () => {
  await prepareNext('./renderer')

  const mainWindow = new BrowserWindow({
    title: 'HomebrewAi',
    width: isDev ? 1280 : 960,
    height: 640,
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: true,
      preload: join(__dirname, 'preload.js'),
      // enableRemoteModule: true,
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
app.on('window-all-closed', app.quit)

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
          updateProgressState('Completed')
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
