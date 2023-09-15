const listenApiEvents = child => {
  child.on('spawn', () => {
    console.log('[universal api] process started!')
  })
  child.on('exit', (code, signal) => {
    console.log('[universal api] exited with ' + `code ${code} and signal ${signal}`)
  })
  child.on('message', msg => {
    console.log('[universal api] message:', msg)
  })
  child.on('error', err => {
    console.log('[universal api] error:', err)
  })
  child.stdout.on('data', data => {
    console.log(`[universal api] stdout:\n${data}`)
  })
  child.stderr.on('data', data => {
    console.error(`[universal api] stderr:\n${data}`)
  })
}

module.exports = { listenApiEvents }
