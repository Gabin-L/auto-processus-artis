# Schéma des données d'entrée

Deux fichiers CSV par ligne à mettre en plan, à remplir à partir du BLE et du
relevé terrain (laser ou main). Exemples complets dans `/examples/`.

## 1. En-tête de ligne (`*_header.csv`)

Format clé/valeur (deux colonnes : `key`, `value`), une ligne par champ.
Champs reconnus (correspondent à `iso_engine.models.LineHeader`) :

| Clé | Obligatoire | Description |
|---|---|---|
| `line_number` | oui | Numéro de ligne BLE |
| `project_code` | oui | Code affaire (ex: `AF145`) |
| `client` | non | Nom client |
| `spec` | non | Spécification tuyauterie (matériau/schedule/rating) |
| `nominal_size` | non | Diamètre nominal de la ligne (ex: `DN80`) — diamètre par défaut, voir réductions ci-dessous |
| `schedule` | non | Épaisseur/schedule |
| `material` | non | Matériau |
| `fluid` | non | Fluide véhiculé |
| `insulation` | non | Calorifuge (oui/non, type) |
| `pid_ref` | non | Référence P&ID |
| `drawing_number` | non | Numéro de plan (cartouche) |
| `revision` | non | Indice de révision (défaut `A`) |
| `author` | non | Dessinateur |
| `date` | non | Date |

Toute clé absente de ce tableau fait échouer le parsing (protection contre
les fautes de frappe silencieuses).

## 2. Points relevés (`*_points.csv`)

Un point par ligne, dans l'ordre du parcours physique de la tuyauterie
(du départ vers l'arrivée). Colonnes :

| Colonne | Obligatoire | Description |
|---|---|---|
| `seq` | oui | Ordre du point le long du tracé (entier, pas besoin d'être continu) |
| `x_mm`, `y_mm`, `z_mm` | oui | Coordonnées du point dans un repère local propre à la ligne, en mm. `z` = altitude (verticale). Seules les positions **relatives** comptent : peu importe l'origine choisie. |
| `joint_type` | non (défaut `weld`) | `weld` (soudure), `flange` (bridé), `thread` (fileté), `end` (extrémité — piquage, équipement : jamais numéroté comme soudure) |
| `fitting_type` | non | Type de raccord au point (`elbow90`, `elbow45`, `tee`, `reducer_concentric`, `valve_gate`...). Vide = simple point du tracé, pas de composant. |
| `fitting_ref` | non | Référence/tag du composant (ex: `VA-014`) |
| `nominal_size` | non | Diamètre nominal **à partir de ce point** si différent du diamètre par défaut de la ligne (utilisé pour les réductions) |
| `note` | non | Commentaire libre |

### Comment saisir un relevé terrain

Chaque **changement de direction** ou **composant** du tracé est un point.
Un tronçon droit entre deux points n'a pas besoin de points intermédiaires
— la longueur réelle du tronçon est recalculée automatiquement à partir des
coordonnées 3D (distance euclidienne), pas saisie à la main.

### Comment saisir une vanne ou un composant "long"

Ce schéma modélise un composant comme un point unique (une simplification
volontaire pour cette première version — voir `docs/workflow.md`, phase 2).
Pour une vanne bridée en ligne droite, un seul point suffit : marquez-le
`joint_type=flange`, `fitting_type=valve_gate`. La longueur hors-tout réelle
de la vanne n'est donc pas encore soustraite de la longueur de tube — à
affiner avec une table de référence des composants standard.

### Exemple

Voir `/examples/sample_header.csv` et `/examples/sample_points.csv` — un
piquage, deux coudes, une vanne bridée, une réduction, une arrivée sur
échangeur. `/examples/sample_drawing.json` est le résultat calculé
correspondant (généré par `iso_engine.export.export_json`).
