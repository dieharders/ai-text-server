/* eslint-disable @typescript-eslint/no-var-requires */

// Modules
const { downloadChunkedFile } = require('./utils/downloader')
const axios = require('axios')

// Native Modules
const { join } = require('path')
const { format } = require('url')
const fs = require('fs')
// const fs = require('fs/promises')

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
        const updateProgress = progress => {
          // @TODO Send ipc command to front-end to update total progress
          console.log('@@ chunk progress:', progress)
          event.sender.send('message', {
            eventId: 'download_progress',
            downloadId: options.id,
            data: progress,
          })
          return progress
        }
        const updateProgressState = state => {
          // @TODO Send ipc command to front-end to update state of progress
          console.log('@@ updateProgressState', state)
          event.sender.send('message', {
            eventId: 'download_progress_state',
            downloadId: options.id,
            data: state,
          })
          return state
        }
        // Save file
        const writePath = join(options.path, options.name)
        console.log('@@ write path:', writePath, 'url:', options.url)
        const handler = async res => {
          console.log('@@ response data:')
          const fileStream = fs.createWriteStream(writePath)
          // @TODO Implement strategy to save chunks to file
          // fs.openSync(path, 'w')
          // fs.write(fd, chunk, 0, chunk.length, null, (err, written) => {})
          // fs.closeSync(fd)

          res.pipe(fileStream).on('finish', () => {
            console.log('@@ File downloaded to path')
            updateProgressState('Completed')
            // @TODO Call a func to verify sha256 hash of file then set 'Completed'
          })
        }
        // Download file
        const response = await axios({
          url: options.url,
          method: 'GET',
          responseType: 'stream',
          onDownloadProgress: progressEvent => {
            const total = progressEvent.total || 1000000000
            const percentCompleted = Math.round((progressEvent.loaded * 100) / total)
            // Handle file progress
            updateProgress(percentCompleted)
          },
        })
        handler(response.data)

        // downloadChunkedFile({
        //   url: options.url,
        //   path: writePath,
        //   updateProgress,
        //   updateProgressState,
        //   handleChunk: handler,
        // })

        return true
      } catch (err) {
        console.log('@@ [Error] Writing file to disk', err)
        return false
      }
    default:
      return
  }
})
