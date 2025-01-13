// Backend funcs
async function startServer() {
  const config = {} // get input values from form
  await window.pywebview.api.start_server_process(config)
  // Nav to Obrew Studio WebUI
  window.location = `${window.frontend.data.obrew_studio_url}/?hostname=${window.frontend.data.local_url}&port=${window.frontend.data.port}`
}
async function shutdownServer() {
  await window.pywebview.api.shutdown_server()
}

// Front-End funcs
async function mountPage() {
  const data = await window.pywebview.api.update_entry_page()
  window.frontend.data = data
  // Parse page with data
  const hostEl = document.getElementById('qr_link')
  hostEl.innerHTML = `${data.remote_url}:${data.port}`
  const docsLinkEl = document.querySelector('.docs-link')
  const docsLink = `${data.local_url}:${data.port}/docs`
  docsLinkEl.innerHTML = docsLink
  docsLinkEl.setAttribute('href', docsLink)
  // Show QR-Code
  const qrcodeEl = document.getElementById('qrcode')
  const qrcodeImage = data.qr_data
  if (qrcodeImage) {
    qrcodeEl.setAttribute('data-attr', 'qrcode')
    qrcodeEl.setAttribute('alt', `qr code for ${data.remote_url}:${data.port}`)
    qrcodeEl.src = `data:image/png;base64,${qrcodeImage}`
  }
}
function toggleAdvanced() {
  const containerEl = document.getElementById('advContainer')
  const isOpen = containerEl.getAttribute('data-attr') === 'open'

  if (isOpen) containerEl.setAttribute('data-attr', 'closed')
  else containerEl.setAttribute('data-attr', 'open')
}

// Mount page
mountPage()
