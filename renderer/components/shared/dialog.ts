interface IDialogOpenProps {
  isDirMode: boolean
  options?: {
    title?: string
    buttonLabel?: string
    filterExtensions?: string[]
    filterName?: string
  }
}
const dialogOpen = async ({ isDirMode, options }: IDialogOpenProps): Promise<string | null> => {
  const desktopDir = async (): Promise<string> => {
    const path = await window.electron.api('getPath', 'desktop')
    return path
  }

  // Open a native OS file explorer to choose a save path
  const dialogOpen = async () => {
    const mode = isDirMode ? 'openDirectory' : 'openFile'
    const cwd = await desktopDir()
    const properties = {
      title: options?.title || 'Choose',
      defaultPath: cwd,
      properties: [mode],
      buttonLabel: options?.buttonLabel || 'Choose',
      filters: [
        {
          extensions: options?.filterExtensions || [],
          name: options?.filterName || '*',
        },
      ],
    }
    return window.electron.api('showOpenDialog', properties)
  }

  const selected = await dialogOpen()
  console.log('[UI] User opened dialogue box', selected)

  if (selected.canceled) {
    console.log('[UI] User cancelled the selection.')
    return null
  } else if (selected.filePaths.length > 1) {
    console.log('[UI] Error: user selected multiple files.')
    return null
  } else {
    console.log('[UI] User selected a single file or folder:', selected.filePaths[0])
    return selected.filePaths[0]
  }
}

export { dialogOpen }
