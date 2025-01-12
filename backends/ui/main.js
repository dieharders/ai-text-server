// Backend funcs
function startServer() {
  window.pywebview.api.start_server()
}
function shutdownServer() {
  window.pywebview.api.shutdown_server()
}

// Front-End funcs
async function mountPage() {
  const data = await window.pywebview.api.update_entry_page()
  const buttonEl = document.getElementById('webui')
  buttonEl.setAttribute(
    'href',
    `${data.obrew_studio_url}/?hostname=${data.local_url}&port=${data.port}`,
  )
}

// Mount page
mountPage()
