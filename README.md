# Painter
Painter est un logiciel de dessin à projection écrit en Python 3 utilisant OpenGL pour le rendu. Il prend en charge les dessins 2D et 3D.
 
## Fonctionnalités

- **Dessin 2D** avec transformations planaires

- **Dessin 3D** avec transformations spaciales

- **Sauvegarde de dessin** 

- **Coloration** coloration des dessins par la prise en charge des couleurs au format RVB

- **outils de dessin** gomme, pipe pinceau, etc 

# Arborescence

├─ painter\  
|├─ 📄 main.py    # fichier principal  
|├─ 📁 Sources\   
||├─ core\     # Coeur de l'application  
|||├─ Gui\      
||||├─ main_window.py  
||||├─ toolbar.py  
||||└─ menus.py  
|||├─ motor_2D\  
||||├─ drawing.py  
||||└─ init_2D.py   
|||├─ motor_3D\  
||||├─ init_3D.py  
||||├─ modeling.py  
||||├─ projection.py    
||||└─ shaders.py   
|||└─ Sauvegarde\  
||||├─ file_editing.py  
||||├─ data_file.py  
||||├─ Data_file.json  
||||└─ Gest_storage.py  
||├─ Assets\     
├─ 📄 README.md  
├─ 📄 LICENSE  
└─ 📄 .gitignore  


## Installation et utilisation

### Prérequis

- **Python** : Version 3 
- **PyQt6**: Module d'interface graphique
- **OpenGL**: Module de rendu 3D

### Installation

1. Installer python depuis son site officiel ou installer anaconda
2. ouvrir une nouvelle instance de terminal et tapez les commandes :
```bash / powershell
pip install PyQt6 PyOpenGL PyOpenGL_accelerate
```

# Execution 

Lancez le fichier main.py ou ouvrez le dans un terminal
