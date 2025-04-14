#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  3 03:36:21 2025

@author: Sasanka
"""

import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QMessageBox, QAction, QToolBar
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtCore import pyqtSignal, QUrl, Qt, QTimer

# Custom QWebEnginePage with a modified user agent and persistent profile support
class MyWebEnginePage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        # Pass the profile to the QWebEnginePage constructor
        super().__init__(profile, parent)
    
    def userAgentForUrl(self, url: QUrl) -> str:
        # Use a modern desktop user agent string
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
               "AppleWebKit/537.36 (KHTML, like Gecko) " \
               "Chrome/105.0.5195.102 Safari/537.36"

# Custom WebView class to handle context menu
class MyWebView(QWebEngineView):
    saveSelectedText = pyqtSignal(str)
    
    def contextMenuEvent(self, event):
        menu = self.page().createStandardContextMenu()
        selected_text = self.selectedText()
        if selected_text:
            action = QAction("Save selected text", self)
            action.triggered.connect(lambda: self.saveSelectedText.emit(selected_text))
            menu.addAction(action)
        menu.exec_(event.globalPos())

# Main browser window
class BrowserWindow(QMainWindow):
    def __init__(self, csv_file_path):
        super().__init__()
        self.setWindowTitle("Rudimentary Web Browser")
        self.setGeometry(100, 100, 1200, 800)  # Larger window size

        # Set up toolbar
        self.toolbar = QToolBar()
        self.toolbar.setFixedHeight(30)
        self.addToolBar(self.toolbar)

        self.reload_btn = QPushButton("Reload")
        self.reload_btn.setEnabled(True)
        self.next_btn = QPushButton("Next")
        self.next_btn.setEnabled(False)
        self.status_label = QLabel("Loading CSV...")

        self.toolbar.addWidget(self.reload_btn)
        self.toolbar.addWidget(self.next_btn)
        self.toolbar.addWidget(self.status_label)

        # Create web view
        self.webview = MyWebView()

        # Enable JavaScript and plugins for Cloudflare challenge scripts
        self.webview.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        self.webview.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)

        # Create a persistent profile for cookies and cache
        profile = QWebEngineProfile("Default", self)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        profile.setHttpCacheType(QWebEngineProfile.DiskHttpCache)

        # Create custom page with the persistent profile and set it for the web view
        page = MyWebEnginePage(profile, self.webview)
        self.webview.setPage(page)

        self.setCentralWidget(self.webview)

        # Connect signals and slots
        self.reload_btn.clicked.connect(self.webview.reload)
        self.next_btn.clicked.connect(self.next_link)
        self.webview.saveSelectedText.connect(self.on_save_selected_text)
        self.webview.loadFinished.connect(self.handle_load_finished)

        self.csv_data = None
        self.current_index = -1
        self.csv_file_path = None

        self.load_csv(csv_file_path)

    def handle_load_finished(self, ok):
        current_url = self.webview.url().toString()
        if "challenges.cloudflare.com" in current_url:
            # If still on the Cloudflare challenge page, wait a few seconds then reload.
            QTimer.singleShot(3000, self.webview.reload)

    def load_csv(self, file_path):
        try:
            self.csv_data = pd.read_csv(file_path)
            if "Source" not in self.csv_data.columns:
                raise ValueError("CSV file must have a 'Source' column")
            if "SelectedText" not in self.csv_data.columns:
                self.csv_data["SelectedText"] = ""
            if "Check" not in self.csv_data.columns:
                self.csv_data["Check"] = 0  # Mark unprocessed links with 0
            self.csv_file_path = file_path
            self.find_next_unprocessed()
            self.load_current_url()
            self.status_label.setText(f"Loaded {len(self.csv_data)} links")
            self.next_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV: {e}")
            self.status_label.setText("Failed to load CSV")
            self.webview.setUrl(QUrl("about:blank"))

    def find_next_unprocessed(self):
        for i in range(self.current_index + 1, len(self.csv_data)):
            if self.csv_data.at[i, "Check"] == 0:
                self.current_index = i
                return
        self.current_index = len(self.csv_data)  # No more unprocessed links

    def load_current_url(self):
        if self.csv_data is None or self.csv_data.empty:
            self.webview.setUrl(QUrl("about:blank"))
            self.status_label.setText("No links loaded")
            self.next_btn.setEnabled(False)
        elif self.current_index < len(self.csv_data):
            url = self.csv_data.iloc[self.current_index]["Source"]
            self.webview.setUrl(QUrl(url))
            self.status_label.setText(f"Viewing link {self.current_index + 1} of {len(self.csv_data)}")
            self.next_btn.setEnabled(True)
        else:
            self.status_label.setText("All links processed")
            self.next_btn.setEnabled(False)

    def next_link(self):
        self.find_next_unprocessed()
        self.load_current_url()

    def on_save_selected_text(self, text):
        if self.csv_data is not None and 0 <= self.current_index < len(self.csv_data):
            self.csv_data.at[self.current_index, "SelectedText"] = text
            self.csv_data.at[self.current_index, "Check"] = 1  # Mark as processed
            self.write_csv()

    def write_csv(self):
        if self.csv_file_path and self.csv_data is not None:
            try:
                self.csv_data.to_csv(self.csv_file_path, index=False)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to write CSV: {e}")

    def closeEvent(self, event):
        self.write_csv()
        event.accept()

if __name__ == "__main__":
    # On macOS, force software rendering if needed
    from PyQt5.QtCore import Qt
    QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)
    
    app = QApplication(sys.argv)
    if len(sys.argv) < 2:
        QMessageBox.critical(None, "Error", "Please provide a CSV file path as a command-line argument.")
        sys.exit(1)
    csv_file_path = sys.argv[1]
    window = BrowserWindow(csv_file_path)
    window.show()
    sys.exit(app.exec_())
