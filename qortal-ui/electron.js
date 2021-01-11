const { app, BrowserWindow, ipcMain, Menu, Notification, Tray, nativeImage } = require('electron')
const { autoUpdater } = require('electron-updater')
const path = require('path')

// THOUGHTS: Make this APP more modularize and platform agnostic...

process.env['APP_PATH'] = app.getAppPath()
const server = require('./server.js')

Menu.setApplicationMenu(null)

let myWindow = null

// TODO: Move the Tray function into another file (maybe Tray.js) -_-
// const tray = new Tray(nativeImage.createEmpty());

const APP_ICON = path.join(__dirname, 'img', 'icons');

const iconPath = () => {
    return APP_ICON + (process.platform === 'win32' ? '/ico/256x256.ico' : '/png/256x256.png');
};

function createWindow() {

    myWindow = new BrowserWindow({
        backgroundColor: '#eee',
        width: 800,
        height: 640,
        minWidth: 700,
        minHeight: 640,
        icon: iconPath(),
        title: "Qortal",
        autoHideMenuBar: true,
        webPreferences: {
            nodeIntegration: false,
            partition: 'persist:webviewsession',
            enableRemoteModule: false,
            sandbox: true
        },

    })

    myWindow.loadURL('http://localhost:12388/app/wallet')

    myWindow.on('closed', function () {

        myWindow = null
    })
}

const createTray = () => {

    let myTray = new Tray(path.join(__dirname, 'img', 'icons', 'png', '32x32.png'))
    const contextMenu = Menu.buildFromTemplate([
        {
            label: "Quit", click() {
                myTray.destroy();
                app.quit();
            },
        }
    ])
    myTray.setTitle("QORTAL UI")
    myTray.setToolTip("QORTAL UI")
    myTray.setContextMenu(contextMenu)
}


const isLock = app.requestSingleInstanceLock()

if (!isLock) {

    app.quit()
} else {

    app.on('second-instance', (event, cmd, dir) => {

        if (myWindow) {

            if (myWindow.isMinimized()) myWindow.restore()
            myWindow.focus()
        }
    })

    app.allowRendererProcessReuse = true

    app.on('ready', () => {

        createWindow()
        createTray()

        if (process.platform === 'win32') {

            app.setAppUserModelId("org.qortal.QortalUi");
        }
        autoUpdater.checkForUpdatesAndNotify()
    })

    app.on('window-all-closed', function () {

        if (process.platform !== 'darwin') {
            app.quit()
        }
    })

    app.on('activate', function () {

        if (myWindow === null) {

            createWindow()
            createTray()
        }
    })

    ipcMain.on('app_version', (event, args) => {

        myWindow.webContents.send("app_version", { version: app.getVersion() });
    })


    autoUpdater.on('update-available', () => {

        const n = new Notification({
            title: 'Update Available!',
            body: 'It will be downloaded in the background and installed on next restart'
        })
        n.show()
    })

    autoUpdater.on('error', (err) => {

        const n = new Notification({
            title: 'Error while Updating...',
            body: err
        })
        n.show()
    })

    autoUpdater.on('update-downloaded', () => {

        const n = new Notification({
            title: 'Update Downloaded!',
            body: 'Restarting to Update'
        })
        n.show()

        // Restart App
        autoUpdater.quitAndInstall();
    })
}
