# ici nous allons travailler sur la sauvegarde un projet (qui est sur une forme de dict) dans un fichier .painter en fprmat JSON
# nous allons aussi gerer la lecture de ces fichier .painter  (ceci c'est pour l'importation des fichier) déja existante
#  on commence par impoter le module JSON qui nous permet de lire/ecrire du python
import json
from datetime import datetime # datetime : Pour ajouter la date de sauvegarde
from PySide6.QtWidgets import QFileDialog, QMessageBox # QFileDialog : Boîte de dialogue pour choisir où sauvegarder/ouvrir et QMessageBox : Afficher des messages d'erreur/succès
class projectManager: # cette class gere la sauvegarde et l'ouverture des fichier .painter
    def __init__(self): # ceci est un constructeur qui nous permet de proposer a l'utilisateur de sauvegarder son nouveau project dans le dossier dans le quel il as sauvegarder son dernier projet
        self.last_directory = "" #une variable pour mémorisé le dernier dossier utiliser
# gérons maintenant la partie sauvegarde des projects
    def save_project(self, drawing_area, parent_widget=None): # nous permet de sauvegarder  le projet actuel dans un fichier .painter

#E1 commencons d'abord par récuperer les données dans le canvas      
        try:
            data = drawing_area.export_data()
        except Exception as e:
            # Si export_data() plante, on affiche une erreur
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "Erreur d'export",
                    f"Impossible d'exporter les données du canvas :\n{e}"
                )
            return False # ce bloc est utiliser dans le cas ou Si DrawingArea a un bug dans export_data(), on ne veut pasque tout le programme plante. On attrape l'erreur et on informe l'utilisateur.

# E2 nous allons maintenant ouvrir la boite de dialogue "sauvegarde sous"
        # getSaveFileName ouvre une fenêtre système pour choisir où sauvegarder
        # Elle retourne 2 valeurs : le chemin du fichier et le filtre utilisé
        file_path, _ = QFileDialog.getSaveFileName(
            parent_widget,                          # Widget parent (pour centrer la fenêtre)
            "Sauvegarder le projet",                # Titre de la fenêtre
            self.last_directory,                    # Dossier où s'ouvrir
            "Fichiers Painter (*.painter);;Tous les fichiers (*.*)"  # Filtres
        )

#E3 nous allons vérifier si l'utilisateur a bien choisi un fichier 
        if not file_path:
            # L'utilisateur a annulé, on arrête ici (pas d'erreur, c'est normal)
            return False
        if not file_path.endswith('.painter'):
            file_path += '.painter' # Si l'utilisateur tape "mon_projet" sans extension, on veut que ça devienne "mon_projet.painter"
        import os
        self.last_directory = os.path.dirname(file_path) #E4 ceci c'est pour sauvegarder le dosssier pour la prochaine fois
        project_data = {
            "version": "1.0",                           # Version du format de fichier
            "date_sauvegarde": datetime.now().isoformat(),  # Date et heure actuelles
            "nom_projet": os.path.basename(file_path),  # Nom du fichier
            "scene_2d": data,                           # Les données du canvas
            "scene_3d": {}                              # Pour l'instant vide (futur)
        }
        #E5 Appeler notre méthode privée pour écrire le fichier
        success = self._write_to_file(file_path, project_data, parent_widget)
        if success and parent_widget:
            # Afficher un message de succès avec une icône verte
            QMessageBox.information(
                parent_widget,
                "Sauvegarde réussie",
                f"Le projet a été sauvegardé avec succès :\n{file_path}"
            )
        return success

# gérons maintenant la partie ouverture d'un projet
    def load_project(self, drawing_area, parent_widget=None):

#E1 OUVRIR LA BOÎTE DE DIALOGUE "OUVRIR UN FICHIER"

        # getOpenFileName ouvre une fenêtre système pour choisir un fichier
        file_path, _ = QFileDialog.getOpenFileName(
            parent_widget,                          # Widget parent
            "Ouvrir un projet",                     # Titre
            self.last_directory,                    # Dossier de départ
            "Fichiers Painter (*.painter);;Tous les fichiers (*.*)"  # Filtres
        )

#E2 VÉRIFIER QUE L'UTILISATEUR A BIEN CHOISI UN FICHIER
        if not file_path:
            # L'utilisateur a annulé
            return False
        
#E3 SAUVEGARDER LE DOSSIER POUR LA PROCHAINE FOIS
        import os
        self.last_directory = os.path.dirname(file_path)

#E4 LIRE LE FICHIER ET PARSER LE JSON
        # Appeler notre méthode privée pour lire le fichier
        project_data = self._read_from_file(file_path, parent_widget)
        
        # Si la lecture a échoué, project_data sera None
        if project_data is None:
            return False
        
#E5 VALIDER LA STRUCTURE DES DONNÉES
        # Vérifier que le fichier contient bien les clés attendues
        if "scene_2d" not in project_data:
            if parent_widget:
                QMessageBox.warning(
                    parent_widget,
                    "Fichier invalide",
                    "Ce fichier ne contient pas de données 2D valides."
                )
            return False
       
 #E6 ENVOYER LES DONNÉES À DRAWINGAREA      
        # Extraire les données 2D
        scene_2d_data = project_data["scene_2d"]
        
        # Appeler import_data() que tu as créée à l'Étape 2
        try:
            success = drawing_area.import_data(scene_2d_data)
        except Exception as e:
            # Si import_data() plante, on affiche une erreur
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "Erreur d'import",
                    f"Impossible d'importer les données dans le canvas :\n{e}"
                )
            return False
       
#E7 AFFICHER UN MESSAGE DE CONFIRMATION       
        if success and parent_widget:
            # Compter le nombre de traits chargés
            nb_traits = len(scene_2d_data.get("paths", []))
            
            QMessageBox.information(
                parent_widget,
                "Ouverture réussie",
                f"Le projet a été ouvert avec succès !\n"
                f"{nb_traits} trait(s) chargé(s)."
            )
        
        return success
    
#  MÉTHODES PRIVÉES (HELPER METHODS)
    def _write_to_file(self, file_path, data, parent_widget=None): # Écrit des données dans un fichier JSON.
        try:
            # Ouvrir le fichier en mode écriture
            # 'w' = write (écrire, écrase le contenu si le fichier existe)
            # encoding='utf-8' = pour supporter les accents et caractères spéciaux
            with open(file_path, 'w', encoding='utf-8') as f:
                # json.dump() convertit le dictionnaire en JSON et l'écrit dans le fichier
                # indent=4 : Formater joliment le JSON (4 espaces d'indentation)
                # ensure_ascii=False : Permettre les caractères non-ASCII (accents)
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            # IOError = erreur d'entrée/sortie (disque plein, pas de permission, etc.)
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "Erreur d'écriture",
                    f"Impossible d'écrire le fichier :\n{e}"
                )
            return False
        except Exception as e:
            # Toute autre erreur imprévue
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "Erreur",
                    f"Une erreur est survenue lors de la sauvegarde :\n{e}"
                )
            return False
    def _read_from_file(self, file_path, parent_widget=None): #  Lit un fichier JSON et retourne les données.
        try:
            # Ouvrir le fichier en mode lecture
            # 'r' = read (lecture)
            # encoding='utf-8' = pour lire correctement les accents
            with open(file_path, 'r', encoding='utf-8') as f:
                # json.load() lit le JSON et le convertit en dictionnaire Python
                data = json.load(f)
            
            return data
            
        except FileNotFoundError:
            # Le fichier n'existe pas
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "Fichier introuvable",
                    f"Le fichier n'existe pas :\n{file_path}"
                )
            return None
        except json.JSONDecodeError as e:
            # Le fichier n'est pas un JSON valide (corrompu, mal formaté)
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "Fichier corrompu",
                    f"Le fichier n'est pas un JSON valide :\n{e}"
                )
            return None
        
        except Exception as e:
            # Toute autre erreur imprévue
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "Erreur",
                    f"Une erreur est survenue lors de la lecture :\n{e}"
                )
            return None
        