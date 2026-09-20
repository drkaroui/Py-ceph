import ctypes
import math
import os
import sys
from datetime import datetime

import cv2
from fpdf import FPDF
import numpy as np
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)



def get_resource_path(relative_path):
  """Obtenir le chemin absolu des ressources, fonctionne pour dev et PyInstaller."""
  try:
    # PyInstaller crée un dossier temporaire et stocke le chemin dans _MEIPASS
    base_path = sys._MEIPASS
  except AttributeError:
    base_path = os.path.abspath(".")

  return os.path.join(base_path, relative_path)

try:
  ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
      "monapp.ceph.1.0"
  )
except Exception:
  pass

# ---------------- DEFINITION COMPLETE DES POINTS (STEINER + TWEED) ----------------
LANDMARKS_DEF = [
    ("S", "Sella (Centre de la selle turcique)"),
    ("N", "Nasion (Suture naso-frontale)"),
    ("A", "Point A (Subspinale maxillaire)"),
    ("B", "Point B (Supramentale mandibulaire)"),
    ("Pog", "Pogonion (Point le plus antérieur du menton)"),
    ("Gn", "Gnathion (Point le plus antero-inférieur du menton)"),
    ("Go", "Gonion (Angle de la mandibule)"),
    ("1u", "Apex de l'incisive supérieure"),
    ("1u_edge", "Bord incisif supérieur"),
    ("1l", "Apex de l'incisive inférieure"),
    ("1l_edge", "Bord incisif inférieur"),
    ("ANS", "Épine Nasale Antérieure"),
    ("PNS", "Épine Nasale Postérieure"),
    # Points spécifiques pour l'analyse de Tweed
    ("Po", "Porion (Bord supérieur du méat acoustique externe)"),
    ("Or", "Orbitale (Point le plus inférieur du rebord orbitaire)"),
]


class CephGraphicView(QLabel):

    """Canvas d'affichage de la télé-radiographie avec gestion des tracés Steiner et Tweed."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.image_np_orig = None
        self.image_np_adjusted = None
        self.pixmap_orig = None
        self.landmarks = {}

        self.dragging_landmark = None
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "border: 2px dashed #444; background-color: #1e1e1e;"
        )

        self.setMinimumSize(400, 400)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    def load_image(self, file_path):
        self.image_np_orig = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if self.image_np_orig is None:
            return False

        self.image_np_adjusted = self.image_np_orig.copy()
        self.landmarks.clear()
        self.dragging_landmark = None
        self.update_pixmap_from_np()
        return True

    def apply_contrast_brightness(self, alpha=1.0, beta=0):
        if self.image_np_orig is None:
            return

        self.image_np_adjusted = cv2.convertScaleAbs(
            self.image_np_orig, alpha=alpha, beta=beta
        )
        self.update_pixmap_from_np()

    def update_pixmap_from_np(self):
        if self.image_np_adjusted is None:
            return

        height, width = self.image_np_adjusted.shape
        bytes_per_line = width
        q_img = QImage(
            self.image_np_adjusted.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_Grayscale8,
        )
        self.pixmap_orig = QPixmap.fromImage(q_img)
        self.update_canvas()

    def get_real_coords(self, event_pos):
        pixmap_curr = self.pixmap()
        if pixmap_curr is None or self.pixmap_orig is None:
            return None

        rect = self.contentsRect()
        pix_size = pixmap_curr.size()

        offset_x = (rect.width() - pix_size.width()) / 2
        offset_y = (rect.height() - pix_size.height()) / 2

        click_x = event_pos.x() - offset_x
        click_y = event_pos.y() - offset_y

        if (
            0 <= click_x <= pix_size.width()
            and 0 <= click_y <= pix_size.height()
        ):
            scale_x = self.pixmap_orig.width() / pix_size.width()
            scale_y = self.pixmap_orig.height() / pix_size.height()
            return click_x * scale_x, click_y * scale_y
        return None

    def find_landmark_near(self, real_x, real_y, tolerance_px=10):
        if self.pixmap_orig is None:
            return None

        scale_x = self.pixmap().width() / self.pixmap_orig.width()
        for key, (rx, ry) in self.landmarks.items():
            dist = math.hypot((rx - real_x) * scale_x, (ry - real_y) * scale_x)
            if dist <= tolerance_px:
                return key
        return None

    def mousePressEvent(self, event):
        if self.pixmap_orig is None:
            return

        coords = self.get_real_coords(event.position())
        if coords is None:
            return

        real_x, real_y = coords
        clicked_lm = self.find_landmark_near(real_x, real_y)

        # Clic Droit -> Supprimer
        if event.button() == Qt.MouseButton.RightButton:
            if clicked_lm:
                menu = QMenu(self)
                action_delete = QAction(
                    f"❌ Supprimer le point [{clicked_lm}]", self
                )
                action_delete.triggered.connect(
                    lambda: self.delete_landmark(clicked_lm)
                )
                menu.addAction(action_delete)
                menu.exec(event.globalPosition().toPoint())
            return

        # Clic Gauche -> Ajouter ou Déplacer
        if event.button() == Qt.MouseButton.LeftButton:
            shift_pressed = bool(
                event.modifiers() & Qt.KeyboardModifier.ShiftModifier
            )

            if clicked_lm and not shift_pressed:
                self.dragging_landmark = clicked_lm
            else:
                next_key = self.parent_app.get_next_missing_landmark()
                if next_key:
                    self.landmarks[next_key] = (real_x, real_y)
                    self.parent_app.on_landmarks_updated()
                    self.update_canvas()

    def mouseMoveEvent(self, event):
        if self.dragging_landmark and self.pixmap_orig:
            coords = self.get_real_coords(event.position())
            if coords:
                self.landmarks[self.dragging_landmark] = coords
                self.update_canvas()
                self.parent_app.calculate_cephalometric_angles()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging_landmark = None

    def delete_landmark(self, key):
        if key in self.landmarks:
            del self.landmarks[key]
            self.parent_app.on_landmarks_updated()
            self.update_canvas()

    def update_canvas(self):
        if self.pixmap_orig is None:
            return

        scaled_pixmap = self.pixmap_orig.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        painter = QPainter(scaled_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        scale_x = scaled_pixmap.width() / self.pixmap_orig.width()
        scale_y = scaled_pixmap.height() / self.pixmap_orig.height()

        def get_pt(key):
            if key in self.landmarks:
                x, y = self.landmarks[key]
                return QPointF(x * scale_x, y * scale_y)
            return None

        # --- Lignes Steiner (Vert) ---
        pen_steiner = QPen(QColor(0, 230, 118), 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen_steiner)

        steiner_lines = [
            ("S", "N"),
            ("N", "A"),
            ("N", "B"),
            ("N", "Gn"),
            ("Go", "Gn"),
            ("1u", "1u_edge"),
            ("1l", "1l_edge"),
            ("ANS", "PNS"),
        ]
        for k1, k2 in steiner_lines:
            p1, p2 = get_pt(k1), get_pt(k2)
            if p1 and p2:
                painter.drawLine(p1, p2)

        # --- Lignes Triangle de Tweed (Jaune/Orange) ---
        pen_tweed = QPen(QColor(255, 170, 0), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen_tweed)

        tweed_lines = [
            ("Po", "Or"),  # Plan de Francfort
            ("Go", "Gn"),  # Plan Mandibulaire
            ("1l", "1l_edge"),  # Axe Incisive Inférieure
        ]
        for k1, k2 in tweed_lines:
            p1, p2 = get_pt(k1), get_pt(k2)
            if p1 and p2:
                painter.drawLine(p1, p2)

        # Dessin des points
        for key, (rx, ry) in self.landmarks.items():
            px, py = rx * scale_x, ry * scale_y

            if key == self.dragging_landmark:
                pen_point = QPen(QColor(255, 235, 59), 8)
            else:
                pen_point = QPen(QColor(255, 52, 100), 6)

            painter.setPen(pen_point)
            painter.drawPoint(QPointF(px, py))

            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.drawText(int(px) + 5, int(py) - 5, key)

        painter.end()
        super().setPixmap(scaled_pixmap)


# ---------------- APPLICATION PRINCIPALE ----------------
class CephalometricApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Py-ceph - Analyse Céphalométrique de Steiner & Tweed (Dr.Karoui.Abdelfetteh)"
        )
        icon_path = get_resource_path("braces.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(50, 50, 1600, 950)

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # ==================== PANNEAU GAUCHE ====================
        left_layout = QVBoxLayout()
        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        # 1. Informations Patient
        grp_patient = QGroupBox("Informations Patient")
        lay_patient = QHBoxLayout()

        lbl_nom = QLabel("Nom :")
        self.txt_nom = QLineEdit()
        self.txt_nom.setPlaceholderText("Ex: Dupont")

        lbl_prenom = QLabel("Prénom :")
        self.txt_prenom = QLineEdit()
        self.txt_prenom.setPlaceholderText("Ex: Jean")

        lay_patient.addWidget(lbl_nom)
        lay_patient.addWidget(self.txt_nom)
        lay_patient.addWidget(lbl_prenom)
        lay_patient.addWidget(self.txt_prenom)

        grp_patient.setLayout(lay_patient)
        left_layout.addWidget(grp_patient)

        # 2. Chargement & Réglages Image
        grp_img_ctrl = QGroupBox("Télé-radiographie & Réglages Image")
        lay_img_ctrl = QHBoxLayout()

        self.btn_load_img = QPushButton("Charger Radio (.png, .jpg, .bmp)")
        self.btn_load_img.setStyleSheet(
            "background-color: #0288d1; color: white; font-weight: bold;"
            " padding: 8px;"
        )
        self.btn_load_img.clicked.connect(self.load_cephalogram)
        lay_img_ctrl.addWidget(self.btn_load_img)

        self.lbl_contrast = QLabel("Contraste : 1.0")
        self.slider_contrast = QSlider(Qt.Orientation.Horizontal)
        self.slider_contrast.setRange(5, 30)
        self.slider_contrast.setValue(10)
        self.slider_contrast.valueChanged.connect(self.on_image_adjust_changed)

        lay_img_ctrl.addWidget(self.lbl_contrast)
        lay_img_ctrl.addWidget(self.slider_contrast)

        self.lbl_brightness = QLabel("Luminosité : 0")
        self.slider_brightness = QSlider(Qt.Orientation.Horizontal)
        self.slider_brightness.setRange(-100, 100)
        self.slider_brightness.setValue(0)
        self.slider_brightness.valueChanged.connect(
            self.on_image_adjust_changed
        )

        lay_img_ctrl.addWidget(self.lbl_brightness)
        lay_img_ctrl.addWidget(self.slider_brightness)

        self.btn_reset_adjust = QPushButton("Réinitialiser")
        self.btn_reset_adjust.clicked.connect(self.reset_image_adjustments)
        lay_img_ctrl.addWidget(self.btn_reset_adjust)

        grp_img_ctrl.setLayout(lay_img_ctrl)
        left_layout.addWidget(grp_img_ctrl)

        # 3. Canvas d'affichage
        self.canvas = CephGraphicView(self)
        left_layout.addWidget(self.canvas)

        main_layout.addWidget(left_widget)

        # ==================== PANNEAU DROIT ====================
        right_layout = QVBoxLayout()
        right_widget = QWidget()
        right_widget.setFixedWidth(560)
        right_widget.setLayout(right_layout)

        # 1. Placement des Points
        grp_pts = QGroupBox("1. Placement des Points Anatomiques")
        lay_pts = QVBoxLayout()

        self.lbl_current_target = QLabel(
            "Charger une radiographie pour commencer."
        )
        self.lbl_current_target.setStyleSheet(
            "color: #ff9800; font-weight: bold;"
        )
        self.lbl_current_target.setWordWrap(True)
        lay_pts.addWidget(self.lbl_current_target)

        lbl_tip = QLabel(
            "💡 <i>Maintenez <b>Shift</b> en cliquant pour forcer l'ajout d'un"
            " point très proche d'un autre.</i>"
        )
        lbl_tip.setWordWrap(True)
        lbl_tip.setStyleSheet("color: #aaa; font-size: 11px;")
        lay_pts.addWidget(lbl_tip)

        self.list_landmarks = QListWidget()
        self.list_landmarks.setFixedHeight(100)
        lay_pts.addWidget(self.list_landmarks)

        lay_btn_pts = QHBoxLayout()
        self.btn_delete_selected = QPushButton("🗑️ Supprimer sélection")
        self.btn_delete_selected.clicked.connect(
            self.delete_selected_from_list
        )
        lay_btn_pts.addWidget(self.btn_delete_selected)

        self.btn_reset_pts = QPushButton("Réinitialiser tout")
        self.btn_reset_pts.clicked.connect(self.reset_landmarks)
        lay_btn_pts.addWidget(self.btn_reset_pts)

        lay_pts.addLayout(lay_btn_pts)
        grp_pts.setLayout(lay_pts)
        right_layout.addWidget(grp_pts)

        # 2. Résultats des Mesures & Diagnostic (Steiner & Tweed)
        grp_analysis = QGroupBox(
            "2. Analyse & Diagnostic ODF (Steiner + Tweed)"
        )
        lay_analysis = QVBoxLayout()

        self.all_measures = [
            # Steiner
            ("SNA (Steiner)", "82° ± 2°"),
            ("SNB (Steiner)", "80° ± 2°"),
            ("ANB (Steiner)", "2° ± 2°"),
            ("SND (Steiner)", "76° ± 2°"),
            ("GoGn - SN", "32° ± 5°"),
            ("1u à NA (Angle)", "22°"),
            ("1u à NA (Distance)", "4 mm"),
            ("1l à NB (Angle)", "25°"),
            ("1l à NB (Distance)", "4 mm"),
            ("Inter-incisif (1u/1l)", "131°"),
            ("Pog à NB (Distance)", "2 mm"),
            # Tweed
            ("FMA (Tweed)", "25° ± 3°"),
            ("FMIA (Tweed)", "65° ± 3°"),
            ("IMPA (Tweed)", "90° ± 3°"),
        ]

        self.table_results = QTableWidget(len(self.all_measures), 4)
        self.table_results.setHorizontalHeaderLabels(
            ["Mesure", "Valeur", "Norme", "Remarque / Diagnostic ODF"]
        )
        self.table_results.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table_results.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table_results.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table_results.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )

        for row, (name, norm) in enumerate(self.all_measures):
            self.table_results.setItem(row, 0, QTableWidgetItem(name))
            self.table_results.setItem(row, 1, QTableWidgetItem("-"))
            self.table_results.setItem(row, 2, QTableWidgetItem(norm))
            self.table_results.setItem(row, 3, QTableWidgetItem("En attente"))

        lay_analysis.addWidget(self.table_results)
        grp_analysis.setLayout(lay_analysis)
        right_layout.addWidget(grp_analysis)

        # 3. Export PDF
        grp_export = QGroupBox("3. Exportation Rapport")
        lay_export = QVBoxLayout()
        self.btn_export_pdf = QPushButton("📄 Exporter le rapport PDF")
        self.btn_export_pdf.setStyleSheet(
            "background-color: #2e7d32; color: white; font-weight: bold;"
            " padding: 10px;"
        )
        self.btn_export_pdf.clicked.connect(self.export_to_pdf)
        lay_export.addWidget(self.btn_export_pdf)
        grp_export.setLayout(lay_export)
        right_layout.addWidget(grp_export)

        main_layout.addWidget(right_widget)

    def load_cephalogram(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner la télé-radiographie",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif)",
        )
        if file_path:
            if self.canvas.load_image(file_path):
                self.reset_image_adjustments()
                self.on_landmarks_updated()

    def on_image_adjust_changed(self):
        alpha = self.slider_contrast.value() / 10.0
        beta = self.slider_brightness.value()

        self.lbl_contrast.setText(f"Contraste : {alpha:.1f}")
        self.lbl_brightness.setText(f"Luminosité : {beta}")

        self.canvas.apply_contrast_brightness(alpha, beta)

    def reset_image_adjustments(self):
        self.slider_contrast.setValue(10)
        self.slider_brightness.setValue(0)
        self.on_image_adjust_changed()

    def get_next_missing_landmark(self):
        for key, desc in LANDMARKS_DEF:
            if key not in self.canvas.landmarks:
                return key
        return None

    def on_landmarks_updated(self):
        self.update_landmarks_list_ui()
        self.update_guidance_label()
        self.calculate_cephalometric_angles()

    def update_landmarks_list_ui(self):
        self.list_landmarks.clear()
        for key, (x, y) in self.canvas.landmarks.items():
            self.list_landmarks.addItem(
                f"Point [{key}] : x={int(x)}, y={int(y)}"
            )

    def delete_selected_from_list(self):
        selected_items = self.list_landmarks.selectedItems()
        if not selected_items:
            return
        item_text = selected_items[0].text()
        key = item_text.split("[")[1].split("]")[0]
        self.canvas.delete_landmark(key)

    def reset_landmarks(self):
        self.canvas.landmarks.clear()
        self.canvas.update_canvas()
        self.on_landmarks_updated()

    def update_guidance_label(self):
        next_key = self.get_next_missing_landmark()
        if next_key:
            desc = next((d for k, d in LANDMARKS_DEF if k == next_key), "")
            self.lbl_current_target.setText(
                f"👉 Cliquez pour placer : [{next_key}] - {desc}"
            )
        else:
            self.lbl_current_target.setText(
                "✅ Tous les points ont été placés !"
            )

    # ---------------- CALCULS GEOMETRIQUES ----------------
    def calculate_angle_3points(self, p1, p_vertex, p2):
        v1 = np.array([p1[0] - p_vertex[0], p1[1] - p_vertex[1]])
        v2 = np.array([p2[0] - p_vertex[0], p2[1] - p_vertex[1]])

        cos_theta = np.dot(v1, v2) / (
            np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-7
        )
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        return math.degrees(math.acos(cos_theta))

    def calculate_angle_2lines(self, line1_p1, line1_p2, line2_p1, line2_p2):
        v1 = np.array(
            [line1_p2[0] - line1_p1[0], line1_p2[1] - line1_p1[1]]
        )
        v2 = np.array(
            [line2_p2[0] - line2_p1[0], line2_p2[1] - line2_p1[1]]
        )

        cos_theta = np.dot(v1, v2) / (
            np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-7
        )
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        angle = math.degrees(math.acos(cos_theta))
        return angle if angle <= 90 else 180 - angle

    def calculate_distance_point_to_line(self, pt, line_p1, line_p2):
        p = np.array(pt)
        a = np.array(line_p1)
        b = np.array(line_p2)

        num = abs(
            (b[1] - a[1]) * p[0]
            - (b[0] - a[0]) * p[1]
            + b[0] * a[1]
            - b[1] * a[0]
        )
        den = math.hypot(b[1] - a[1], b[0] - a[0])
        return num / (den + 1e-7)

    def set_result_item(
        self,
        row,
        value,
        is_degree=True,
        min_v=None,
        max_v=None,
        remark_low="",
        remark_normal="Normale",
        remark_high="",
    ):
        unit = "°" if is_degree else " px"
        item_val = QTableWidgetItem(f"{value:.1f}{unit}")
        item_rem = QTableWidgetItem()

        if min_v is not None and max_v is not None:
            if value < min_v:
                color = QColor(211, 47, 47)  # Rouge
                item_rem.setText(remark_low)
            elif value > max_v:
                color = QColor(211, 47, 47)  # Rouge
                item_rem.setText(remark_high)
            else:
                color = QColor(0, 200, 83)  # Vert
                item_rem.setText(remark_normal)

            item_val.setForeground(color)
            item_rem.setForeground(color)

        self.table_results.setItem(row, 1, item_val)
        self.table_results.setItem(row, 3, item_rem)

    def calculate_cephalometric_angles(self):
        lm = self.canvas.landmarks

        # ---------------- STEINER ----------------
        # 0. SNA
        if "S" in lm and "N" in lm and "A" in lm:
            sna = self.calculate_angle_3points(lm["S"], lm["N"], lm["A"])
            self.set_result_item(
                0,
                sna,
                True,
                80,
                84,
                "Rétrognathie maxillaire",
                "Position maxillaire normale",
                "Prognathisme maxillaire",
            )
        else:
            self.table_results.setItem(0, 1, QTableWidgetItem("-"))

        # 1. SNB
        if "S" in lm and "N" in lm and "B" in lm:
            snb = self.calculate_angle_3points(lm["S"], lm["N"], lm["B"])
            self.set_result_item(
                1,
                snb,
                True,
                78,
                82,
                "Rétrognathie mandibulaire",
                "Position mandibulaire normale",
                "Prognathisme mandibulaire",
            )
        else:
            self.table_results.setItem(1, 1, QTableWidgetItem("-"))

        # 2. ANB
        if "S" in lm and "N" in lm and "A" in lm and "B" in lm:
            sna = self.calculate_angle_3points(lm["S"], lm["N"], lm["A"])
            snb = self.calculate_angle_3points(lm["S"], lm["N"], lm["B"])
            anb = sna - snb
            self.set_result_item(
                2,
                anb,
                True,
                0,
                4,
                "Classe III squelettique",
                "Classe I squelettique",
                "Classe II squelettique",
            )
        else:
            self.table_results.setItem(2, 1, QTableWidgetItem("-"))

        # 3. SND
        if "S" in lm and "N" in lm and "Gn" in lm:
            snd = self.calculate_angle_3points(lm["S"], lm["N"], lm["Gn"])
            self.set_result_item(
                3,
                snd,
                True,
                74,
                78,
                "Position antéro-inférieure faible",
                "Position normale",
                "Position antéro-inférieure forte",
            )
        else:
            self.table_results.setItem(3, 1, QTableWidgetItem("-"))

        # 4. GoGn - SN
        if "Go" in lm and "Gn" in lm and "S" in lm and "N" in lm:
            gogn_sn = self.calculate_angle_2lines(
                lm["Go"], lm["Gn"], lm["S"], lm["N"]
            )
            self.set_result_item(
                4,
                gogn_sn,
                True,
                27,
                37,
                "Hypodivergence (croissance htz)",
                "Normodivergence",
                "Hyperdivergence (croissance vert)",
            )
        else:
            self.table_results.setItem(4, 1, QTableWidgetItem("-"))

        # 5. 1u à NA (Angle)
        if "1u" in lm and "1u_edge" in lm and "N" in lm and "A" in lm:
            a_1u_na = self.calculate_angle_2lines(
                lm["1u"], lm["1u_edge"], lm["N"], lm["A"]
            )
            self.set_result_item(
                5,
                a_1u_na,
                True,
                18,
                26,
                "Rétroclination supérieure",
                "Inclinaison sup. normale",
                "Proclination supérieure",
            )
        else:
            self.table_results.setItem(5, 1, QTableWidgetItem("-"))

        # 6. 1u à NA (Distance)
        if "1u_edge" in lm and "N" in lm and "A" in lm:
            d_1u_na = self.calculate_distance_point_to_line(
                lm["1u_edge"], lm["N"], lm["A"]
            )
            self.set_result_item(6, d_1u_na, False)
        else:
            self.table_results.setItem(6, 1, QTableWidgetItem("-"))

        # 7. 1l à NB (Angle)
        if "1l" in lm and "1l_edge" in lm and "N" in lm and "B" in lm:
            a_1l_nb = self.calculate_angle_2lines(
                lm["1l"], lm["1l_edge"], lm["N"], lm["B"]
            )
            self.set_result_item(
                7,
                a_1l_nb,
                True,
                21,
                29,
                "Rétroclination inférieure",
                "Inclinaison inf. normale",
                "Proclination inférieure",
            )
        else:
            self.table_results.setItem(7, 1, QTableWidgetItem("-"))

        # 8. 1l à NB (Distance)
        if "1l_edge" in lm and "N" in lm and "B" in lm:
            d_1l_nb = self.calculate_distance_point_to_line(
                lm["1l_edge"], lm["N"], lm["B"]
            )
            self.set_result_item(8, d_1l_nb, False)
        else:
            self.table_results.setItem(8, 1, QTableWidgetItem("-"))

        # 9. Inter-incisif
        if (
            "1u" in lm
            and "1u_edge" in lm
            and "1l" in lm
            and "1l_edge" in lm
        ):
            a_ii = self.calculate_angle_2lines(
                lm["1u"], lm["1u_edge"], lm["1l"], lm["1l_edge"]
            )
            val_ii = 180 - a_ii
            self.set_result_item(
                9,
                val_ii,
                True,
                125,
                137,
                "Biprotrusion",
                "Angle inter-incisif normal",
                "Birétroclusion",
            )
        else:
            self.table_results.setItem(9, 1, QTableWidgetItem("-"))

        # 10. Pog à NB
        if "Pog" in lm and "N" in lm and "B" in lm:
            d_pog_nb = self.calculate_distance_point_to_line(
                lm["Pog"], lm["N"], lm["B"]
            )
            self.set_result_item(10, d_pog_nb, False)
        else:
            self.table_results.setItem(10, 1, QTableWidgetItem("-"))

        # ---------------- TRIANGLE DE TWEED ----------------
        # 11. FMA (Angle Francfort / Plan Mandibulaire)
        if "Po" in lm and "Or" in lm and "Go" in lm and "Gn" in lm:
            fma = self.calculate_angle_2lines(
                lm["Po"], lm["Or"], lm["Go"], lm["Gn"]
            )
            self.set_result_item(
                11,
                fma,
                True,
                22,
                28,
                "Hypodivergence / Croissance horizontale",
                "Normodivergence Tweed",
                "Hyperdivergence / Croissance verticale",
            )
        else:
            self.table_results.setItem(11, 1, QTableWidgetItem("-"))

        # 12. FMIA (Angle Incisive Inférieure / Francfort)
        if "Po" in lm and "Or" in lm and "1l" in lm and "1l_edge" in lm:
            fmia = self.calculate_angle_2lines(
                lm["Po"], lm["Or"], lm["1l"], lm["1l_edge"]
            )
            self.set_result_item(
                12,
                fmia,
                True,
                62,
                68,
                "Incisive inf. lingualée / Rétroclination",
                "Axe incisif inf./Francfort normal",
                "Incisive inf. vestibulée / Proclination",
            )
        else:
            self.table_results.setItem(12, 1, QTableWidgetItem("-"))

        # 13. IMPA (Angle Incisive Inférieure / Plan Mandibulaire)
        if "Go" in lm and "Gn" in lm and "1l" in lm and "1l_edge" in lm:
            impa = self.calculate_angle_2lines(
                lm["Go"], lm["Gn"], lm["1l"], lm["1l_edge"]
            )
            self.set_result_item(
                13,
                impa,
                True,
                87,
                93,
                "Rétroinclination incisive inf. (Rétroalveolie)",
                "Inclinaison incisive inf. normale",
                "Proinclination incisive inf. (Proalveolie)",
            )
        else:
            self.table_results.setItem(13, 1, QTableWidgetItem("-"))

    # ---------------- EXPORTATION PDF ----------------
    def export_to_pdf(self):
        if self.canvas.pixmap_orig is None:
            QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez d'abord charger une télé-radiographie.",
            )
            return

        nom_patient = self.txt_nom.text().strip() or "Non spécifié"
        prenom_patient = self.txt_prenom.text().strip() or "Non spécifié"

        default_filename = f"Rapport_{nom_patient}_{prenom_patient}.pdf".replace(
            " ", "_"
        )

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le rapport PDF",
            default_filename,
            "Fichiers PDF (*.pdf)",
        )
        if not save_path:
            return

        try:
            temp_img_path = "temp_ceph_render.png"
            pixmap = self.canvas.pixmap()
            pixmap.save(temp_img_path)

            pdf = FPDF(orientation="P", unit="mm", format="A4")
            pdf.add_page()

            pdf.set_font("Helvetica", style="B", size=15)
            pdf.cell(
                0,
                10,
                text="Rapport d'Analyse Céphalométrique (Steiner & Tweed)",
                new_x="LMARGIN",
                new_y="NEXT",
                align="C",
            )
            pdf.ln(2)

            pdf.set_font("Helvetica", style="B", size=10)
            pdf.set_fill_color(240, 240, 240)
            date_jour = datetime.now().strftime("%d/%m/%Y")

            pdf.cell(
                0,
                7,
                text=(
                    f" Patient : {nom_patient.upper()} {prenom_patient.capitalize()} | Date"
                    f" : {date_jour}"
                ),
                border=1,
                fill=True,
                new_x="LMARGIN",
                new_y="NEXT",
            )
            pdf.ln(3)

            # Image
            pdf.image(temp_img_path, x=55, w=100)
            pdf.ln(3)

            # En-tête Tableau
            pdf.set_font("Helvetica", style="B", size=11)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(
                0,
                6,
                text="Résultats des Analyses Céphalométriques",
                new_x="LMARGIN",
                new_y="NEXT",
            )
            pdf.ln(2)

            pdf.set_font("Helvetica", style="B", size=8)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(45, 6, text="Mesure", border=1, fill=True)
            pdf.cell(25, 6, text="Valeur", border=1, fill=True)
            pdf.cell(25, 6, text="Norme", border=1, fill=True)
            pdf.cell(
                95,
                6,
                text="Remarque / Diagnostic ODF",
                border=1,
                fill=True,
                new_x="LMARGIN",
                new_y="NEXT",
            )

            # Remplissage des données avec coloration dynamique
            pdf.set_font("Helvetica", size=8)
            for row in range(self.table_results.rowCount()):
                measure = (
                    self.table_results.item(row, 0).text()
                    if self.table_results.item(row, 0)
                    else ""
                )
                val_item = self.table_results.item(row, 1)
                value = val_item.text() if val_item else "-"
                norm = (
                    self.table_results.item(row, 2).text()
                    if self.table_results.item(row, 2)
                    else ""
                )
                rem_item = self.table_results.item(row, 3)
                remark = rem_item.text() if rem_item else ""

                r_col, g_col, b_col = 0, 0, 0
                if val_item and val_item.foreground():
                    qcol = val_item.foreground().color()
                    r_col, g_col, b_col = qcol.red(), qcol.green(), qcol.blue()

                pdf.set_text_color(0, 0, 0)
                pdf.cell(45, 6, text=measure, border=1)

                pdf.set_text_color(r_col, g_col, b_col)
                pdf.cell(25, 6, text=value, border=1)

                pdf.set_text_color(0, 0, 0)
                pdf.cell(25, 6, text=norm, border=1)

                pdf.set_text_color(r_col, g_col, b_col)
                pdf.cell(
                    95,
                    6,
                    text=remark,
                    border=1,
                    new_x="LMARGIN",
                    new_y="NEXT",
                )

            pdf.set_text_color(0, 0, 0)
            pdf.output(save_path)

            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)

            QMessageBox.information(
                self,
                "Succès",
                f"Rapport PDF exporté avec succès !\n{save_path}",
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Erreur", f"Échec de l'exportation PDF : {str(e)}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CephalometricApp()
    window.show()
    sys.exit(app.exec())