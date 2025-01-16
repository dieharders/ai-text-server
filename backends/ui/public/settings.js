// Backend funcs
async function saveSettings() {
  const form = document.querySelector('form')
  // Disable button
  const btnEl = document.getElementById('saveChanges')
  if (btnEl) btnEl.disabled = true
  // Get form data
  const formData = new FormData(form)
  // Write checkbox data
  const checkboxes = document.querySelectorAll('input[type="checkbox"]')
  const checkData = {}
  checkboxes.forEach(v => {
    if (v.checked) checkData[v.name] = 'true'
    else checkData[v.name] = 'false'
  })
  // Convert to a plain JavaScript object
  const formDataObject = Object.fromEntries(formData.entries())
  await window.pywebview.api.save_settings({ ...formDataObject, ...checkData })
  return
}

// Front-End funcs
async function mountPage() {
  const data = await window.pywebview.api.update_settings_page()
  // Parse page with data
  const llamaIndexEl = document.getElementById('llamaCloud')
  if (data.llamaIndexAPIKey) llamaIndexEl.value = `${data.llamaIndexAPIKey}`
  const sslEl = document.getElementById('ssl')
  if (data.ssl) sslEl.checked = true
  else sslEl.checked = false
  const corsEl = document.getElementById('cors')
  if (data.cors) corsEl.value = `${data.cors}`
  const adminEl = document.getElementById('admin')
  if (data.adminWhitelist) adminEl.value = `${data.adminWhitelist}`
  return
}

// Mount page
mountPage()
// Listeners
document.querySelector('.formOptions').addEventListener('change', () => {
  const btnEl = document.getElementById('saveChanges')
  if (btnEl) btnEl.disabled = false
})
