import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QFileDialog, QListWidget, QListWidgetItem,
    QAbstractItemView, QGraphicsDropShadowEffect, QSizeGrip
)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint, Signal, Property, QRect
from PySide6.QtGui import QIcon, QPixmap, QColor, QDragEnterEvent, QDropEvent, QPainter, QAction, QFont, QTransform
from PIL import Image

# --- Custom Widgets ---

class ImageCardWidget(QFrame):
    """Custom widget for the list items, similar to Dash.py cards."""
    # Signal to notify when rotation changes
    rotationChanged = Signal()

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.rotation = 0  # Current rotation in degrees
        self.setObjectName("ImageCard")
        self.setFixedHeight(85)
        self.setStyleSheet("""
            #ImageCard {
                background-color: #2d2d2d;
                border-radius: 8px;
                border: 1px solid #3d3d3d;
            }
            #ImageCard:hover {
                background-color: #353535;
                border: 1px solid #0078d4;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(65, 65)
        self.thumb_label.setStyleSheet("border-radius: 4px; background-color: #1e1e1e;")
        self.update_thumbnail()
        self.thumb_label.setAlignment(Qt.AlignCenter)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        self.name_label = QLabel(os.path.basename(file_path))
        self.name_label.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 11px;")
        
        size = os.path.getsize(file_path) / 1024
        size_label = QLabel(f"{size:.1f} KB")
        size_label.setStyleSheet("color: #888888; font-size: 9px;")
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(size_label)
        info_layout.addStretch()
        
        # Controls Layout (Rotate + Remove)
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(5)
        
        self.btn_rotate_left = QPushButton("⟲")
        self.btn_rotate_right = QPushButton("⟳")
        self.btn_remove = QPushButton("✕")
        
        for btn in [self.btn_rotate_left, self.btn_rotate_right, self.btn_remove]:
            btn.setFixedSize(26, 26)
            btn.setCursor(Qt.PointingHandCursor)
            if btn == self.btn_remove:
                btn.setStyleSheet("""
                    QPushButton { background: transparent; color: #666666; border-radius: 13px; font-weight: bold; }
                    QPushButton:hover { background: #ff4444; color: white; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton { background: #3d3d3d; color: #cccccc; border-radius: 13px; font-size: 14px; border: none; }
                    QPushButton:hover { background: #0078d4; color: white; }
                """)
        
        self.btn_rotate_left.clicked.connect(lambda: self.rotate_image(-90))
        self.btn_rotate_right.clicked.connect(lambda: self.rotate_image(90))
        
        controls_layout.addWidget(self.btn_rotate_left)
        controls_layout.addWidget(self.btn_rotate_right)
        controls_layout.addWidget(self.btn_remove)
        
        layout.addWidget(self.thumb_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addLayout(controls_layout)

    def rotate_image(self, angle):
        self.rotation = (self.rotation + angle) % 360
        self.update_thumbnail()
        self.rotationChanged.emit() # Emit signal to update main preview

    def update_thumbnail(self):
        pixmap = QPixmap(self.file_path)
        if self.rotation != 0:
            transform = QTransform().rotate(self.rotation)
            pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
        
        scaled_pixmap = pixmap.scaled(65, 65, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.thumb_label.setPixmap(scaled_pixmap)

class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None, primary=False):
        super().__init__(text, parent)
        self.primary = primary
        self._color = QColor("#3d3d3d") if not primary else QColor("#0078d4")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(50)
        self.update_style()
        
    def enterEvent(self, event):
        self.animate_color(QColor("#505050") if not self.primary else QColor("#2b88d8"))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_color(QColor("#3d3d3d") if not self.primary else QColor("#0078d4"))
        super().leaveEvent(event)

    def animate_color(self, end_color):
        self.anim = QPropertyAnimation(self, b"backgroundColor")
        self.anim.setDuration(200)
        self.anim.setEndValue(end_color)
        self.anim.start()

    def get_bg_color(self):
        return self._color

    def set_bg_color(self, color):
        self._color = color
        self.update_style()

    def update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color.name()};
                color: white;
                border-radius: 6px;
                padding: 5px 15px;
                font-weight: bold;
                border: none;
                font-size: 11px;
            }}
        """)

    backgroundColor = Property(QColor, get_bg_color, set_bg_color)

class TitleBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(45)
        self.setObjectName("TitleBar")
        self.setStyleSheet("background-color: #1e1e1e; border-top-left-radius: 12px; border-top-right-radius: 12px;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 10, 0)
        
        self.title_label = QLabel("IMAGE MERGER DASH")
        self.title_label.setStyleSheet("color: #0078d4; font-weight: bold; font-size: 13px; letter-spacing: 2px;")
        
        self.btn_min = QPushButton("–")
        self.btn_close = QPushButton("✕")
        
        for btn in [self.btn_min, self.btn_close]:
            btn.setFixedSize(35, 35)
            btn.setCursor(Qt.PointingHandCursor)
            
        self.btn_min.setStyleSheet("QPushButton { background: transparent; color: #888888; font-size: 18px; border: none; } QPushButton:hover { color: white; background: #333333; }")
        self.btn_close.setStyleSheet("QPushButton { background: transparent; color: #888888; font-size: 16px; border: none; } QPushButton:hover { color: white; background: #e81123; border-top-right-radius: 12px; }")
        
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_close)
        
        self.btn_min.clicked.connect(self.parent.showMinimized)
        self.btn_close.clicked.connect(self.parent.close)
        
        self.start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            delta = event.globalPos() - self.start_pos
            self.parent.move(self.parent.pos() + delta)
            self.start_pos = event.globalPos()

class ImageListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAcceptDrops(True)
        self.setSpacing(8)
        self.setObjectName("ImageList")
        self.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 2px dashed #333333;
                border-radius: 10px;
                padding: 10px;
            }
            QListWidget::item {
                background: transparent;
                border: none;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("QListWidget { background-color: #252526; border: 2px dashed #0078d4; border-radius: 10px; padding: 10px; }")
        else:
            super().dragEnterEvent(event)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("QListWidget { background-color: #1e1e1e; border: 2px dashed #333333; border-radius: 10px; padding: 10px; }")
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("QListWidget { background-color: #1e1e1e; border: 2px dashed #333333; border-radius: 10px; padding: 10px; }")
        if event.mimeData().hasUrls():
            files = [u.toLocalFile() for u in event.mimeData().urls()]
            self.parent().add_images(files)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

class ImageMergerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1100, 850)
        
        # Set Application Icon
        icon_path = os.path.join(os.path.dirname(__file__), "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            QApplication.setWindowIcon(QIcon(icon_path))
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main Container
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setStyleSheet("""
            #MainFrame {
                background-color: #121212;
                border-radius: 12px;
                border: 1px solid #252525;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 200))
        self.main_frame.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.main_frame)
        
        self.content_layout = QVBoxLayout(self.main_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Title Bar
        self.title_bar = TitleBar(self)
        self.content_layout.addWidget(self.title_bar)
        
        # Body
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(25, 25, 25, 25)
        body_layout.setSpacing(25)
        
        # Left Side: List and Controls
        left_panel = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        self.drop_label = QLabel("FILA DE IMAGENS")
        self.drop_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.drop_label)
        header_layout.addStretch()
        
        self.count_label = QLabel("0 itens")
        self.count_label.setStyleSheet("color: #0078d4; font-weight: bold; font-size: 11px;")
        header_layout.addWidget(self.count_label)
        left_panel.addLayout(header_layout)
        
        self.image_list = ImageListWidget(self)
        self.image_list.itemSelectionChanged.connect(self.update_preview)
        left_panel.addWidget(self.image_list)
        
        btn_layout = QHBoxLayout()
        self.btn_add = AnimatedButton("＋ ADICIONAR IMAGENS", primary=False)
        self.btn_add.clicked.connect(self.browse_images)
        self.btn_clear = AnimatedButton("🗑 LIMPAR TUDO", primary=False)
        self.btn_clear.clicked.connect(self.clear_list)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_clear)
        left_panel.addLayout(btn_layout)
        
        # Right Side: Preview and Export
        right_panel = QVBoxLayout()
        
        preview_header = QLabel("PRÉ-VISUALIZAÇÃO")
        preview_header.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        right_panel.addWidget(preview_header)
        
        self.preview_container = QFrame()
        self.preview_container.setStyleSheet("background-color: #1e1e1e; border-radius: 10px; border: 1px solid #252525;")
        preview_inner_layout = QVBoxLayout(self.preview_container)
        
        self.preview_label = QLabel("Selecione uma imagem para visualizar")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("color: #444444; font-weight: bold; font-size: 12px;")
        self.preview_label.setMinimumWidth(450)
        preview_inner_layout.addWidget(self.preview_label)
        
        right_panel.addWidget(self.preview_container, 1)
        
        # Export Section
        export_group = QFrame()
        export_group.setFixedHeight(130)
        export_group.setStyleSheet("background-color: #1e1e1e; border-radius: 10px; border: 1px solid #252525; margin-top: 20px;")
        export_layout = QVBoxLayout(export_group)
        export_layout.setContentsMargins(20, 15, 20, 15)
        
        export_title = QLabel("GERAR ARQUIVO FINAL")
        export_title.setStyleSheet("color: #888888; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        export_layout.addWidget(export_title)
        
        export_btns = QHBoxLayout()
        export_btns.setSpacing(15)
        self.btn_jpg = AnimatedButton("STITCH JPG", primary=True)
        self.btn_gif = AnimatedButton("ANIMATED GIF", primary=True)
        self.btn_pdf = AnimatedButton("MULTI-PAGE PDF", primary=True)
        
        self.btn_jpg.clicked.connect(lambda: self.export_images("jpg"))
        self.btn_gif.clicked.connect(lambda: self.export_images("gif"))
        self.btn_pdf.clicked.connect(lambda: self.export_images("pdf"))
        
        export_btns.addWidget(self.btn_jpg)
        export_btns.addWidget(self.btn_gif)
        export_btns.addWidget(self.btn_pdf)
        export_layout.addLayout(export_btns)
        
        right_panel.addWidget(export_group)
        
        body_layout.addLayout(left_panel, 2)
        body_layout.addLayout(right_panel, 3)
        
        self.content_layout.addWidget(body_widget)
        
        # Status Bar
        self.status_bar = QLabel(" Pronto")
        self.status_bar.setStyleSheet("color: #666666; font-size: 10px; padding: 5px; background: #181818; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;")
        self.content_layout.addWidget(self.status_bar)

    def browse_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar Imagens", "", "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if files:
            self.add_images(files)

    def add_images(self, files):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
                item = QListWidgetItem(self.image_list)
                item.setSizeHint(QSize(0, 95))
                
                card = ImageCardWidget(f, self.image_list)
                card.btn_remove.clicked.connect(lambda checked=False, i=item: self.remove_item(i))
                # Connect rotation signal to update preview
                card.rotationChanged.connect(self.update_preview)
                
                self.image_list.addItem(item)
                self.image_list.setItemWidget(item, card)
                
                # Motion animation for the card
                self.animate_card_entry(card)
        
        self.update_count()

    def remove_item(self, item):
        row = self.image_list.row(item)
        self.image_list.takeItem(row)
        self.update_count()
        self.update_preview()

    def animate_card_entry(self, card):
        anim = QPropertyAnimation(card, b"pos")
        anim.setDuration(400)
        anim.setStartValue(QPoint(-100, card.pos().y()))
        anim.setEndValue(card.pos())
        anim.setEasingCurve(QEasingCurve.OutBack)
        anim.start()

    def update_count(self):
        count = self.image_list.count()
        self.count_label.setText(f"{count} itens")
        self.status_bar.setText(f" {count} imagens carregadas")

    def clear_list(self):
        self.image_list.clear()
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("Selecione uma imagem para visualizar")
        self.update_count()

    def update_preview(self):
        selected = self.image_list.selectedItems()
        if selected:
            item_widget = self.image_list.itemWidget(selected[0])
            if item_widget:
                path = item_widget.file_path
                rotation = item_widget.rotation
                pixmap = QPixmap(path)
                
                if rotation != 0:
                    transform = QTransform().rotate(rotation)
                    pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
                
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size() - QSize(40, 40), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                self.preview_label.setText("")
        else:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("Selecione uma imagem para visualizar")

    def export_images(self, fmt):
        count = self.image_list.count()
        if count == 0:
            self.status_bar.setText(" Erro: Nenhuma imagem na fila")
            return
        
        image_data = []
        for i in range(count):
            item = self.image_list.item(i)
            widget = self.image_list.itemWidget(item)
            image_data.append((widget.file_path, widget.rotation))
            
        processed_images = []
        for path, rotation in image_data:
            img = Image.open(path).convert("RGB")
            if rotation != 0:
                # PIL rotates counter-clockwise, so we use -rotation
                img = img.rotate(-rotation, expand=True)
            processed_images.append(img)
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Arquivo", f"resultado.{fmt}", f"Arquivo {fmt.upper()} (*.{fmt})"
        )
        
        if not save_path:
            return
            
        self.status_bar.setText(f" Processando {fmt.upper()}...")
        QApplication.processEvents()
        
        try:
            if fmt == "jpg":
                widths, heights = zip(*(i.size for i in processed_images))
                max_width = max(widths)
                total_height = sum(heights)
                new_im = Image.new('RGB', (max_width, total_height), (255, 255, 255))
                y_offset = 0
                for im in processed_images:
                    new_im.paste(im, (0, y_offset))
                    y_offset += im.size[1]
                new_im.save(save_path, "JPEG", quality=90)
                
            elif fmt == "gif":
                processed_images[0].save(
                    save_path, save_all=True, append_images=processed_images[1:], 
                    duration=500, loop=0, optimize=True
                )
                
            elif fmt == "pdf":
                processed_images[0].save(
                    save_path, save_all=True, append_images=processed_images[1:]
                )
                
            self.status_bar.setText(f" Sucesso! Salvo em: {os.path.basename(save_path)}")
        except Exception as e:
            self.status_bar.setText(f" Erro ao salvar: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set global font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = ImageMergerApp()
    window.show()
    
    # Initial fade-in and slide-up animation
    window.setWindowOpacity(0)
    fade_anim = QPropertyAnimation(window, b"windowOpacity")
    fade_anim.setDuration(800)
    fade_anim.setStartValue(0)
    fade_anim.setEndValue(1)
    fade_anim.setEasingCurve(QEasingCurve.OutCubic)
    fade_anim.start()
    
    sys.exit(app.exec())
