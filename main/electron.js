/* eslint-disable @typescript-eslint/no-var-requires */

// Modules
const { listenApiEvents } = require('./utils/api')
const { downloadChunkedFile } = require('./utils/downloader')
const { EProgressState } = require('./utils/downloader')

// Native Modules
const { spawn } = require('child_process')
const { join } = require('path')
const { format } = require('url')
const fs = require('fs')
const fsp = require('fs/promises')

// Packages
const { BrowserWindow, app, dialog, ipcMain } = require('electron')
const isDev = require('electron-is-dev')
const prepareNext = require('electron-next')

// https://www.freecodecamp.org/news/node-js-child-processes-everything-you-need-to-know-e69498fe970a/
const apiPath = isDev ? './backends/main.py' : './includes/api/main-x86_64.py'

let universalAPI
let mainWindow

// Create the browser window
const createWindow = () => {
  mainWindow = new BrowserWindow({
    title: 'HomebrewAi',
    width: isDev ? 1280 : 960,
    height: 640,
    // backgroundColor: '#ffffff',
    // icon: `file://${__dirname}/dist/assets/logo.png`,
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: join(__dirname, 'preload.js'),
      enableRemoteModule: false,
    },
  })
}

// Start the frontend
const start = async () => {
  // Start the backend process for the universal api
  universalAPI = spawn('python', [apiPath])
  // Listen to universal api events
  listenApiEvents(universalAPI)
  // Prepare the renderer for frontend
  await prepareNext('./renderer')
  // Start frontend browser window
  createWindow()
}

app.on('ready', async () => {
  await start()

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

// Window closed event
app.on('closed', () => {
  mainWindow = null
})

// Quit the app once all windows are closed
app.on('window-all-closed', () => {
  // On MacOs, users expect the app to stay open when the window is closed
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', async () => {
  // macOS specific close process
  if (mainWindow === null) await start()
})

// listen the channel `message` and resend the received message to the renderer process
ipcMain.on('message', (event, message) => {
  event.sender.send('message', message)
})

// listen for an api request, then invoke it and send back result
ipcMain.handle('api', async (event, eventName, options) => {
  switch (eventName) {
    case 'showConfirmDialog':
      return dialog.showMessageBoxSync(mainWindow, options)
    case 'showOpenDialog':
      return dialog.showOpenDialog(options)
    case 'getPath':
      return app.getPath(options)
    case 'getAppPath':
      return app.getAppPath()
    case 'delete_file':
      if (!options?.path) return false
      try {
        await fsp.unlink(options.path)
        console.log('@@ [Electron] Deleted file from:', options.path)
        return true
      } catch (err) {
        console.log(`@@ [Electron] Failed to delete file from ${options.path}: ${err}`)
        return false
      }
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
        console.log('@@ [Electron] Created write stream:', writePath, 'url:', options.url)
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
          console.log('@@ [Electron] File downloaded to path')
          fileStream.end()
          updateProgressState(EProgressState.Completed)
          // @TODO Call a func to verify sha256 hash of file then set 'Completed'
        }
        return result
      } catch (err) {
        console.log('@@ [Electron] Failed writing file to disk', err)
        return false
      }
    default:
      return
  }
})
