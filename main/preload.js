/* eslint-disable @typescript-eslint/no-var-requires */

const { ipcRenderer, contextBridge } = require('electron')

/**
 * This allows the renderer (frontend) to communicate with main process (electron/node).
 * You can also create and provide an api layer for the frontend and main process.
 * Anything exposed here is duplicated and attached to window object.
 * No promises, funcs can be directly attached.
 */
contextBridge.exposeInMainWorld('electron', {
  // Communicate between renderer and main process
  message: {
    send: payload => ipcRenderer.send('message', payload),
    on: handler => ipcRenderer.on('message', handler),
    off: handler => ipcRenderer.off('message', handler),
  },
  // Call an electron api command
  api: async (methodName, options) => ipcRenderer.invoke('api', methodName, options),
})
