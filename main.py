import os
import re
import time
import sys
import importlib

import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QGroupBox, QDialog, QFormLayout,
    QDoubleSpinBox, QToolButton
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer, QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineScript, QWebEnginePage

from config import (
    VK_API_VERSION,
    DELAY_BETWEEN_REQUESTS,
    DELETE_COMMENT_URL
)

CONFIG_DEFAULTS = """\
FOLDER_PATH = r'Z:/Архив_ВК/comments/' # Путь к папке с файлами https://vk.com/data_protection?section=rules&scroll_to_archive=1
ACCESS_TOKEN = 'vk1.a.Sq1MjQsdfsdffffdsfsfsdfsdf'  # Токен через f12
VK_API_VERSION = '5.199' # Версия VK API https://dev.vk.com/ru/reference/versions
DELAY_BETWEEN_REQUESTS = 0.05 # Задержка между запросами к API (в секундах)
DELETE_COMMENT_URL = 'https://api.vk.com/method/wall.deleteComment' # Версия VK API https://dev.vk.com/ru/method/board.deleteComment
"""


def load_config():
    import config
    importlib.reload(config)
    return config


def reset_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.py")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(CONFIG_DEFAULTS)


BG_PRIMARY   = "#18181b"
BG_SECONDARY = "#27272a"
BG_TERTIARY  = "#3f3f46"
ACCENT       = "#6366f1"
ACCENT_HOVER = "#818cf8"
DANGER       = "#ef4444"
DANGER_HOVER = "#f87171"
SUCCESS      = "#22c55e"
SUCCESS_HOVER= "#4ade80"
WARNING_CLR  = "#f59e0b"
TEXT_PRIMARY = "#fafafa"
TEXT_SECOND  = "#a1a1aa"
BORDER       = "#52525b"
LOG_BG       = "#0f0f11"


STYLESHEET = f"""
    QMainWindow, QWidget {{
        background-color: {BG_PRIMARY};
        color: {TEXT_PRIMARY};
        font-family: "Segoe UI"; font-size: 14px;
    }}
    QGroupBox {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER};
        border-radius: 12px;
        margin-top: 12px;
        padding-top: 20px;
        font-weight: bold;
        color: {TEXT_SECOND};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
    }}
    QLineEdit {{
        background-color: {BG_TERTIARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 8px 12px;
        color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT};
    }}
    QLineEdit:read-only {{ color: {SUCCESS}; }}
    QPushButton {{
        background-color: {BG_TERTIARY};
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        color: {TEXT_PRIMARY};
        font-weight: 500;
    }}
    QPushButton:hover {{ background-color: {ACCENT}; }}
    QPushButton:pressed {{ background-color: {ACCENT_HOVER}; }}
    QPushButton:disabled {{
        background-color: {BG_TERTIARY};
        color: {TEXT_SECOND};
    }}
    QPushButton#Primary {{ background-color: {ACCENT}; color: #fff; }}
    QPushButton#Primary:hover {{ background-color: {ACCENT_HOVER}; }}
    QPushButton#Success {{ background-color: {SUCCESS}; color: #000; }}
    QPushButton#Success:hover {{ background-color: {SUCCESS_HOVER}; }}
    QPushButton#Danger {{ background-color: {DANGER}; color: #fff; }}
    QPushButton#Danger:hover {{ background-color: {DANGER_HOVER}; }}
    QProgressBar {{
        background-color: {BG_TERTIARY};
        border: none;
        border-radius: 6px;
        text-align: center;
        height: 8px;
    }}
    QProgressBar::chunk {{
        background-color: {ACCENT};
        border-radius: 6px;
    }}
    QTextEdit {{
        background-color: {LOG_BG};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 10px;
        color: {TEXT_PRIMARY};
        font-family: "Cascadia Code", "Consolas", "Courier New";
        font-size: 13px;
    }}
    QLabel {{ color: {TEXT_SECOND}; }}
    QScrollArea, QScrollBar:vertical {{
        border: none;
        background: {BG_TERTIARY};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {TEXT_SECOND}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    QSpinBox, QDoubleSpinBox {{
        background-color: {BG_TERTIARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 6px 10px;
        color: {TEXT_PRIMARY};
    }}
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        background-color: {BG_SECONDARY};
        border: none;
        border-radius: 4px;
        width: 20px;
    }}
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
        background-color: {BG_TERTIARY};
    }}
    QComboBox {{
        background-color: {BG_TERTIARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 6px 10px;
        color: {TEXT_PRIMARY};
    }}
    QComboBox::drop-down {{ border: none; }}
    QComboBox QAbstractItemView {{
        background-color: {BG_SECONDARY};
        color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT};
    }}
"""


TOKEN_INTERCEPT_JS = """
(function() {
    if (window.__vkTokenHook) return;
    window.__vkTokenHook = true;

    function extractToken(urlOrBody) {
        if (!urlOrBody) return;
        const m = urlOrBody.match(/access_token=([^&"\\s]+)/);
        if (m) console.log('__VK_TOKEN__' + m[1]);
    }

    const _fetch = window.fetch;
    window.fetch = function(...args) {
        const url = typeof args[0] === 'string' ? args[0]
                  : args[0] && args[0].url ? args[0].url : '';
        if (url.includes('api.vk.com/method/')) extractToken(url);
        if (args[0] && typeof args[0] === 'object' && args[0].body) {
            extractToken(typeof args[0].body === 'string' ? args[0].body : '');
        }
        if (args[1] && args[1].body) {
            extractToken(typeof args[1].body === 'string' ? args[1].body : '');
        }
        return _fetch.apply(this, args).then(async resp => {
            try {
                const clone = resp.clone();
                const text = await clone.text();
                extractToken(text);
            } catch(e) {}
            return resp;
        });
    };

    const _open = XMLHttpRequest.prototype.open;
    const _send = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
        this._vkUrl = url;
        return _open.apply(this, [method, url, ...rest]);
    };
    XMLHttpRequest.prototype.send = function(body) {
        if (this._vkUrl && this._vkUrl.includes('api.vk.com/method/')) {
            extractToken(this._vkUrl);
            if (body) extractToken(typeof body === 'string' ? body : '');
        }
        return _send.apply(this, arguments);
    };
})();
"""


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️  Настройки")
        self.setModal(True)
        self.resize(520, 320)
        self.setMinimumWidth(440)

        cfg = load_config()

        lo = QVBoxLayout(self)
        lo.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.folder_edit = QLineEdit(cfg.FOLDER_PATH)
        self.folder_browse = QPushButton("…")
        self.folder_browse.setFixedWidth(32)
        self.folder_browse.clicked.connect(self._pick_folder)
        folder_h = QHBoxLayout()
        folder_h.addWidget(self.folder_edit)
        folder_h.addWidget(self.folder_browse)
        folder_h.setSpacing(6)
        form.addRow("Папка:", folder_h)

        self.version_edit = QLineEdit(cfg.VK_API_VERSION)
        form.addRow("VK API версия:", self.version_edit)

        self.delay_edit = QDoubleSpinBox()
        self.delay_edit.setRange(0, 10)
        self.delay_edit.setSingleStep(0.01)
        self.delay_edit.setValue(cfg.DELAY_BETWEEN_REQUESTS)
        self.delay_edit.setDecimals(3)
        self.delay_edit.setSuffix(" сек")
        form.addRow("Задержка:", self.delay_edit)

        self.url_edit = QLineEdit(cfg.DELETE_COMMENT_URL)
        form.addRow("API URL:", self.url_edit)

        lo.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        reset_btn = QPushButton("↺  По умолчанию")
        reset_btn.setObjectName("Danger")
        reset_btn.clicked.connect(self._reset)
        save_btn = QPushButton("💾  Сохранить")
        save_btn.setObjectName("Primary")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(reset_btn)
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        lo.addLayout(btns)

    def _pick_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if d:
            self.folder_edit.setText(d)

    def _reset(self):
        reset_config()
        cfg = load_config()
        self.folder_edit.setText(cfg.FOLDER_PATH)
        self.version_edit.setText(cfg.VK_API_VERSION)
        self.delay_edit.setValue(cfg.DELAY_BETWEEN_REQUESTS)
        self.url_edit.setText(cfg.DELETE_COMMENT_URL)
        QMessageBox.information(self, "Сброс", "Настройки сброшены до значений по умолчанию.")

    def _save(self):
        folder = self.folder_edit.text().strip()
        version = self.version_edit.text().strip()
        delay = self.delay_edit.value()
        url = self.url_edit.text().strip()

        if not folder:
            QMessageBox.warning(self, "Ошибка", "Укажите путь к папке.")
            return
        if not version:
            QMessageBox.warning(self, "Ошибка", "Укажите версию VK API.")
            return
        if not url:
            QMessageBox.warning(self, "Ошибка", "Укажите API URL.")
            return

        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.py")
        content = (
            f"FOLDER_PATH = r'{folder}' "
            f"# Путь к папке с файлами https://vk.com/data_protection?section=rules&scroll_to_archive=1\n"
            f"ACCESS_TOKEN = 'vk1.a.Sq1MjQsdfsdffffdsfsfsdfsdf'  "
            f"# Токен через f12\n"
            f"VK_API_VERSION = '{version}' "
            f"# Версия VK API https://dev.vk.com/ru/reference/versions\n"
            f"DELAY_BETWEEN_REQUESTS = {delay} "
            f"# Задержка между запросами к API (в секундах)\n"
            f"DELETE_COMMENT_URL = '{url}' "
            f"# Версия VK API https://dev.vk.com/ru/method/board.deleteComment\n"
        )
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)

        import config
        importlib.reload(config)

        self.accept()
        QMessageBox.information(self, "Сохранено", "Настройки сохранены в config.py.")


class VKWebPage(QWebEnginePage):
    token_found = pyqtSignal(str)

    def javaScriptConsoleMessage(self, level, message, line, source):
        if message.startswith("__VK_TOKEN__"):
            token = message[len("__VK_TOKEN__"):]
            self.token_found.emit(token)


class VKLoginView(QWebEngineView):
    def closeEvent(self, ev):
        if self.isVisible():
            box = QMessageBox(QMessageBox.Icon.Warning,
                               "Закрыть окно авторизации?",
                               "Это окно используется для получения токена VK.\n"
                               "Если закрыть его, удаление комментариев прекратится,\n"
                               "и нужно будет авторизоваться заново.\n\n"
                               "До полного удаления комментариев, можно скрыть окно\n\n"
                               "Закрыть окно?",
                               QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes,
                               None)
            box.setDefaultButton(QMessageBox.StandardButton.No)
            box.setModal(True)
            box.button(QMessageBox.StandardButton.Yes).setText("Да")
            box.button(QMessageBox.StandardButton.No).setText("Нет")
            if box.exec() == QMessageBox.StandardButton.No:
                ev.ignore()
                return
        super().closeEvent(ev)


class DeletionWorker(QThread):
    progress = pyqtSignal(float)
    log = pyqtSignal(str, str)
    finished_signal = pyqtSignal()

    def __init__(self, folder: str, token: str):
        super().__init__()
        self.folder = folder
        self.token = token
        self._running = True

    def run(self):
        cfg = load_config()
        vk_api_ver = cfg.VK_API_VERSION
        delay = cfg.DELAY_BETWEEN_REQUESTS
        api_url = cfg.DELETE_COMMENT_URL

        if not os.path.exists(self.folder):
            self.log.emit(f"❌ Папка не найдена: {self.folder}", "error")
            self.finished_signal.emit()
            return

        files = [os.path.join(self.folder, f) for f in os.listdir(self.folder)
                  if f.lower().endswith(('.html', '.htm', '.txt'))
                  and os.path.isfile(os.path.join(self.folder, f))]

        if not files:
            self.log.emit(f"❌ Файлы не найдены в: {self.folder}", "error")
            self.finished_signal.emit()
            return

        self.log.emit(f"🔎 Найдено {len(files)} файлов для обработки…", "info")

        total_processed = 0
        total_deleted = 0
        processed = set()
        total_files = len(files)

        for idx, fpath in enumerate(files, 1):
            if not self._running:
                break
            self.log.emit(f"\n📄 Обработка: {os.path.basename(fpath)}", "info")
            urls = self._extract_links(fpath)
            for url in urls:
                if not self._running:
                    break
                ids = self._parse_ids(url)
                if not ids:
                    continue
                cid = ids['comment_id']
                if cid in processed:
                    self.log.emit(f"ℹ️ Пропущено: {cid} (уже обработано)", "warning")
                    continue
                processed.add(cid)
                total_processed += 1
                if self._delete(ids['owner_id'], cid, vk_api_ver, delay, api_url):
                    total_deleted += 1
                time.sleep(delay)
            self.progress.emit((idx / total_files) * 100)

        self.log.emit("\n" + "=" * 50, "info")
        self.log.emit("🔥 Удаление завершено!", "success")
        self.log.emit(f"📁 Файлов обработано: {len(files)}", "info")
        self.log.emit(f"🔎 Ссылок найдено: {total_processed}", "info")
        self.log.emit(f"✅ Успешно удалено: {total_deleted}", "success")
        self.log.emit(f"❌ Не удалось удалить: {total_processed - total_deleted}", "info")
        self.log.emit("=" * 50, "info")
        self.finished_signal.emit()

    def stop(self):
        self._running = False

    def _extract_links(self, fp):
        for enc in ['cp1251', 'latin1', 'utf-8', 'utf-16']:
            try:
                with open(fp, 'r', encoding=enc) as f:
                    content = f.read()
                self.log.emit(f"✅ {os.path.basename(fp)} — прочитано ({enc})", "info")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.log.emit(f"❌ Ошибка чтения {fp}: {e}", "error")
                return []
        else:
            self.log.emit(f"❌ Не удалось прочитать файл: {fp}", "error")
            return []
        urls = re.findall(r'https://vk\.com/wall-?\d+_\d+\?reply=\d+', content)
        self.log.emit(f"🔗 Найдено ссылок: {len(urls)}", "info")
        return urls

    @staticmethod
    def _parse_ids(url):
        m = re.search(r'wall(-?\d+)_(\d+)\?reply=(\d+)', url)
        return {'owner_id': int(m.group(1)), 'comment_id': int(m.group(3))} if m else None

    def _delete(self, owner_id, comment_id, vk_api_ver, delay, api_url):
        params = {'access_token': self.token, 'v': vk_api_ver,
                   'owner_id': owner_id, 'comment_id': comment_id}
        try:
            data = requests.post(api_url.strip(), data=params).json()
            if 'response' in data:
                self.log.emit(f"✅ Удалён: {comment_id}", "success")
                return True
            if 'error' in data:
                err = data['error']
                code, msg = err['error_code'], err['error_msg']
                h = {
                    211: lambda: self.log.emit(f"ℹ️ Пропущено {comment_id}: доступ запрещён", "warning"),
                    18:  lambda: self.log.emit(f"ℹ️ Пропущено {comment_id}: страница удалена", "warning"),
                    9:   lambda: (self.log.emit("💤 Слишком частые запросы", "warning"), time.sleep(5)),
                    6:   lambda: (self.log.emit("💤 Нужен больший интервал", "warning"), time.sleep(1)),
                    14:  lambda: self.log.emit("❌ Требуется Captcha", "error"),
                    7:   lambda: self.log.emit(f"❌ Нет прав на удаление {comment_id}", "error"),
                }
                (h.get(code,
                  lambda: self.log.emit(f"❌ [{code}] {comment_id}: {msg}", "error")))()
                return False
            self.log.emit(f"❌ Неизвестный ответ для {comment_id}: {data}", "error")
            return False
        except Exception as e:
            self.log.emit(f"❌ Ошибка при удалении {comment_id}: {e}", "error")
            return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VK Delete Comments")
        self.resize(700, 780)
        self.setMinimumSize(700, 780)

        self.access_token = ""
        self.folder_path = ""
        self.deletion_worker = None
        self.browser = None
        self._token_flash_timer = QTimer(self)

        self._init_ui()
        self._connect_signals()
        self._load_folder_from_config()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        lo = QVBoxLayout(central)
        lo.setContentsMargins(20, 20, 20, 20)
        lo.setSpacing(14)

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.settings_btn = QToolButton()
        self.settings_btn.setText("⚙️")
        self.settings_btn.setToolTip("Настройки")
        self.settings_btn.setFixedSize(36, 36)
        self.settings_btn.setStyleSheet(
            f"QToolButton {{ background: {BG_TERTIARY}; border: none; "
            f"border-radius: 8px; font-size: 18px; color: {TEXT_SECOND}; }}"
            f"QToolButton:hover {{ background: {ACCENT}; color: #fff; }}"
        )
        self.settings_btn.clicked.connect(self._open_settings)
        top_bar.addWidget(self.settings_btn)
        lo.addLayout(top_bar)

        g = QGroupBox("📂  Папка с файлами")
        gl = QHBoxLayout(g)
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        self.folder_edit.setMinimumHeight(36)
        self.browse_btn = QPushButton("Обзор…")
        self.browse_btn.setMinimumHeight(36)
        self.browse_btn.setMinimumWidth(90)
        gl.addWidget(self.folder_edit)
        gl.addWidget(self.browse_btn)
        lo.addWidget(g)

        g = QGroupBox("🔑  Авторизация VK")
        gl = QHBoxLayout(g)
        self.login_btn = QPushButton("Войти в VK")
        self.login_btn.setObjectName("Primary")
        self.login_btn.setEnabled(False)
        self.login_btn.setMinimumHeight(36)
        self.login_btn.setMinimumWidth(130)
        self.refresh_btn = QPushButton("⟳  Обновить токен")
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setMinimumHeight(36)
        self.refresh_btn.setMinimumWidth(150)
        gl.addWidget(self.login_btn)
        gl.addWidget(self.refresh_btn)
        gl.addStretch()
        lo.addWidget(g)

        g = QGroupBox("🎫  Access Token")
        gl = QHBoxLayout(g)
        self.token_edit = QLineEdit()
        self.token_edit.setReadOnly(True)
        self.token_edit.setMinimumHeight(36)
        gl.addWidget(self.token_edit)
        lo.addWidget(g)

        ctrl_box = QGroupBox("⚙️  Управление")
        ctrl_lo = QVBoxLayout(ctrl_box)
        ctrl_lo.setContentsMargins(14, 5, 14, 16)
        ctrl_lo.setSpacing(12)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.delete_btn = QPushButton("▶  Удалить комментарии")
        self.delete_btn.setObjectName("Success")
        self.delete_btn.setEnabled(False)
        self.delete_btn.setMinimumHeight(48)
        self.stop_btn = QPushButton("■  Остановить")
        self.stop_btn.setObjectName("Danger")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(48)
        btn_row.addWidget(self.delete_btn, stretch=1)
        btn_row.addWidget(self.stop_btn, stretch=1)
        ctrl_lo.addLayout(btn_row)

        self.progress = QProgressBar()
        ctrl_lo.addWidget(self.progress)

        self.status_lbl = QLabel("Готово к работе")
        ctrl_lo.addWidget(self.status_lbl)
        lo.addWidget(ctrl_box)

        g = QGroupBox("📋  Логи")
        gl = QVBoxLayout(g)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMinimumHeight(200)
        gl.addWidget(self.log_edit)
        lo.addWidget(g)

    def _connect_signals(self):
        self.browse_btn.clicked.connect(self._select_folder)
        self.login_btn.clicked.connect(self._login_to_vk)
        self.refresh_btn.clicked.connect(self._manual_refresh)
        self.delete_btn.clicked.connect(self._start_deletion)
        self.stop_btn.clicked.connect(self._stop_deletion)
        self._token_flash_timer.setSingleShot(True)
        self._token_flash_timer.timeout.connect(self._flash_token)

    def _load_folder_from_config(self):
        cfg = load_config()
        if cfg.FOLDER_PATH and os.path.isdir(cfg.FOLDER_PATH):
            self.folder_path = cfg.FOLDER_PATH
            self.folder_edit.setText(cfg.FOLDER_PATH)
            self.login_btn.setEnabled(True)

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            cfg = load_config()
            if cfg.FOLDER_PATH:
                self.folder_path = cfg.FOLDER_PATH
                self.folder_edit.setText(cfg.FOLDER_PATH)
                if os.path.isdir(cfg.FOLDER_PATH):
                    self.login_btn.setEnabled(True)
            self._log("⚙️ Настройки обновлены из config.py", "info")

    def _log(self, msg, level="info"):
        c = {"info": TEXT_PRIMARY, "success": SUCCESS,
             "error": DANGER, "warning": WARNING_CLR}.get(level, TEXT_PRIMARY)
        self.log_edit.append(f'<span style="color:{c}">{msg}</span>')

    def _select_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите папку с файлами")
        if d:
            self.folder_path = d
            self.folder_edit.setText(d)
            self._log(f"📁 Выбрана папка: {d}")
            self.login_btn.setEnabled(True)

    def _login_to_vk(self):
        if self.browser:
            self._log("⚠️ Браузер уже запущен", "warning")
            return
        self._log("🔄 Запуск браузера для авторизации в VK…")
        self.login_btn.setEnabled(False)

        page = VKWebPage(self)
        page.token_found.connect(self._set_token)

        script = QWebEngineScript()
        script.setSourceCode(TOKEN_INTERCEPT_JS)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)
        page.scripts().insert(script)

        self.browser = VKLoginView()
        self.browser.setPage(page)
        self.browser.setWindowTitle("VK Login")
        self.browser.resize(1024, 700)
        self.browser.destroyed.connect(self._on_browser_closed)
        self.browser.load(QUrl("https://vk.com"))
        self.browser.show()

        self.refresh_btn.setEnabled(True)
        self._log("✅ Браузер открыт. Войдите в свой аккаунт.")
        self._log("⏳ Токен будет автоматически извлекаться из запросов VK API…")

    def _manual_refresh(self):
        self._log("🔄 Ручное обновление токена…", "info")
        if self.browser:
            self.browser.reload()
            self._log("🔄 Страница обновляется, ожидайте…", "info")
        elif not self.access_token:
            self._log("⏳ Сначала нажмите 'Войти в VK'", "warning")

    def _set_token(self, token: str):
        if token == self.access_token:
            return
        self.access_token = token
        self.token_edit.setText(token)
        if self.folder_path:
            self.delete_btn.setEnabled(True)
        self._log("✅ Токен успешно получен!", "success")
        self._token_flash_timer.start(2000)

    def _flash_token(self):
        if self.access_token and len(self.access_token) > 20:
            self.token_edit.setText(self.access_token[:20] + "•••")

    def _on_browser_closed(self):
        self.browser = None
        self.login_btn.setEnabled(True)
        self.refresh_btn.setEnabled(False)
        self._log("⚠️ Окно авторизации закрыто. Токен перестанет обновляться.", "warning")

    def _start_deletion(self):
        if not self.folder_path:
            QMessageBox.critical(self, "Ошибка", "Выберите папку с файлами!")
            return
        if not self.access_token:
            QMessageBox.critical(self, "Ошибка", "Получите токен доступа!")
            return
        self.delete_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_lbl.setText("⏳ Удаление запущено…")
        self.deletion_worker = DeletionWorker(self.folder_path, self.access_token)
        self.deletion_worker.progress.connect(self.progress.setValue)
        self.deletion_worker.log.connect(self._log)
        self.deletion_worker.finished_signal.connect(self._deletion_finished)
        self.deletion_worker.start()

    def _stop_deletion(self):
        if self.deletion_worker:
            self.deletion_worker.stop()
        self.status_lbl.setText("⏹️ Остановлено пользователем")
        self._log("⏹️ Процесс удаления остановлен", "warning")

    def _deletion_finished(self):
        self.delete_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_lbl.setText("✅ Готово")
        self.progress.setValue(100)

    def closeEvent(self, ev):
        reset_config()
        self._log("↺ config.py сброшен до значений по умолчанию", "info")

        if self.browser:
            self.browser.close()
            self.browser.deleteLater()
        if self.deletion_worker and self.deletion_worker.isRunning():
            self.deletion_worker.stop()
            self.deletion_worker.wait()
        ev.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setWindowIcon(QIcon('icon.ico'))
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
