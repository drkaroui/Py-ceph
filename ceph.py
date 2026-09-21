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
    QComboBox,
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
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("monapp.ceph.1.0")
except Exception:
    pass

# ---------------- DEFINITION DES POINTS (STEINER + TWEED) ----------------
LANDMARKS_DEF = [
    ("S", {"FR": "Sella (Centre de la selle turcique)", "EN": "Sella (Center of sella turcica)"}),
    ("N", {"FR": "Nasion (Suture naso-frontale)", "EN": "Nasion (Nasofrontal suture)"}),
    ("A", {"FR": "Point A (Subspinale maxillaire)", "EN": "Point A (Maxillary subspinale)"}),
    ("B", {"FR": "Point B (Supramentale mandibulaire)", "EN": "Point B (Mandibular supramentale)"}),
    ("Pog", {"FR": "Pogonion (Point le plus antérieur du menton)", "EN": "Pogonion (Most anterior point of chin)"}),
    ("Gn", {"FR": "Gnathion (Point le plus antero-inférieur du menton)", "EN": "Gnathion (Most anteroinferior point of chin)"}),
    ("Go", {"FR": "Gonion (Angle de la mandibule)", "EN": "Gonion (Mandibular angle)"}),
    ("1u", {"FR": "Apex de l'incisive supérieure", "EN": "Upper incisor apex"}),
    ("1u_edge", {"FR": "Bord incisif supérieur", "EN": "Upper incisor tip"}),
    ("1l", {"FR": "Apex de l'incisive inférieure", "EN": "Lower incisor apex"}),
    ("1l_edge", {"FR": "Bord incisif inférieur", "EN": "Lower incisor tip"}),
    ("ANS", {"FR": "Épine Nasale Antérieure", "EN": "Anterior Nasal Spine (ANS)"}),
    ("PNS", {"FR": "Épine Nasale Postérieure", "EN": "Posterior Nasal Spine (PNS)"}),
    ("Po", {"FR": "Porion (Bord supérieur du méat acoustique externe)", "EN": "Porion (Upper margin of external acoustic meatus)"}),
    ("Or", {"FR": "Orbitale (Point le plus inférieur du rebord orbitaire)", "EN": "Orbitale (Lowest point of infraorbital margin)"}),
]

# ---------------- DICTIONNAIRE DE TRADUCTIONS ----------------
TRANSLATIONS = {
    "FR": {
        "title": "Py-ceph - Analyse Céphalométrique de Steiner & Tweed (Dr.Karoui.Abdelfetteh)",
        "patient_info": "Informations Patient",
        "last_name": "Nom :",
        "first_name": "Prénom :",
        "ph_last_name": "Ex: Dupont",
        "ph_first_name": "Ex: Jean",
        "img_settings": "Télé-radiographie & Réglages Image",
        "load_radio": "Charger Radio (.png, .jpg, .bmp)",
        "contrast": "Contraste :",
        "brightness": "Luminosité :",
        "reset": "Réinitialiser",
        "landmarks_placement": "1. Placement des Points Anatomiques",
        "start_hint": "Charger une radiographie pour commencer.",
        "all_placed": "✅ Tous les points ont été placés !",
        "click_to_place": "👉 Cliquez pour placer :",
        "shift_tip": "💡 <i>Maintenez <b>Shift</b> en cliquant pour forcer l'ajout d'un point très proche d'un autre.</i>",
        "delete_selected": "🗑️ Supprimer sélection",
        "reset_all": "Réinitialiser tout",
        "analysis_title": "2. Analyse & Diagnostic ODF (Steiner + Tweed)",
        "col_measure": "Mesure",
        "col_value": "Valeur",
        "col_norm": "Norme",
        "col_remark": "Remarque / Diagnostic ODF",
        "export_title": "3. Exportation Rapport",
        "btn_export": "📄 Exporter le rapport PDF",
        "delete_point_menu": "❌ Supprimer le point [{}]",
        "pending": "En attente",
        "lang_label": "Langue / Language :",
        # Diagnostic labels
        "normal": "Normale",
        "max_retro": "Rétrognathie maxillaire",
        "max_pos_norm": "Position maxillaire normale",
        "max_prog": "Prognathisme maxillaire",
        "mand_retro": "Rétrognathie mandibulaire",
        "mand_pos_norm": "Position mandibulaire normale",
        "mand_prog": "Prognathisme mandibulaire",
        "class_3": "Classe III squelettique",
        "class_1": "Classe I squelettique",
        "class_2": "Classe II squelettique",
        "pos_low": "Position antéro-inférieure faible",
        "pos_norm": "Position normale",
        "pos_high": "Position antéro-inférieure forte",
        "hypo_div": "Hypodivergence (croissance htz)",
        "normo_div": "Normodivergence",
        "hyper_div": "Hyperdivergence (croissance vert)",
        "retro_sup": "Rétroclination supérieure",
        "inc_sup_norm": "Inclinaison sup. normale",
        "pro_sup": "Proclination supérieure",
        "retro_inf": "Rétroclination inférieure",
        "inc_inf_norm": "Inclinaison inf. normale",
        "pro_inf": "Proclination inférieure",
        "biprotrusion": "Biprotrusion",
        "inter_inc_norm": "Angle inter-incisif normal",
        "bi_retro": "Birétroclusion",
        "tweed_hypo": "Hypodivergence / Croissance horizontale",
        "tweed_normo": "Normodivergence Tweed",
        "tweed_hyper": "Hyperdivergence / Croissance verticale",
        "tweed_fmia_low": "Incisive inf. lingualée / Rétroclination",
        "tweed_fmia_norm": "Axe incisif inf./Francfort normal",
        "tweed_fmia_high": "Incisive inf. vestibulée / Proclination",
        "tweed_impa_low": "Rétroinclination incisive inf. (Rétroalveolie)",
        "tweed_impa_norm": "Inclinaison incisive inf. normale",
        "tweed_impa_high": "Proinclination incisive inf. (Proalveolie)",
        # PDF & Messages
        "pdf_title": "Rapport d'Analyse Céphalométrique (Steiner & Tweed)",
        "patient": "Patient",
        "date": "Date",
        "not_specified": "Non spécifié",
        "err_no_radio": "Veuillez d'abord charger une télé-radiographie.",
        "success_pdf": "Rapport PDF exporté avec succès !",
    },
    "EN": {
        "title": "Py-ceph - Steiner & Tweed Cephalometric Analysis (Dr.Karoui.Abdelfetteh)",
        "patient_info": "Patient Information",
        "last_name": "Last Name:",
        "first_name": "First Name:",
        "ph_last_name": "E.g. Smith",
        "ph_first_name": "E.g. John",
        "img_settings": "X-Ray & Image Controls",
        "load_radio": "Load X-Ray (.png, .jpg, .bmp)",
        "contrast": "Contrast:",
        "brightness": "Brightness:",
        "reset": "Reset",
        "landmarks_placement": "1. Anatomical Landmarks Placement",
        "start_hint": "Load an X-ray image to start.",
        "all_placed": "✅ All landmarks placed!",
        "click_to_place": "👉 Click to place:",
        "shift_tip": "💡 <i>Hold <b>Shift</b> while clicking to force landmark placement close to another.</i>",
        "delete_selected": "🗑️ Delete selected",
        "reset_all": "Reset all",
        "analysis_title": "2. Orthodontic Analysis & Diagnosis (Steiner + Tweed)",
        "col_measure": "Measurement",
        "col_value": "Value",
        "col_norm": "Norm",
        "col_remark": "Remarks / Diagnosis",
        "export_title": "3. Export Report",
        "btn_export": "📄 Export PDF Report",
        "delete_point_menu": "❌ Delete point [{}]",
        "pending": "Pending",
        "lang_label": "Language / Langue :",
        # Diagnostic labels
        "normal": "Normal",
        "max_retro": "Maxillary retrognathism",
        "max_pos_norm": "Normal maxillary position",
        "max_prog": "Maxillary prognathism",
        "mand_retro": "Mandibular retrognathism",
        "mand_pos_norm": "Normal mandibular position",
        "mand_prog": "Mandibular prognathism",
        "class_3": "Skeletal Class III",
        "class_1": "Skeletal Class I",
        "class_2": "Skeletal Class II",
        "pos_low": "Weak anteroinferior position",
        "pos_norm": "Normal position",
        "pos_high": "Strong anteroinferior position",
        "hypo_div": "Hypodivergence (horizontal growth)",
        "normo_div": "Normodivergence",
        "hyper_div": "Hyperdivergence (vertical growth)",
        "retro_sup": "Upper retroclination",
        "inc_sup_norm": "Normal upper inclination",
        "pro_sup": "Upper proclination",
        "retro_inf": "Lower retroclination",
        "inc_inf_norm": "Normal lower inclination",
        "pro_inf": "Lower proclination",
        "biprotrusion": "Biprotrusion",
        "inter_inc_norm": "Normal interincisal angle",
        "bi_retro": "Biretroclusion",
        "tweed_hypo": "Hypodivergence / Horizontal growth",
        "tweed_normo": "Tweed Normodivergence",
        "tweed_hyper": "Hyperdivergence / Vertical growth",
        "tweed_fmia_low": "Lower incisor retroclination / Lingualized",
        "tweed_fmia_norm": "Normal lower incisor / Frankfurt axis",
        "tweed_fmia_high": "Lower incisor proclination / Labialized",
        "tweed_impa_low": "Lower incisor retroinclination",
        "tweed_impa_norm": "Normal lower incisor inclination",
        "tweed_impa_high": "Lower incisor proinclination",
        # PDF & Messages
        "pdf_title": "Cephalometric Analysis Report (Steiner & Tweed)",
        "patient": "Patient",
        "date": "Date",
        "not_specified": "Not specified",
        "err_no_radio": "Please load an X-ray image first.",
        "success_pdf": "PDF report successfully exported!",
    },
}


class CephGraphicView(QLabel):
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
        self.setStyleSheet("border: 2px dashed #444; background-color: #1e1e1e;")
        self.setMinimumSize(400, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

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
        self.image_np_adjusted = cv2.convertScaleAbs(self.image_np_orig, alpha=alpha, beta=beta)
        self.update_pixmap_from_np()

    def update_pixmap_from_np(self):
        if self.image_np_adjusted is None:
            return
        height, width = self.image_np_adjusted.shape
        q_img = QImage(self.image_np_adjusted.data, width, height, width, QImage.Format.Format_Grayscale8)
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

        if 0 <= click_x <= pix_size.width() and 0 <= click_y <= pix_size.height():
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

        if event.button() == Qt.MouseButton.RightButton:
            if clicked_lm:
                menu = QMenu(self)
                text = self.parent_app.tr("delete_point_menu").format(clicked_lm)
                action_delete = QAction(text, self)
                action_delete.triggered.connect(lambda: self.delete_landmark(clicked_lm))
                menu.addAction(action_delete)
                menu.exec(event.globalPosition().toPoint())
            return

        if event.button() == Qt.MouseButton.LeftButton:
            shift_pressed = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
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
            self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
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

        # Steiner Lines
        painter.setPen(QPen(QColor(0, 230, 118), 2, Qt.PenStyle.SolidLine))
        steiner_lines = [
            ("S", "N"), ("N", "A"), ("N", "B"), ("N", "Gn"),
            ("Go", "Gn"), ("1u", "1u_edge"), ("1l", "1l_edge"), ("ANS", "PNS")
        ]
        for k1, k2 in steiner_lines:
            p1, p2 = get_pt(k1), get_pt(k2)
            if p1 and p2:
                painter.drawLine(p1, p2)

        # Tweed Lines
        painter.setPen(QPen(QColor(255, 170, 0), 2, Qt.PenStyle.DashLine))
        tweed_lines = [("Po", "Or"), ("Go", "Gn"), ("1l", "1l_edge")]
        for k1, k2 in tweed_lines:
            p1, p2 = get_pt(k1), get_pt(k2)
            if p1 and p2:
                painter.drawLine(p1, p2)

        # Points
        for key, (rx, ry) in self.landmarks.items():
            px, py = rx * scale_x, ry * scale_y
            pen_point = QPen(QColor(255, 235, 59), 8) if key == self.dragging_landmark else QPen(QColor(255, 52, 100), 6)
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
        self.current_lang = "FR"

        icon_path = get_resource_path("braces.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(50, 50, 1600, 950)

        self.init_ui()
        self.retranslate_ui()

    def tr(self, key):
        """Helper de traduction."""
        return TRANSLATIONS.get(self.current_lang, {}).get(key, key)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # ==================== PANNEAU GAUCHE ====================
        left_layout = QVBoxLayout()
        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        # 0. Sélecteur de Langue
        lay_lang = QHBoxLayout()
        self.lbl_lang = QLabel()
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Français", "English"])
        self.combo_lang.currentIndexChanged.connect(self.on_language_changed)
        lay_lang.addWidget(self.lbl_lang)
        lay_lang.addWidget(self.combo_lang)
        lay_lang.addStretch()
        left_layout.addLayout(lay_lang)

        # 1. Patient
        self.grp_patient = QGroupBox()
        lay_patient = QHBoxLayout()
        self.lbl_nom = QLabel()
        self.txt_nom = QLineEdit()
        self.lbl_prenom = QLabel()
        self.txt_prenom = QLineEdit()
        lay_patient.addWidget(self.lbl_nom)
        lay_patient.addWidget(self.txt_nom)
        lay_patient.addWidget(self.lbl_prenom)
        lay_patient.addWidget(self.txt_prenom)
        self.grp_patient.setLayout(lay_patient)
        left_layout.addWidget(self.grp_patient)

        # 2. Image controls
        self.grp_img_ctrl = QGroupBox()
        lay_img_ctrl = QHBoxLayout()
        self.btn_load_img = QPushButton()
        self.btn_load_img.setStyleSheet("background-color: #0288d1; color: white; font-weight: bold; padding: 8px;")
        self.btn_load_img.clicked.connect(self.load_cephalogram)
        lay_img_ctrl.addWidget(self.btn_load_img)

        self.lbl_contrast = QLabel()
        self.slider_contrast = QSlider(Qt.Orientation.Horizontal)
        self.slider_contrast.setRange(5, 30)
        self.slider_contrast.setValue(10)
        self.slider_contrast.valueChanged.connect(self.on_image_adjust_changed)
        lay_img_ctrl.addWidget(self.lbl_contrast)
        lay_img_ctrl.addWidget(self.slider_contrast)

        self.lbl_brightness = QLabel()
        self.slider_brightness = QSlider(Qt.Orientation.Horizontal)
        self.slider_brightness.setRange(-100, 100)
        self.slider_brightness.setValue(0)
        self.slider_brightness.valueChanged.connect(self.on_image_adjust_changed)
        lay_img_ctrl.addWidget(self.lbl_brightness)
        lay_img_ctrl.addWidget(self.slider_brightness)

        self.btn_reset_adjust = QPushButton()
        self.btn_reset_adjust.clicked.connect(self.reset_image_adjustments)
        lay_img_ctrl.addWidget(self.btn_reset_adjust)

        self.grp_img_ctrl.setLayout(lay_img_ctrl)
        left_layout.addWidget(self.grp_img_ctrl)

        # 3. Canvas
        self.canvas = CephGraphicView(self)
        left_layout.addWidget(self.canvas)

        main_layout.addWidget(left_widget)

        # ==================== PANNEAU DROIT ====================
        right_layout = QVBoxLayout()
        right_widget = QWidget()
        right_widget.setFixedWidth(560)
        right_widget.setLayout(right_layout)

        # 1. Placement points
        self.grp_pts = QGroupBox()
        lay_pts = QVBoxLayout()
        self.lbl_current_target = QLabel()
        self.lbl_current_target.setStyleSheet("color: #ff9800; font-weight: bold;")
        self.lbl_current_target.setWordWrap(True)
        lay_pts.addWidget(self.lbl_current_target)

        self.lbl_tip = QLabel()
        self.lbl_tip.setWordWrap(True)
        self.lbl_tip.setStyleSheet("color: #aaa; font-size: 11px;")
        lay_pts.addWidget(self.lbl_tip)

        self.list_landmarks = QListWidget()
        self.list_landmarks.setFixedHeight(100)
        lay_pts.addWidget(self.list_landmarks)

        lay_btn_pts = QHBoxLayout()
        self.btn_delete_selected = QPushButton()
        self.btn_delete_selected.clicked.connect(self.delete_selected_from_list)
        lay_btn_pts.addWidget(self.btn_delete_selected)

        self.btn_reset_pts = QPushButton()
        self.btn_reset_pts.clicked.connect(self.reset_landmarks)
        lay_btn_pts.addWidget(self.btn_reset_pts)

        lay_pts.addLayout(lay_btn_pts)
        self.grp_pts.setLayout(lay_pts)
        right_layout.addWidget(self.grp_pts)

        # 2. Results
        self.grp_analysis = QGroupBox()
        lay_analysis = QVBoxLayout()

        self.all_measures = [
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
            ("FMA (Tweed)", "25° ± 3°"),
            ("FMIA (Tweed)", "65° ± 3°"),
            ("IMPA (Tweed)", "90° ± 3°"),
        ]

        self.table_results = QTableWidget(len(self.all_measures), 4)
        self.table_results.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_results.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_results.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_results.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        for row, (name, norm) in enumerate(self.all_measures):
            self.table_results.setItem(row, 0, QTableWidgetItem(name))
            self.table_results.setItem(row, 1, QTableWidgetItem("-"))
            self.table_results.setItem(row, 2, QTableWidgetItem(norm))
            self.table_results.setItem(row, 3, QTableWidgetItem("-"))

        lay_analysis.addWidget(self.table_results)
        self.grp_analysis.setLayout(lay_analysis)
        right_layout.addWidget(self.grp_analysis)

        # 3. Export
        self.grp_export = QGroupBox()
        lay_export = QVBoxLayout()
        self.btn_export_pdf = QPushButton()
        self.btn_export_pdf.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 10px;")
        self.btn_export_pdf.clicked.connect(self.export_to_pdf)
        lay_export.addWidget(self.btn_export_pdf)
        self.grp_export.setLayout(lay_export)
        right_layout.addWidget(self.grp_export)

        main_layout.addWidget(right_widget)

    def on_language_changed(self, index):
        self.current_lang = "FR" if index == 0 else "EN"
        self.retranslate_ui()

    def retranslate_ui(self):
        """Réactualise tous les textes de l'interface graphique."""
        self.setWindowTitle(self.tr("title"))
        self.lbl_lang.setText(self.tr("lang_label"))
        self.grp_patient.setTitle(self.tr("patient_info"))
        self.lbl_nom.setText(self.tr("last_name"))
        self.txt_nom.setPlaceholderText(self.tr("ph_last_name"))
        self.lbl_prenom.setText(self.tr("first_name"))
        self.txt_prenom.setPlaceholderText(self.tr("ph_first_name"))

        self.grp_img_ctrl.setTitle(self.tr("img_settings"))
        self.btn_load_img.setText(self.tr("load_radio"))
        self.btn_reset_adjust.setText(self.tr("reset"))

        self.grp_pts.setTitle(self.tr("landmarks_placement"))
        self.lbl_tip.setText(self.tr("shift_tip"))
        self.btn_delete_selected.setText(self.tr("delete_selected"))
        self.btn_reset_pts.setText(self.tr("reset_all"))

        self.grp_analysis.setTitle(self.tr("analysis_title"))
        self.table_results.setHorizontalHeaderLabels([
            self.tr("col_measure"), self.tr("col_value"), self.tr("col_norm"), self.tr("col_remark")
        ])

        self.grp_export.setTitle(self.tr("export_title"))
        self.btn_export_pdf.setText(self.tr("btn_export"))

        self.on_image_adjust_changed()
        self.update_guidance_label()
        self.calculate_cephalometric_angles()

    def load_cephalogram(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select X-Ray / Sélectionner Télé-radiographie", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif)"
        )
        if file_path:
            if self.canvas.load_image(file_path):
                self.reset_image_adjustments()
                self.on_landmarks_updated()

    def on_image_adjust_changed(self):
        alpha = self.slider_contrast.value() / 10.0
        beta = self.slider_brightness.value()
        self.lbl_contrast.setText(f"{self.tr('contrast')} {alpha:.1f}")
        self.lbl_brightness.setText(f"{self.tr('brightness')} {beta}")
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
            self.list_landmarks.addItem(f"Point [{key}] : x={int(x)}, y={int(y)}")

    def delete_selected_from_list(self):
        selected_items = self.list_landmarks.selectedItems()
        if not selected_items:
            return
        key = selected_items[0].text().split("[")[1].split("]")[0]
        self.canvas.delete_landmark(key)

    def reset_landmarks(self):
        self.canvas.landmarks.clear()
        self.canvas.update_canvas()
        self.on_landmarks_updated()

    def update_guidance_label(self):
        if self.canvas.pixmap_orig is None:
            self.lbl_current_target.setText(self.tr("start_hint"))
            return

        next_key = self.get_next_missing_landmark()
        if next_key:
            desc_dict = next((d for k, d in LANDMARKS_DEF if k == next_key), {})
            desc = desc_dict.get(self.current_lang, "")
            self.lbl_current_target.setText(f"{self.tr('click_to_place')} [{next_key}] - {desc}")
        else:
            self.lbl_current_target.setText(self.tr("all_placed"))

    # ---------------- GEOMETRIC CALCULATIONS ----------------
    def calculate_angle_3points(self, p1, p_vertex, p2):
        v1 = np.array([p1[0] - p_vertex[0], p1[1] - p_vertex[1]])
        v2 = np.array([p2[0] - p_vertex[0], p2[1] - p_vertex[1]])
        cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-7)
        return math.degrees(math.acos(np.clip(cos_theta, -1.0, 1.0)))

    def calculate_angle_2lines(self, line1_p1, line1_p2, line2_p1, line2_p2):
        v1 = np.array([line1_p2[0] - line1_p1[0], line1_p2[1] - line1_p1[1]])
        v2 = np.array([line2_p2[0] - line2_p1[0], line2_p2[1] - line2_p1[1]])
        cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-7)
        angle = math.degrees(math.acos(np.clip(cos_theta, -1.0, 1.0)))
        return angle if angle <= 90 else 180 - angle

    def calculate_distance_point_to_line(self, pt, line_p1, line_p2):
        p, a, b = np.array(pt), np.array(line_p1), np.array(line_p2)
        num = abs((b[1] - a[1]) * p[0] - (b[0] - a[0]) * p[1] + b[0] * a[1] - b[1] * a[0])
        return num / (math.hypot(b[1] - a[1], b[0] - a[0]) + 1e-7)

    def set_result_item(self, row, value, is_degree=True, min_v=None, max_v=None, key_low="", key_normal="normal", key_high=""):
        unit = "°" if is_degree else " px"
        item_val = QTableWidgetItem(f"{value:.1f}{unit}")
        item_rem = QTableWidgetItem()

        if min_v is not None and max_v is not None:
            if value < min_v:
                color = QColor(211, 47, 47)
                item_rem.setText(self.tr(key_low))
            elif value > max_v:
                color = QColor(211, 47, 47)
                item_rem.setText(self.tr(key_high))
            else:
                color = QColor(0, 200, 83)
                item_rem.setText(self.tr(key_normal))

            item_val.setForeground(color)
            item_rem.setForeground(color)
        else:
            item_rem.setText("-")

        self.table_results.setItem(row, 1, item_val)
        self.table_results.setItem(row, 3, item_rem)

    def calculate_cephalometric_angles(self):
        lm = self.canvas.landmarks

        # SNA
        if "S" in lm and "N" in lm and "A" in lm:
            sna = self.calculate_angle_3points(lm["S"], lm["N"], lm["A"])
            self.set_result_item(0, sna, True, 80, 84, "max_retro", "max_pos_norm", "max_prog")
        else:
            self.table_results.setItem(0, 1, QTableWidgetItem("-"))

        # SNB
        if "S" in lm and "N" in lm and "B" in lm:
            snb = self.calculate_angle_3points(lm["S"], lm["N"], lm["B"])
            self.set_result_item(1, snb, True, 78, 82, "mand_retro", "mand_pos_norm", "mand_prog")
        else:
            self.table_results.setItem(1, 1, QTableWidgetItem("-"))

        # ANB
        if "S" in lm and "N" in lm and "A" in lm and "B" in lm:
            sna = self.calculate_angle_3points(lm["S"], lm["N"], lm["A"])
            snb = self.calculate_angle_3points(lm["S"], lm["N"], lm["B"])
            self.set_result_item(2, sna - snb, True, 0, 4, "class_3", "class_1", "class_2")
        else:
            self.table_results.setItem(2, 1, QTableWidgetItem("-"))

        # SND
        if "S" in lm and "N" in lm and "Gn" in lm:
            snd = self.calculate_angle_3points(lm["S"], lm["N"], lm["Gn"])
            self.set_result_item(3, snd, True, 74, 78, "pos_low", "pos_norm", "pos_high")
        else:
            self.table_results.setItem(3, 1, QTableWidgetItem("-"))

        # GoGn - SN
        if "Go" in lm and "Gn" in lm and "S" in lm and "N" in lm:
            gogn_sn = self.calculate_angle_2lines(lm["Go"], lm["Gn"], lm["S"], lm["N"])
            self.set_result_item(4, gogn_sn, True, 27, 37, "hypo_div", "normo_div", "hyper_div")
        else:
            self.table_results.setItem(4, 1, QTableWidgetItem("-"))

        # 1u à NA (Angle)
        if "1u" in lm and "1u_edge" in lm and "N" in lm and "A" in lm:
            a_1u_na = self.calculate_angle_2lines(lm["1u"], lm["1u_edge"], lm["N"], lm["A"])
            self.set_result_item(5, a_1u_na, True, 18, 26, "retro_sup", "inc_sup_norm", "pro_sup")
        else:
            self.table_results.setItem(5, 1, QTableWidgetItem("-"))

        # 1u à NA (Dist)
        if "1u_edge" in lm and "N" in lm and "A" in lm:
            self.set_result_item(6, self.calculate_distance_point_to_line(lm["1u_edge"], lm["N"], lm["A"]), False)
        else:
            self.table_results.setItem(6, 1, QTableWidgetItem("-"))

        # 1l à NB (Angle)
        if "1l" in lm and "1l_edge" in lm and "N" in lm and "B" in lm:
            a_1l_nb = self.calculate_angle_2lines(lm["1l"], lm["1l_edge"], lm["N"], lm["B"])
            self.set_result_item(7, a_1l_nb, True, 21, 29, "retro_inf", "inc_inf_norm", "pro_inf")
        else:
            self.table_results.setItem(7, 1, QTableWidgetItem("-"))

        # 1l à NB (Dist)
        if "1l_edge" in lm and "N" in lm and "B" in lm:
            self.set_result_item(8, self.calculate_distance_point_to_line(lm["1l_edge"], lm["N"], lm["B"]), False)
        else:
            self.table_results.setItem(8, 1, QTableWidgetItem("-"))

        # Inter-incisif
        if "1u" in lm and "1u_edge" in lm and "1l" in lm and "1l_edge" in lm:
            a_ii = self.calculate_angle_2lines(lm["1u"], lm["1u_edge"], lm["1l"], lm["1l_edge"])
            self.set_result_item(9, 180 - a_ii, True, 125, 137, "biprotrusion", "inter_inc_norm", "bi_retro")
        else:
            self.table_results.setItem(9, 1, QTableWidgetItem("-"))

        # Pog à NB
        if "Pog" in lm and "N" in lm and "B" in lm:
            self.set_result_item(10, self.calculate_distance_point_to_line(lm["Pog"], lm["N"], lm["B"]), False)
        else:
            self.table_results.setItem(10, 1, QTableWidgetItem("-"))

        # FMA
        if "Po" in lm and "Or" in lm and "Go" in lm and "Gn" in lm:
            fma = self.calculate_angle_2lines(lm["Po"], lm["Or"], lm["Go"], lm["Gn"])
            self.set_result_item(11, fma, True, 22, 28, "tweed_hypo", "tweed_normo", "tweed_hyper")
        else:
            self.table_results.setItem(11, 1, QTableWidgetItem("-"))

        # FMIA
        if "Po" in lm and "Or" in lm and "1l" in lm and "1l_edge" in lm:
            fmia = self.calculate_angle_2lines(lm["Po"], lm["Or"], lm["1l"], lm["1l_edge"])
            self.set_result_item(12, fmia, True, 62, 68, "tweed_fmia_low", "tweed_fmia_norm", "tweed_fmia_high")
        else:
            self.table_results.setItem(12, 1, QTableWidgetItem("-"))

        # IMPA
        if "Go" in lm and "Gn" in lm and "1l" in lm and "1l_edge" in lm:
            impa = self.calculate_angle_2lines(lm["Go"], lm["Gn"], lm["1l"], lm["1l_edge"])
            self.set_result_item(13, impa, True, 87, 93, "tweed_impa_low", "tweed_impa_norm", "tweed_impa_high")
        else:
            self.table_results.setItem(13, 1, QTableWidgetItem("-"))

    # ---------------- EXPORT PDF ----------------
    def export_to_pdf(self):
        if self.canvas.pixmap_orig is None:
            QMessageBox.warning(self, "Warning", self.tr("err_no_radio"))
            return

        nom_patient = self.txt_nom.text().strip() or self.tr("not_specified")
        prenom_patient = self.txt_prenom.text().strip() or self.tr("not_specified")
        default_filename = f"Rapport_{nom_patient}_{prenom_patient}.pdf".replace(" ", "_")

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", default_filename, "PDF Files (*.pdf)"
        )
        if not save_path:
            return

        try:
            temp_img_path = "temp_ceph_render.png"
            self.canvas.pixmap().save(temp_img_path)

            pdf = FPDF(orientation="P", unit="mm", format="A4")
            pdf.add_page()

            pdf.set_font("Helvetica", style="B", size=15)
            pdf.cell(0, 10, text=self.tr("pdf_title"), new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(2)

            pdf.set_font("Helvetica", style="B", size=10)
            pdf.set_fill_color(240, 240, 240)
            date_jour = datetime.now().strftime("%d/%m/%Y")

            pdf.cell(
                0, 7,
                text=f" {self.tr('patient')} : {nom_patient.upper()} {prenom_patient.capitalize()} | {self.tr('date')} : {date_jour}",
                border=1, fill=True, new_x="LMARGIN", new_y="NEXT"
            )
            pdf.ln(3)

            pdf.image(temp_img_path, x=55, w=100)
            pdf.ln(3)

            pdf.set_font("Helvetica", style="B", size=11)
            pdf.cell(0, 6, text=self.tr("analysis_title"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

            pdf.set_font("Helvetica", style="B", size=8)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(45, 6, text=self.tr("col_measure"), border=1, fill=True)
            pdf.cell(25, 6, text=self.tr("col_value"), border=1, fill=True)
            pdf.cell(25, 6, text=self.tr("col_norm"), border=1, fill=True)
            pdf.cell(95, 6, text=self.tr("col_remark"), border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", size=8)
            for row in range(self.table_results.rowCount()):
                measure = self.table_results.item(row, 0).text() if self.table_results.item(row, 0) else ""
                val_item = self.table_results.item(row, 1)
                value = val_item.text() if val_item else "-"
                norm = self.table_results.item(row, 2).text() if self.table_results.item(row, 2) else ""
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
                pdf.cell(95, 6, text=remark, border=1, new_x="LMARGIN", new_y="NEXT")

            pdf.set_text_color(0, 0, 0)
            pdf.output(save_path)

            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)

            QMessageBox.information(self, "Success", f"{self.tr('success_pdf')}\n{save_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"PDF Export Failed: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CephalometricApp()
    window.show()
    sys.exit(app.exec())
