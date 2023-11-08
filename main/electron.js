/* eslint-disable @typescript-eslint/no-var-requires */

// Modules
const { join } = require('path')
const constants = require('../shared/constants.json')
const { listenApiEvents } = require('./utils/api')
const { downloader } = require('./utils/downloader')

// Native Modules
const { spawn } = require('child_process')
const { format } = require('url')

// Packages
const { BrowserWindow, app, dialog, ipcMain, shell } = require('electron')
const isDev = require('electron-is-dev')
const prepareNext = require('electron-next')

let universalAPI
let mainWindow

// Create the browser window
const createWindow = (devmode = false) => {
  mainWindow = new BrowserWindow({
    title: 'HomebrewAi',
    width: isDev ? 1280 : 960,
    height: 640,
    // backgroundColor: '#ffffff',
    // icon: `file://${__dirname}/dist/assets/logo.png`,
    autoHideMenuBar: true,
    webPreferences: {
      devTools: devmode,
      nodeIntegration: false,
      contextIsolation: true,
      preload: join(__dirname, 'preload.js'),
      enableRemoteModule: false,
    },
  })
}

// Start the frontend
const start = async () => {
  // Start the backend process for the homebrew api
  // https://www.freecodecamp.org/news/node-js-child-processes-everything-you-need-to-know-e69498fe970a/
  const closeAfterExec = '/c'
  const pathToProcess = join(__dirname, '..', 'backends')

  universalAPI = isDev
    ? spawn('python', ['./backends/main.py'])
    : spawn('cmd', [closeAfterExec, 'main.exe'], { cwd: pathToProcess })
  // Listen to homebrew api events
  listenApiEvents(universalAPI)
  // Prepare the renderer for frontend
  await prepareNext('./renderer')
  // Start frontend browser window
  createWindow(isDev)
  // Open dev tools if in dev env
  if (isDev) mainWindow.webContents.openDevTools()
  // Hide menu bar
  // if (!isDev) {
  //   mainWindow.removeMenu() // Only Windows and Linux
  // }
  // Configure opening new windows from links
  mainWindow.webContents.setWindowOpenHandler(async ({ url }) => {
    // open url in a browser and prevent default
    try {
      await shell.openExternal(url)
    } catch (err) {
      console.log('[Electron] Failed to open external website')
    }
    if (url.startsWith('about_blank')) {
      return { action: 'allow' }
    }
    return { action: 'deny' }
  })
  // Window just closed event
  mainWindow.on('close', async () => {
    // Tell homebrew to shutdown all external services
    try {
      await fetch({
        url: `http://0.0.0.0:${constants.PORT_HOMEBREW_API}/v1/services/shutdown`,
        method: 'GET',
      })
    } catch (err) {
      console.log('[App] Failed to shutdown services:', err.code)
    }
  })
  // Window closed event
  mainWindow.on('closed', () => {
    console.log('[App] Main window closed, killing homebrew API process')
    // Kill all child processes here
    // Look into npm `tree-kill` to kill all child sub-processes too: https://stackoverflow.com/questions/18694684/spawn-and-kill-a-process-in-node-js
    // universalAPI.stdin.pause()
    // universalAPI.kill()
    spawn('cmd', [`/C TASKKILL /F /PID ${universalAPI.pid} /T`])
    universalAPI = null
    // Dereference the window object, usually you would store windows
    // in an array if your app supports multi windows, this is the time
    // when you should delete the corresponding element.
    mainWindow = null
    // Kill this main script
    console.log('[App] Ending main process')
    process.exit()
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
  await start()
  // app.getGPUInfo() // Get info
  console.log('[App] Ready')
})

// Quit the app once all windows are closed
app.on('window-all-closed', () => {
  console.log('[App] All windows closed')
  // On MacOs, users expect the app to stay open in bg when the window is closed
  if (process.platform !== 'darwin') {
    console.log('[App] Quitting app')
    app.quit()
  }
})

// On macOS it's common to re-create a window in the app when the
// dock icon is clicked and there are no other windows open.
app.on('activate', async () => {
  if (mainWindow === null) {
    console.log('[App] Activate')
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
  const canWritePath = () => {
    // Check we can write to path
    const fs = require('fs')
    const exists = fs.existsSync(filePath)
    if (exists) {
      try {
        fs.accessSync(filePath, fs.constants.W_OK | fs.constants.R_OK)
        return true
      } catch (e) {
        console.log('[Electron] Error: Cannot access directory')
        return false
      }
    } else {
      try {
        fs.mkdirSync(filePath)
        return true
      } catch (e) {
        if (e.code == 'EACCESS') {
          console.log('[Electron] Error: Cannot create directory, access denied.')
        } else {
          console.log(`[Electron] Error: ${e.code}`)
        }
        return false
      }
    }
  }
  // Create downloader instance
  const createDownloaderInstance = () => {
    if (dlService) return
    dlService = downloader({ config, modelCard, event, filePath })
    downloaders[id] = dlService
    console.log('[Electron] New downloader created.')
  }

  // Handle api events
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
      try {
        const success = await dlService.onDelete()
        if (dlService) delete downloaders[id]
        return success
      } catch (err) {
        console.log('[Electron] Error:', err)
        return false
      }
    }
    case 'pause_download':
      return dlService.onPause()
    // Initiate the previous download
    case 'resume_download':
      if (!canWritePath()) return
      createDownloaderInstance()
      return dlService.onStart(true)
    // Start service and return a config
    case 'start_download':
      if (!canWritePath()) return
      createDownloaderInstance()
      return dlService.onStart()
    default:
      return
  }
})
