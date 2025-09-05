import sys
from pathlib import Path
from typing import List

from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QMessageBox,
    QGroupBox,
)

class Odin4GUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Odin4 GUI – PyQt5")
        self.setMinimumSize(900, 650)

        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self.on_proc_output)
        self.proc.finished.connect(self.on_proc_finished)
        self.proc.errorOccurred.connect(self.on_proc_error)

        self.build_ui()
        self.refresh_cmd_preview()

    def build_ui(self):
        root = QVBoxLayout()

        files_box = QGroupBox("Firmware Files (.tar.md5 / .tar)")
        files_layout = QGridLayout()
        self.file_fields = {}
        for row, (key, label) in enumerate([
            ("BL", "Bootloader (-b)"),
            ("AP", "AP Image (-a)"),
            ("CP", "CP Modem (-c)"),
            ("CSC", "CSC (-s)"),
            ("UMS", "UMS (-u)")
        ]):
            le = QLineEdit()
            le.setPlaceholderText(f"Select {key}…")
            le.textChanged.connect(self.refresh_cmd_preview)
            btn = QPushButton("Browse…")
            btn.clicked.connect(lambda _=None, k=key, line=le: self.pick_file(k, line))
            files_layout.addWidget(QLabel(f"{label}:",), row, 0)
            files_layout.addWidget(le, row, 1)
            files_layout.addWidget(btn, row, 2)
            self.file_fields[key] = le
        files_box.setLayout(files_layout)

        opt_box = QGroupBox("Options")
        opt_layout = QHBoxLayout()
        self.chk_erase = QCheckBox("Erase NAND (-e)")
        self.chk_validate = QCheckBox("Home binary validation (-V)")
        self.chk_reboot = QCheckBox("Reboot to normal (--reboot)")
        self.chk_redl = QCheckBox("Reboot to DL (--redownload)")
        for chk in [self.chk_erase, self.chk_validate, self.chk_reboot, self.chk_redl]:
            chk.stateChanged.connect(self.refresh_cmd_preview)
            opt_layout.addWidget(chk)
        opt_box.setLayout(opt_layout)

        actions = QHBoxLayout()
        self.btn_show_ver = QPushButton("Show Version (-v)")
        self.btn_show_ver.clicked.connect(self.run_show_version)
        self.btn_show_lic = QPushButton("Show License (-w)")
        self.btn_show_lic.clicked.connect(self.run_show_license)
        self.btn_start = QPushButton("Start Flash ▶︎")
        self.btn_start.clicked.connect(self.start_flash)
        self.btn_abort = QPushButton("Abort ✕")
        self.btn_abort.clicked.connect(self.abort_process)
        self.btn_abort.setEnabled(False)
        self.btn_clearlog = QPushButton("Clear Log")
        self.btn_clearlog.clicked.connect(lambda: self.log.clear())
        actions.addWidget(self.btn_show_ver)
        actions.addWidget(self.btn_show_lic)
        actions.addStretch(1)
        actions.addWidget(self.btn_clearlog)
        actions.addWidget(self.btn_abort)
        actions.addWidget(self.btn_start)

        self.cmd_preview = QLabel()
        self.cmd_preview.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.cmd_preview.setStyleSheet("QLabel { font-family: monospace; }")

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Output will appear here…")

        root.addWidget(files_box)
        root.addWidget(opt_box)
        root.addLayout(actions)
        root.addWidget(QLabel("Command Preview:"))
        root.addWidget(self.cmd_preview)
        root.addWidget(QLabel("Log:"))
        root.addWidget(self.log, 1)

        self.setLayout(root)

    def pick_file(self, key: str, line: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(self, f"Select {key} file", str(Path.home()), "Firmware (*.tar *.tar.md5);;All files (*)")
        if path:
            line.setText(path)

    def build_args(self) -> List[str]:
        args: List[str] = []
        mapping = {
            "BL": "-b",
            "AP": "-a",
            "CP": "-c",
            "CSC": "-s",
            "UMS": "-u",
        }
        for key, flag in mapping.items():
            val = self.file_fields[key].text().strip()
            if val:
                args += [flag, val]
        if self.chk_erase.isChecked():
            args.append("-e")
        if self.chk_validate.isChecked():
            args.append("-V")
        if self.chk_reboot.isChecked():
            args.append("--reboot")
        if self.chk_redl.isChecked():
            args.append("--redownload")
        return args

    def refresh_cmd_preview(self):
        exe = "odin4.exe" if sys.platform.startswith("win") else "odin4"
        quoted = lambda s: f'"{s}"' if (" " in s or "\t" in s) else s
        args = [quoted(a) for a in self.build_args()]
        self.cmd_preview.setText(" ".join([quoted(exe)] + args))

    def log_append(self, text: str):
        self.log.moveCursor(self.log.textCursor().End)
        self.log.insertPlainText(text)
        self.log.moveCursor(self.log.textCursor().End)

    def run_show_version(self):
        self.log_append("\nShowing version (-v)…\n")
        self.run_proc(["odin4", "-v"])

    def run_show_license(self):
        self.log_append("\nShowing license (-w)…\n")
        self.run_proc(["odin4", "-w"])

    def validate_before_flash(self) -> bool:
        if not any(self.file_fields[k].text().strip() for k in self.file_fields):
            QMessageBox.warning(self, "Missing files", "Please choose at least one firmware file (BL/AP/CP/CSC/UMS).")
            return False
        return True

    def start_flash(self):
        if not self.validate_before_flash():
            return
        cmd = ["odin4"] + self.build_args()
        self.log_append("\nStarting Odin4…\n")
        self.run_proc(cmd)
        self.btn_start.setEnabled(False)
        self.btn_abort.setEnabled(True)

    def abort_process(self):
        if self.proc.state() != QProcess.NotRunning:
            self.proc.kill()
            self.log_append("\nProcess aborted by user.\n")
        self.btn_start.setEnabled(True)
        self.btn_abort.setEnabled(False)

    def run_proc(self, cmd: List[str]):
        try:
            self.proc.start(cmd[0], cmd[1:])
        except Exception as e:
            QMessageBox.critical(self, "Failed to start", f"Could not start process:\n{e}")

    def on_proc_output(self):
        data = self.proc.readAllStandardOutput().data().decode(errors="replace")
        self.log_append(data)

    def on_proc_finished(self, code: int, status):
        self.log_append(f"\n[Process finished with code {code}]\n")
        self.btn_start.setEnabled(True)
        self.btn_abort.setEnabled(False)

    def on_proc_error(self, error):
        self.log_append(f"\n[Process error: {error}]\n")
        self.btn_start.setEnabled(True)
        self.btn_abort.setEnabled(False)

def main():
    app = QApplication(sys.argv)
    w = Odin4GUI()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
