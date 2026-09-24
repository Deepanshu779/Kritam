WINDOW_STYLE = """
QMainWindow { background: #050a14; }
QWidget { color: #eef4ff; font-family: "Segoe UI"; font-size: 14px; }
QWidget#homePage { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #050b16,stop:0.58 #081222,stop:1 #0d1a2d); border: 1px solid #142b49; border-radius: 18px; }
QFrame#sidebar { background: #07101d; border: 1px solid #142b49; border-radius: 18px; }
QLabel#sidebarLogo { background: qlineargradient(x1:0,y1:1,x2:1,y2:0,stop:0 #1168e8,stop:0.55 #25a9ff,stop:1 #8c6cff); border-radius: 10px; color: white; font-size: 25px; font-weight: 800; }
QLabel#brand { color: #f5f8ff; font-size: 20px; font-weight: 800; letter-spacing: 1px; }
QLabel#muted { color: #8191ab; }
QPushButton#nav { text-align: left; padding: 12px 13px; border: 1px solid transparent; border-radius: 11px; background: transparent; color: #aab8ce; }
QPushButton#nav:hover { background: #10213a; color: white; }
QPushButton#nav:checked { background: #12396b; border: 1px solid #159cff; color: white; }
QFrame#sidebarProfile { background: #0b1729; border: 1px solid #203858; border-radius: 13px; }
QLabel#readyText { color: #dce8ff; font-weight: 650; }
QLabel#sidebarFooter { color: #71819b; font-size: 12px; }

QLabel#dashboardTitle { color: #f3f7ff; font-size: 26px; font-weight: 800; letter-spacing: 1px; }
QLabel#dashboardSubtitle { color: #8292ad; font-size: 13px; }
QPushButton#windowIcon { background: transparent; border: none; color: #9aa9bf; font-size: 19px; }
QFrame#heroPanel { background: #081728; border: 1px solid #1c3b62; border-radius: 18px; }
QLabel#heroGreeting { color: #f7faff; font-size: 31px; font-weight: 800; }
QLabel#heroSub { color: #e0e9f8; font-size: 18px; }
QLabel#heroDesc { color: #93a3bd; font-size: 14px; }
QLabel#sectionTitle { color: #eef4ff; font-size: 16px; font-weight: 700; }
QPushButton#dashboardCard { text-align: left; background: #0c192b; border: 1px solid #1c3554; border-radius: 14px; color: #edf3ff; }
QPushButton#dashboardCard:hover { background: #112540; border: 1px solid #287ed1; }
QLabel#dashboardIcon { color: #56b6ff; font-size: 23px; font-weight: 700; }
QLabel#dashboardCardTitle { color: #edf3ff; font-size: 14px; font-weight: 700; }
QLabel#dashboardCardDesc { color: #8193ae; font-size: 11px; }

QFrame#composer { background: #071321; border: 1px solid #27476c; border-radius: 15px; }
QLineEdit { background: #08111e; border: 1px solid #1b304d; border-radius: 10px; padding: 11px 14px; color: #f4f8ff; }
QLineEdit:focus { border: 1px solid #159cff; }
QPushButton#composerIcon { background: #0d1c30; border: 1px solid #27405f; border-radius: 10px; color: #a8b9d0; font-size: 20px; }
QPushButton#primary { background: #157cff; border: 1px solid #49a9ff; border-radius: 10px; color: white; font-size: 20px; font-weight: 700; }
QPushButton#primary:hover { background: #2890ff; }
QPushButton#mic { background: #0d2340; border: 1px solid #258dff; border-radius: 10px; color: #8ed2ff; font-size: 15px; }
QPushButton#chip { background: #0b182a; border: 1px solid #203b5c; border-radius: 17px; padding: 7px 13px; color: #9fb0c9; }
QPushButton#chip:hover { background: #122641; color: white; }

QFrame#profileCard, QFrame#sideCard { background: #0a1627; border: 1px solid #1b3553; border-radius: 15px; }
QLabel#sideTitle { color: #f0f5ff; font-size: 15px; font-weight: 750; }
QLabel#readyAccent { color: #16e6b4; font-size: 12px; font-weight: 650; }
QLabel#speechBubble { background: #0d1d32; border: 1px solid #204268; border-radius: 13px; color: #c9d5e8; padding: 11px; }
QPushButton#sideAction { text-align: left; background: #0d1b2e; border: 1px solid #1b304c; border-radius: 9px; color: #cbd7e9; padding: 9px 10px; }
QPushButton#sideAction:hover { background: #132844; border: 1px solid #2a6094; color: white; }
QLabel#voiceValue { background: #0d1b2e; border: 1px solid #1b3553; border-radius: 9px; padding: 9px; color: #cbd8eb; }
QPushButton#listenButton { background: #082b49; border: 1px solid #159cff; border-radius: 18px; padding: 10px; color: #dff5ff; font-weight: 700; }
QPushButton#listenButton:hover { background: #0d3b61; }

QFrame#card { background: #0b1728; border: 1px solid #1d3452; border-radius: 15px; }
QLabel#heroTitle { font-size: 30px; font-weight: 750; }
QLabel#cardTitle { color: #f2f5ff; font-size: 16px; font-weight: 700; }
QLabel#cardText { color: #b9c5da; font-size: 14px; }
QLabel#hint { color: #7f8da6; font-size: 13px; }
QLabel#settingLabel { color: #9aa9c2; font-size: 13px; padding: 7px 0; }
QLabel#settingValue { color: #edf2ff; font-size: 13px; font-weight: 600; padding: 7px 0; }
QPushButton { background: #101d30; border: 1px solid #223852; border-radius: 9px; padding: 8px 12px; }
QPushButton:hover { background: #172944; }
QScrollArea { border: none; background: transparent; }
QWidget#voiceRecordingBar { background: #111d2d; border: 1px solid #2b496b; border-radius: 28px; }
QPushButton#voiceCancel { background: transparent; border: none; color: #7f90a9; font-size: 28px; }
QPushButton#voiceFinish { background: #15304b; border: 1px solid #376083; border-radius: 20px; color: #eff7ff; font-size: 21px; }
"""