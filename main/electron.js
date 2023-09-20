/* eslint-disable @typescript-eslint/no-var-requires */

// Modules
const { listenApiEvents } = require('./utils/api')
const { downloader } = require('./utils/downloader')

// Native Modules
const { spawn } = require('child_process')
const { join } = require('path')
const { format } = require('url')

// Packages
const { BrowserWindow, app, dialog, ipcMain, shell } = require('electron')
const isDev = require('electron-is-dev')
const prepareNext = require('electron-next')

// https://www.freecodecamp.org/news/node-js-child-processes-everything-you-need-to-know-e69498fe970a/
const apiProgramPath = isDev ? './backends/main.py' : './includes/api/main-x86_64.py'

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
  universalAPI = spawn('python', [apiProgramPath])
  // Listen to universal api events
  listenApiEvents(universalAPI)
  // Prepare the renderer for frontend
  await prepareNext('./renderer')
  // Start frontend browser window
  createWindow()
  // Open dev tools if in dev env
  if (isDev) mainWindow.webContents.openDevTools()
  // Configure opening new windows from links
  mainWindow.webContents.setWindowOpenHandler(async ({ url }) => {
    // open url in a browser and prevent default
    try {
      await shell.openExternal(url)
    } catch (err) {
      console.log('@@ [Electron] Failed to open external website')
    }
    if (url.startsWith('about_blank')) {
      return { action: 'allow' }
    }
    return { action: 'deny' }
  })
  // Window closed event
  mainWindow.on('closed', () => {
    console.log('@@ [App] closed')
    // Dereference the window object, usually you would store windows
    // in an array if your app supports multi windows, this is the time
    // when you should delete the corresponding element.
    mainWindow = null
  })
  // Load the html for frontend
  const url = isDev
    ? 'http://localhost:8000'
    : format({
        pathname: join(__dirname, '../renderer/out/index.html'),
        protocol: 'file:',
        slashes: true,
      })

  mainWindow.loadURL(url)
}

// Normal start process
app.on('ready', async () => {
  console.log('@@ [App] ready')
  await start()
})

// Quit the app once all windows are closed
app.on('window-all-closed', () => {
  console.log('@@ [App] all windows closed')
  // On MacOs, users expect the app to stay open in bg when the window is closed
  if (process.platform !== 'darwin') {
    console.log('@@ [App] quit')
    app.quit()
  }
})

// On macOS it's common to re-create a window in the app when the
// dock icon is clicked and there are no other windows open.
app.on('activate', async () => {
  if (mainWindow === null) {
    console.log('@@ [App] activate')
    await start()
  }
})

// listen the channel `message` and resend the received message to the renderer process
ipcMain.on('message', (event, message) => {
  event.sender.send('message', message)
})

// Listen for an api request, then invoke it and send back result
let downloaders = {}
ipcMain.handle('api', async (event, eventName, options) => {
  // Create an instance of a service to handle dl operations (if none exist)
  // This only concerns endpoints using `dlService`.
  const filePath = options?.filePath
  const config = options?.config
  const modelCard = options?.modelCard
  const id = modelCard?.id
  let dlService = downloaders[id]
  if (!dlService) {
    dlService = downloader({ config, modelCard, event, filePath })
    downloaders[id] = dlService
    console.log('@@ [Electron] New downloader created.')
  }

  switch (eventName) {
    case 'showConfirmDialog':
      return dialog.showMessageBoxSync(mainWindow, options)
    case 'showOpenDialog':
      return dialog.showOpenDialog(options)
    case 'getPath':
      return app.getPath(options)
    case 'getAppPath':
      return app.getAppPath()
    case 'delete_file': {
      if (dlService) delete downloaders[id]
      return dlService.onDelete()
    }
    case 'pause_download':
      return dlService.onPause()
    case 'cancel_download': {
      const result = await dlService.onCancel()
      if (dlService) delete downloaders[id]
      return result
    }
    case 'resume_download':
      return dlService.onStart(true)
    // Start service and return a config
    case 'start_download':
      return dlService.onStart()
    default:
      return
  }
})
