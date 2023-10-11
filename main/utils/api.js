const listenApiEvents = child => {
  child.on('spawn', () => {
    console.log('[homebrew api] process started!')
  })
  child.on('exit', (code, signal) => {
    console.log('[homebrew api] exited with ' + `code ${code} and signal ${signal}`)
  })
  child.on('message', msg => {
    console.log('[homebrew api] message:', msg)
  })
  child.on('error', err => {
    console.log('[homebrew api] error:', err)
  })
  child.stdout.on('data', data => {
    console.log(`[homebrew api] stdout:\n${data}`)
  })
  child.stderr.on('data', data => {
    console.error(`[homebrew api] stderr:\n${data}`)
  })
}

module.exports = { listenApiEvents }
