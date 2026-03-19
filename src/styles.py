THEME_TEMPLATE = """
QMainWindow, QDialog {{
    background-color: {bg};
    color: {text};
}}
QWidget {{
    background-color: {bg};
    color: {text};
    font-family: "Segoe UI", "맑은 고딕", sans-serif;
    font-size: 13px;
}}
QMenuBar {{
    background-color: {bg_alt};
    color: {text};
    border-bottom: 1px solid {border};
    padding: 2px;
}}
QMenuBar::item:selected {{
    background-color: {surface_hover};
    border-radius: 4px;
}}
QMenu {{
    background-color: {bg};
    color: {text};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item:selected {{
    background-color: {surface_hover};
    border-radius: 4px;
}}
QToolBar {{
    background-color: {bg_alt};
    border-bottom: 1px solid {border};
    spacing: 4px;
    padding: 4px 8px;
}}
QToolButton {{
    background-color: transparent;
    color: {text};
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
}}
QToolButton:hover {{
    background-color: {surface};
    border: 1px solid {surface_hover};
}}
QToolButton:pressed {{
    background-color: {surface_hover};
}}
QPushButton {{
    background-color: {accent};
    color: {accent_text};
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 600;
    min-height: 20px;
}}
QPushButton:hover {{
    background-color: {accent_hover};
}}
QPushButton:pressed {{
    background-color: {accent};
}}
QPushButton:disabled {{
    background-color: {surface_hover};
    color: {text_dim};
}}
QPushButton#secondaryBtn {{
    background-color: {surface};
    color: {text};
}}
QPushButton#secondaryBtn:hover {{
    background-color: {surface_hover};
}}
QPushButton#dangerBtn {{
    background-color: {danger};
    color: {accent_text};
}}
QPushButton#dangerBtn:hover {{
    background-color: {danger_hover};
}}
QLabel {{
    background-color: transparent;
    color: {text};
}}
QLabel#titleLabel {{
    font-size: 15px;
    font-weight: 700;
    color: {text};
}}
QLabel#subtitleLabel {{
    font-size: 11px;
    color: {text_dim};
}}
QLabel#accentLabel {{
    color: {accent};
    font-weight: 600;
}}
QSlider::groove:horizontal {{
    height: 6px;
    background-color: {surface};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background-color: {accent};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}
QSlider::sub-page:horizontal {{
    background-color: {accent};
    border-radius: 3px;
}}
QSpinBox, QComboBox, QLineEdit {{
    background-color: {surface};
    color: {text};
    border: 1px solid {surface_hover};
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 20px;
}}
QSpinBox:focus, QComboBox:focus, QLineEdit:focus {{
    border: 1px solid {accent};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {bg};
    color: {text};
    border: 1px solid {border};
    selection-background-color: {surface_hover};
}}
QTabWidget::pane {{
    border: 1px solid {border};
    border-radius: 6px;
    background-color: {bg};
}}
QTabBar::tab {{
    background-color: {bg_alt};
    color: {text_dim};
    border: 1px solid {border};
    border-bottom: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}
QTabBar::tab:selected {{
    background-color: {bg};
    color: {text};
    border-bottom: 2px solid {accent};
}}
QTabBar::tab:hover:!selected {{
    background-color: {surface};
    color: {text};
}}
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:vertical {{
    background-color: {bg_alt};
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background-color: {surface_hover};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {text_dim};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background-color: {bg_alt};
    height: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background-color: {surface_hover};
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {text_dim};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QProgressBar {{
    background-color: {surface};
    border-radius: 4px;
    text-align: center;
    color: {text};
    height: 8px;
}}
QProgressBar::chunk {{
    background-color: {accent};
    border-radius: 4px;
}}
QStatusBar {{
    background-color: {bg_alt};
    color: {text_dim};
    border-top: 1px solid {border};
}}
QSplitter::handle {{
    background-color: {border};
    width: 2px;
}}
QGroupBox {{
    border: 1px solid {border};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {accent};
}}
QCheckBox {{
    spacing: 8px;
    color: {text};
    background: transparent;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {surface_hover};
    background-color: {surface};
}}
QCheckBox::indicator:checked {{
    background-color: {accent};
    border-color: {accent};
}}
QRadioButton {{
    spacing: 8px;
    color: {text};
    background: transparent;
}}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid {surface_hover};
    background-color: {surface};
}}
QRadioButton::indicator:checked {{
    background-color: {accent};
    border-color: {accent};
}}
QListWidget {{
    background-color: {bg_alt};
    border: 1px solid {border};
    border-radius: 6px;
    outline: none;
}}
QListWidget::item {{
    padding: 6px;
    border-bottom: 1px solid {border};
    border-radius: 0;
}}
QListWidget::item:selected {{
    background-color: {surface};
    color: {text};
}}
QListWidget::item:hover:!selected {{
    background-color: {bg};
}}
QFrame#convertPanel {{
    background-color: {bg_alt};
    border-top: 1px solid {border};
}}
"""

THEME_COLORS = {
    "Catppuccin Mocha": {
        "bg": "#1e1e2e", "bg_alt": "#181825", "surface": "#313244",
        "surface_hover": "#45475a", "text": "#cdd6f4", "text_dim": "#6c7086",
        "accent": "#89b4fa", "accent_hover": "#74c7ec", "accent_text": "#1e1e2e",
        "danger": "#f38ba8", "danger_hover": "#eba0ac", "border": "#313244",
    },
    "Catppuccin Latte": {
        "bg": "#eff1f5", "bg_alt": "#e6e9ef", "surface": "#ccd0da",
        "surface_hover": "#bcc0cc", "text": "#4c4f69", "text_dim": "#9ca0b0",
        "accent": "#1e66f5", "accent_hover": "#2a7bf5", "accent_text": "#ffffff",
        "danger": "#d20f39", "danger_hover": "#e0334f", "border": "#ccd0da",
    },
    "Dracula": {
        "bg": "#282a36", "bg_alt": "#21222c", "surface": "#44475a",
        "surface_hover": "#6272a4", "text": "#f8f8f2", "text_dim": "#6272a4",
        "accent": "#bd93f9", "accent_hover": "#caa9fa", "accent_text": "#282a36",
        "danger": "#ff5555", "danger_hover": "#ff6e6e", "border": "#44475a",
    },
    "Nord": {
        "bg": "#2e3440", "bg_alt": "#272c36", "surface": "#3b4252",
        "surface_hover": "#434c5e", "text": "#eceff4", "text_dim": "#4c566a",
        "accent": "#88c0d0", "accent_hover": "#8fbcbb", "accent_text": "#2e3440",
        "danger": "#bf616a", "danger_hover": "#d08770", "border": "#3b4252",
    },
    "Solarized Dark": {
        "bg": "#002b36", "bg_alt": "#073642", "surface": "#073642",
        "surface_hover": "#586e75", "text": "#839496", "text_dim": "#586e75",
        "accent": "#268bd2", "accent_hover": "#2aa198", "accent_text": "#fdf6e3",
        "danger": "#dc322f", "danger_hover": "#cb4b16", "border": "#073642",
    },
    "Gruvbox Dark": {
        "bg": "#282828", "bg_alt": "#1d2021", "surface": "#3c3836",
        "surface_hover": "#504945", "text": "#ebdbb2", "text_dim": "#928374",
        "accent": "#fabd2f", "accent_hover": "#fe8019", "accent_text": "#282828",
        "danger": "#fb4934", "danger_hover": "#cc241d", "border": "#3c3836",
    },
}

THEME_NAMES = list(THEME_COLORS.keys())


def get_theme_stylesheet(theme_name):
    colors = THEME_COLORS.get(theme_name, THEME_COLORS["Catppuccin Mocha"])
    return THEME_TEMPLATE.format(**colors)


def get_theme_names():
    return list(THEME_NAMES)
