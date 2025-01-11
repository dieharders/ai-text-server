// WebView funcs
function updateConnectPage() {
  const data = window.pywebview.api.update_connect_page()
  return data
}
function openBrowser() {
  window.pywebview.api.open_browser()
}
function toggleFullScreen() {
  try {
    window.pywebview.api.toggle_fullscreen(window)
  } catch (e) {
    console.log(`Fullscreen err: ${e}`)
  }
}
function startServer() {
  window.pywebview.api.start_server()
}
function shutdownServer() {
  window.pywebview.api.shutdown_server()
}

// Function to get URL parameter value by name
function getUrlParameter(name) {
  const urlParams = new URLSearchParams(window.location.search)
  return urlParams.get(name)
}

// Connect button
const hostValue = getUrlParameter('hostname')
const portValue = getUrlParameter('port')
const btn = document.querySelector('.connect-button')
if (hostValue && portValue && btn) {
  // Change value of link to point to remote url (since this is prob someone not on host machine using QR code)
  btn.href = `https://studio.openbrewai.com/?hostname=${hostValue}&port=${portValue}`
}

// Listen for fullscreen toggle keypress
document.addEventListener('keydown', event => {
  if (event.key === 'F11') toggleFullScreen()
})

// Listen for pywebview api to be ready
window.addEventListener('pywebviewready', async () => {
  const data = await updateConnectPage()
  // Parse page with data
  const hostEl = document.getElementById('qr_link')
  hostEl.innerHTML = `${data.remote_url}:${data.port}`
  const docsLinkEl = document.querySelector('.docs-link')
  const docsLink = `${data.local_url}:${data.port}/docs`
  docsLinkEl.innerHTML = docsLink
  docsLinkEl.setAttribute('href', docsLink)
  const connectBtnEl = document.querySelector('.connect-button')
  connectBtnEl.setAttribute(
    'href',
    `https://studio.openbrewai.com/?hostname=${data.local_url}&port=${data.port}`,
  )
  // Show QR-Code
  const qrcodeEl = document.getElementById('qrcode')
  const qrcodeImage = data.qr_data
  if (qrcodeImage) {
    qrcodeEl.setAttribute('data-attr', 'qrcode')
    qrcodeEl.setAttribute('alt', `qr code for ${data.remote_url}:${data.port}`)
    qrcodeEl.src = `data:image/png;base64,${qrcodeImage}`
  }
})
