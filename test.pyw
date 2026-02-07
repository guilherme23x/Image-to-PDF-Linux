import sys
import os
import pathlib
import threading
from PIL import Image
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QFileDialog, QListWidget, QListWidgetItem,
    QAbstractItemView, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint, Signal, Property
from PySide6.QtGui import QIcon, QPixmap, QColor, QDragEnterEvent, QDropEvent, QTransform, QFont

# --- CONFIGURAÇÃO VISUAL CIANO HIGH-TECH ---
BG_COLOR = "#080808"
ACCENT_COLOR = "#00F0FF"
TEXT_PRIMARY = "#E0E0E0"
TEXT_DIM = "#555555"
INPUT_BG = "#111111"

STYLE_SHEET = f"""
    QWidget {{
        background-color: {BG_COLOR};
        color: {TEXT_PRIMARY};
        font-family: 'Segoe UI', sans-serif;
    }}
    QLabel#SectionTitle {{
        background-color: transparent;
        color: {TEXT_DIM};
        font-size: 10px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 2px;
    }}
    QListWidget {{
        background-color: {INPUT_BG};
        border: 1px solid #222;
        border-radius: 4px;
        outline: none;
    }}
    QListWidget::item {{
        background: transparent;
        border: none;
        padding: 5px;
    }}
    QPushButton#ActionBtn {{
        background-color: transparent;
        color: {ACCENT_COLOR};
        border: 1px solid {ACCENT_COLOR};
        border-radius: 2px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
        height: 45px;
        font-size: 11px;
    }}
    QPushButton#ActionBtn:hover {{
        background-color: {ACCENT_COLOR};
        color: #000;
    }}
    QPushButton#NavBtn {{
        background-color: #111;
        color: {TEXT_PRIMARY};
        border: 1px solid #333;
        border-radius: 2px;
        padding: 8px;
        font-size: 10px;
        font-weight: bold;
    }}
    QPushButton#NavBtn:hover {{
        border-color: {ACCENT_COLOR};
    }}
"""

class ImageCardWidget(QFrame):
    rotationChanged = Signal()

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.rotation = 0
        self.setFixedHeight(85)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #0d0d0d;
                border: 1px solid #1a1a1a;
                border-radius: 4px;
            }}
            QFrame:hover {{
                border-color: {ACCENT_COLOR};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(65, 65)
        self.thumb_label.setStyleSheet("background-color: #050505; border-radius: 2px;")
        self.update_thumbnail()
        
        info_layout = QVBoxLayout()
        self.name_label = QLabel(os.path.basename(file_path))
        self.name_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px; font-weight: bold;")
        
        size = os.path.getsize(file_path) / 1024
        self.size_label = QLabel(f"{size:.1f} KB")
        self.size_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px;")
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.size_label)
        info_layout.addStretch()
        
        controls = QHBoxLayout()
        controls.setSpacing(4)
        
        self.btn_rot_l = self._create_ctrl_btn("⟲")
        self.btn_rot_r = self._create_ctrl_btn("⟳")
        self.btn_del = self._create_ctrl_btn("✕", is_del=True)
        
        self.btn_rot_l.clicked.connect(lambda: self.rotate_image(-90))
        self.btn_rot_r.clicked.connect(lambda: self.rotate_image(90))
        
        controls.addWidget(self.btn_rot_l)
        controls.addWidget(self.btn_rot_r)
        controls.addWidget(self.btn_del)
        
        layout.addWidget(self.thumb_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addLayout(controls)

    def _create_ctrl_btn(self, text, is_del=False):
        btn = QPushButton(text)
        btn.setFixedSize(24, 24)
        color = "#ff4444" if is_del else ACCENT_COLOR
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: #555;
                border: 1px solid #333;
                border-radius: 2px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {color};
                border-color: {color};
            }}
        """)
        return btn

    def rotate_image(self, angle):
        self.rotation = (self.rotation + angle) % 360
        self.update_thumbnail()
        self.rotationChanged.emit()

    def update_thumbnail(self):
        pixmap = QPixmap(self.file_path)
        if self.rotation != 0:
            pixmap = pixmap.transformed(QTransform().rotate(self.rotation), Qt.SmoothTransformation)
        self.thumb_label.setPixmap(pixmap.scaled(65, 65, Qt.KeepAspectRatio, Qt.SmoothTransformation))

class ImageListWidget(QListWidget):
    filesDropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(f"border: 1px solid {ACCENT_COLOR}; background-color: #0c0c0c;")
        else:
            super().dragEnterEvent(event)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        if event.mimeData().hasUrls():
            files = [u.toLocalFile() for u in event.mimeData().urls()]
            self.filesDropped.emit(files)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

class ImageMergerCyanEngine(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Merger Cyan Engine")
        self.setMinimumSize(1100, 800)
        self.setStyleSheet(STYLE_SHEET)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(25)

        # Header
        header = QVBoxLayout()
        t1 = QLabel("Image Merger Dash")
        t1.setStyleSheet(f"font-size: 26px; font-weight: 200; letter-spacing: 12px; color: {ACCENT_COLOR};")
        t2 = QLabel("HIGH-TECH IMAGE PROCESSING & STITCHING")
        t2.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; letter-spacing: 4px;")
        header.addWidget(t1)
        header.addWidget(t2)
        main_layout.addLayout(header)

        # Grid de Conteúdo
        content = QHBoxLayout()
        content.setSpacing(40)

        # Coluna Esquerda: Lista
        left_col = QVBoxLayout()
        l1 = QLabel("Fila de Processamento")
        l1.setObjectName("SectionTitle")
        
        self.image_list = ImageListWidget()
        self.image_list.filesDropped.connect(self.add_images)
        self.image_list.itemSelectionChanged.connect(self.update_preview)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("ADICIONAR")
        self.btn_add.setObjectName("NavBtn")
        self.btn_add.clicked.connect(self.browse_images)
        
        self.btn_clear = QPushButton("LIMPAR")
        self.btn_clear.setObjectName("NavBtn")
        self.btn_clear.clicked.connect(self.clear_list)
        
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_clear)

        left_col.addWidget(l1)
        left_col.addWidget(self.image_list)
        left_col.addLayout(btn_row)

        # Coluna Direita: Preview e Export
        right_col = QVBoxLayout()
        
        l2 = QLabel("Monitor de Preview")
        l2.setObjectName("SectionTitle")
        
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet("background-color: #050505; border: 1px solid #111; border-radius: 4px;")
        preview_layout = QVBoxLayout(self.preview_frame)
        
        self.preview_label = QLabel("Aguardando seleção...")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; text-transform: uppercase;")
        preview_layout.addWidget(self.preview_label)

        # Export Group
        export_box = QFrame()
        export_box.setStyleSheet("background-color: #0c0c0c; border: 1px solid #1a1a1a; border-radius: 4px;")
        export_layout = QVBoxLayout(export_box)
        
        l3 = QLabel("Gerar Saída Consolidada")
        l3.setObjectName("SectionTitle")
        
        btns_export = QHBoxLayout()
        self.btn_jpg = QPushButton("STITCH JPG")
        self.btn_gif = QPushButton("ANIMATED GIF")
        self.btn_pdf = QPushButton("MULTI-PAGE PDF")
        
        for b in [self.btn_jpg, self.btn_gif, self.btn_pdf]:
            b.setObjectName("ActionBtn")
            btns_export.addWidget(b)
        
        self.btn_jpg.clicked.connect(lambda: self.export_images("jpg"))
        self.btn_gif.clicked.connect(lambda: self.export_images("gif"))
        self.btn_pdf.clicked.connect(lambda: self.export_images("pdf"))

        export_layout.addWidget(l3)
        export_layout.addLayout(btns_export)

        right_col.addWidget(l2)
        right_col.addWidget(self.preview_frame, 1)
        right_col.addWidget(export_box)

        content.addLayout(left_col, 2)
        content.addLayout(right_col, 3)
        main_layout.addLayout(content)

        # Footer
        self.status_bar = QLabel("SYSTEM READY")
        self.status_bar.setAlignment(Qt.AlignCenter)
        self.status_bar.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; letter-spacing: 2px;")
        main_layout.addWidget(self.status_bar)

    def browse_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Selecionar Imagens", "", "Imagens (*.png *.jpg *.jpeg *.webp)")
        if files: self.add_images(files)

    def add_images(self, files):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                item = QListWidgetItem(self.image_list)
                item.setSizeHint(QSize(0, 95))
                card = ImageCardWidget(f, self.image_list)
                card.btn_del.clicked.connect(lambda _, i=item: self.remove_item(i))
                card.rotationChanged.connect(self.update_preview)
                self.image_list.addItem(item)
                self.image_list.setItemWidget(item, card)
        self.status_bar.setText(f"CARREGADOS: {self.image_list.count()} ITENS")

    def remove_item(self, item):
        self.image_list.takeItem(self.image_list.row(item))
        self.update_preview()

    def clear_list(self):
        self.image_list.clear()
        self.update_preview()

    def update_preview(self):
        selected = self.image_list.selectedItems()
        if selected:
            card = self.image_list.itemWidget(selected[0])
            pixmap = QPixmap(card.file_path)
            if card.rotation != 0:
                pixmap = pixmap.transformed(QTransform().rotate(card.rotation), Qt.SmoothTransformation)
            self.preview_label.setPixmap(pixmap.scaled(self.preview_frame.size() - QSize(40,40), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.preview_label.setText("")
        else:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("AGUARDANDO SELEÇÃO...")

    def export_images(self, fmt):
        count = self.image_list.count()
        if count == 0: return
        
        image_data = []
        for i in range(count):
            w = self.image_list.itemWidget(self.image_list.item(i))
            image_data.append((w.file_path, w.rotation))
            
        processed = []
        for path, rot in image_data:
            img = Image.open(path).convert("RGB")
            if rot != 0: img = img.rotate(-rot, expand=True)
            processed.append(img)
        
        path_save, _ = QFileDialog.getSaveFileName(self, "Salvar", f"export.{fmt}", f"*{fmt}")
        if not path_save: return
            
        try:
            self.status_bar.setText(f"PROCESSANDO {fmt.upper()}...")
            QApplication.processEvents()
            
            if fmt == "jpg":
                w_max = max(i.size[0] for i in processed)
                h_total = sum(i.size[1] for i in processed)
                new_img = Image.new('RGB', (w_max, h_total), (255, 255, 255))
                y = 0
                for im in processed:
                    new_img.paste(im, (0, y))
                    y += im.size[1]
                new_img.save(path_save, "JPEG", quality=90)
            elif fmt == "gif":
                processed[0].save(path_save, save_all=True, append_images=processed[1:], duration=500, loop=0)
            elif fmt == "pdf":
                processed[0].save(path_save, save_all=True, append_images=processed[1:])
                
            self.status_bar.setText(f"SUCESSO: {os.path.basename(path_save)}")
        except Exception as e:
            self.status_bar.setText(f"ERRO: {str(e)[:30]}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ImageMergerCyanEngine()
    win.show()
    sys.exit(app.exec())
