async function mountPage() {
  const data = await window.pywebview.api.update_connect_page()
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
    `${data.obrew_studio_url}/?hostname=${data.local_url}&port=${data.port}`,
  )
  // Show QR-Code
  const qrcodeEl = document.getElementById('qrcode')
  const qrcodeImage = data.qr_data
  if (qrcodeImage) {
    qrcodeEl.setAttribute('data-attr', 'qrcode')
    qrcodeEl.setAttribute('alt', `qr code for ${data.remote_url}:${data.port}`)
    qrcodeEl.src = `data:image/png;base64,${qrcodeImage}`
  }
}

// Mount page
mountPage()
