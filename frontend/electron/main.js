const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

let mainWindow = null
let pythonServer = null

function spawnPythonServer() {
  const port = 9000
  const backendDir = path.join(__dirname, '../../backend')
  const proc = spawn('python', ['-m', 'server'], {
    cwd: backendDir,
    env: { ...process.env, MAHJONG_PORT: String(port) },
    stdio: 'pipe',
  })

  proc.stdout?.on('data', (data) => {
    console.log(`[server] ${data.toString().trim()}`)
  })

  proc.stderr?.on('data', (data) => {
    console.error(`[server] ${data.toString().trim()}`)
  })

  proc.on('error', (err) => {
    console.error('Failed to start Python server:', err)
  })

  return proc
}

async function waitForHealth(port, retries = 30, delayMs = 500) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/health`)
      if (response.ok) return true
    } catch {
      // Server not ready yet
    }
    await new Promise(resolve => setTimeout(resolve, delayMs))
  }
  return false
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 720,
    minWidth: 1280,
    minHeight: 720,
    title: '台灣16張麻將',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (process.env.VITE_DEV_SERVER_URL) {
    await mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL)
  } else {
    await mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.whenReady().then(async () => {
  pythonServer = spawnPythonServer()
  const healthy = await waitForHealth(9000)
  if (!healthy) {
    console.error('Python server failed to start')
  }
  await createWindow()
})

app.on('window-all-closed', () => {
  if (pythonServer) {
    pythonServer.kill()
    pythonServer = null
  }
  app.quit()
})

app.on('before-quit', () => {
  if (pythonServer) {
    pythonServer.kill()
    pythonServer = null
  }
})
