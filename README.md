
# Py-Ceph 📐🩺

**Py-Ceph** est une application de bureau performante développée en Python permettant de réaliser des analyses céphalométriques orthodontiques à partir de clichés radiographiques. L'application offre une interface intuitive pour placer des points de repère (landmarks), calculer automatiquement les angles et mesures céphalométriques, et générer un rapport médical complet au format PDF.

[![Guide d'utilisation Py-Ceph](https://img.youtube.com/vi/52mrNa7-Imk/0.jpg)](https://www.youtube.com/watch?v=52mrNa7-Imk)
*Cliquez sur l'image ci-dessus pour lancer la vidéo de démonstration sur YouTube.*

## 📺 Démonstration & Tutoriel Vidéo

Découvrez l'application en action et son guide d'utilisation en vidéo :  
🎬 https://www.youtube.com/watch?v=52mrNa7-Imk

---

## 🚀 Fonctionnalités Principales

- **Analyse Céphalométrique Interactive :**
  - Chargement et affichage des radiographies céphalométriques.
  - Placement guidé des points anatomiques de repère.
  - Ajustement et repositionnement facile des points.

- **Calculs & Traitement d'Image :**
  - Calcul automatique des angles, distances et relations céphalométriques.
  - Traitement d'image en temps réel via OpenCV (ajustement du contraste, de la luminosité et des filtres).

- **Génération de Rapports :**
  - Exportation des résultats et des tracés au format **PDF**.
  - Génération de graphiques et récapitulatifs pour le diagnostic orthodontique.

- **Interface Ergonomique :**
  - Interface utilisateur moderne et réactive construite avec **PyQt6**.

---

## 🛠️ Technologies Utilisées

* **Langage :** [Python 3.x](https://www.python.org/)
* **Interface Graphique (GUI) :** [PyQt6](https://pypi.org/project/PyQt6/)
* **Traitement d'Image & Calculs :** [OpenCV](https://opencv.org/), [NumPy](https://numpy.org/)
* **Génération de PDF :** [FPDF2](https://pyfpdf.github.io/fpdf2/) / [Pillow](https://python-pillow.org/)
* **Packaging Exécutable :** [PyInstaller](https://pyinstaller.org/)

---

## 📂 Structure du Projet

```text
Py-Ceph/
├── ceph.py               # Fichier principal de l'application
├── requirements.txt      # Liste des dépendances Python
├── icone.png / icone.ico # Icône de l'application
├── .gitignore            # Fichiers ignorés par Git
└── README.md             # Documentation du projet
 ````
💻 Installation et Configuration (Environnement de Développement)
1. Cloner le dépôt
```
```bash
git clone [https://github.com/drkaroui/Py-ceph.git]
cd Py-Ceph
```
2. Créer et activer un environnement virtuel
Sous Windows :

```bash
python -m venv venv
venv\Scripts\activate
```
Sous macOS / Linux :

```bash
python3 -m venv venv
source venv/bin/activate
```
3. Installer les dépendances
```bash
pip install -r requirements.txt
```
4. Lancer l'application
```bash
python ceph.py
```
⚙️ Génération de l'Exécutable (.exe)
Pour compiler l'application en un fichier exécutable autonome sous Windows :

Assurez-vous d'avoir activé votre environnement virtuel avec toutes les dépendances.

Lancez la commande PyInstaller :

```bash
pyinstaller --noconsole --onefile --icon=braces.ico --add-data "braces.png;." ceph.py
```
L'exécutable généré (ceph.exe) se trouvera dans le dossier dist/.
```
📝 Licence
Ce projet est sous licence libre. Vous pouvez l'utiliser et le modifier selon vos besoins.
```
