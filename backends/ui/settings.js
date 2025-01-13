// Backend funcs
async function saveSettings() {
  const data = await window.pywebview.api.save_settings()
  return data
}

// Front-End funcs
async function mountPage() {
  const data = await window.pywebview.api.update_settings_page()
  // Parse page with data
  const llamaIndexEl = document.getElementById('llamaCloud')
  if (data.llamaIndexAPIKey) llamaIndexEl.value = `${data.llamaIndexAPIKey}`
  const sslEl = document.getElementById('ssl')
  if (data.ssl) sslEl.value = `${data.ssl}`
  const corsEl = document.getElementById('cors')
  if (data.cors) corsEl.value = `${data.cors}`
  const adminEl = document.getElementById('admin')
  if (data.adminWhitelist) adminEl.value = `${data.adminWhitelist}`
}

// Mount page
mountPage()
