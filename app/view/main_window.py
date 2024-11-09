from PyQt5.QtCore import QUrl, QSize, QThread
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (NavigationAvatarWidget, NavigationItemPosition, MessageBox, FluentWindow,
                            SplashScreen)

from ..config import GITHUB_REPO_URL, ASSETS_PATH
from ..common.config import cfg
from ..core.thread.version_manager_thread import VersionManager
from .subtitle_style_interface import SubtitleStyleInterface
from .batch_process_interface import BatchProcessInterface
from .home_interface import HomeInterface
from .setting_interface import SettingInterface

LOGO_PATH = ASSETS_PATH / "logo.png"

class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()

        # 创建子界面
        self.homeInterface = HomeInterface(self)
        self.settingInterface = SettingInterface(self)
        self.subtitleStyleInterface = SubtitleStyleInterface(self)
        self.batchProcessInterface = BatchProcessInterface(self)

        # 初始化版本管理器
        self.versionManager = VersionManager()
        self.versionManager.newVersionAvailable.connect(self.onNewVersion)
        self.versionManager.announcementAvailable.connect(self.onAnnouncement)

        # 创建版本检查线程
        self.versionThread = QThread()
        self.versionManager.moveToThread(self.versionThread)
        self.versionThread.started.connect(self.versionManager.performCheck)
        self.versionThread.start()

        # 初始化导航界面
        self.initNavigation()
        self.splashScreen.finish()

    def initNavigation(self):
        """初始化导航栏"""
        # 添加导航项
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('主页'))
        self.addSubInterface(self.batchProcessInterface, FIF.VIDEO, self.tr('批量处理'))
        self.addSubInterface(self.subtitleStyleInterface, FIF.FONT, self.tr('字幕样式'))

        self.navigationInterface.addSeparator()

        # 在底部添加自定义小部件
        self.navigationInterface.addItem(routeKey='avatar', text='GitHub', icon=FIF.GITHUB, onClick=self.onGithubDialog, position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('Settings'), NavigationItemPosition.BOTTOM)

        # 设置默认界面
        self.switchTo(self.homeInterface)

    def switchTo(self, interface):
        if interface.windowTitle():
            self.setWindowTitle(interface.windowTitle())
        else:
            self.setWindowTitle(self.tr('卡卡字幕助手 -- VideoCaptioner'))
        self.stackedWidget.setCurrentWidget(interface, popOut=False)

    def initWindow(self):
        """初始化窗口"""
        self.resize(1050, 800)
        self.setMinimumWidth(700)
        self.setWindowIcon(QIcon(str(LOGO_PATH)))
        self.setWindowTitle(self.tr('卡卡字幕助手 -- VideoCaptioner'))

        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # 创建启动画面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        # 设置窗口位置, 居中
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.show()
        QApplication.processEvents()

    def onGithubDialog(self):
        """打开GitHub"""
        w = MessageBox(
            'GitHub信息',
            'VideoCaptioner 由本人在课余时间独立开发完成，目前托管在GitHub上，欢迎Star和Fork。项目诚然还有很多地方需要完善，遇到软件的问题或者BUG欢迎提交Issue。\n\n https://github.com/WEIFENG2333/VideoCaptioner',
            self
        )
        w.yesButton.setText('打开 GitHub')
        w.cancelButton.setText('取消')
        if w.exec():
            QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL))

    def onNewVersion(self, version, force_update, update_info, download_url):
        """新版本提示"""
        title = '发现新版本' if not force_update else '当前版本已停用'
        content = f'发现新版本 {version}\n\n{update_info}'
        w = MessageBox(title, content, self)
        w.yesButton.setText('立即更新')
        w.cancelButton.setText('稍后再说' if not force_update else '退出程序')
        if w.exec():
            QDesktopServices.openUrl(QUrl(download_url))
        if force_update:
            QApplication.quit()

    def onAnnouncement(self, content):
        """显示公告"""
        w = MessageBox('公告', content, self)
        w.yesButton.setText('我知道了')
        w.cancelButton.hide()
        w.exec()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())

    def closeEvent(self, event):
        # 关闭所有子界面
        self.homeInterface.close()
        self.batchProcessInterface.close()
        self.subtitleStyleInterface.close()
        self.settingInterface.close()
        super().closeEvent(event)
