// Backend funcs
async function startServer() {
  const form = document.querySelector('form')
  // Get form data
  const formData = new FormData(form)
  const config = Object.fromEntries(formData.entries())
  config.port = parseInt(config.port)
  await window.pywebview.api.start_server_process(config)
  // Nav to Obrew Studio WebUI
  // The params help front-end know what server to connect to
  window.location = `${window.frontend.data.obrew_studio_url}/?hostname=${window.frontend.data.local_url}&port=${window.frontend.data.port}`
}
async function shutdownServer() {
  await window.pywebview.api.shutdown_server()
}

// Front-End funcs
async function getPageData() {
  const port = document.getElementById('port').value
  const data = await window.pywebview.api.update_entry_page(port)
  window.frontend.data = data
  return data
}
function updateQRCode(data) {
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
async function mountPage() {
  // Get data from input
  const data = await getPageData()
  if (!data) return
  // Parse page with data
  updateQRCode(data)
  const webuiEl = document.getElementById('webui')
  webuiEl.value = data.obrew_studio_url
}
function hideAdvanced() {
  const containerEl = document.getElementById('advContainer')
  containerEl.setAttribute('data-attr', 'closed')
}
async function toggleAdvanced() {
  const containerEl = document.getElementById('advContainer')
  const isOpen = containerEl.getAttribute('data-attr') === 'open'

  if (isOpen) containerEl.setAttribute('data-attr', 'closed')
  else {
    containerEl.setAttribute('data-attr', 'open')
    // Update data
    const data = await getPageData()
    updateQRCode(data)
  }
}

// Global Vars
window.frontend.data = {}
// Listeners
document.querySelector('.formOptions').addEventListener('change', hideAdvanced)
// Mount page
mountPage()
