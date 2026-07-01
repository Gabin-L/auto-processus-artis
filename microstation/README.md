# Intégration MicroStation

`IsoBuilder.bas` est une macro VBA MicroStation qui lit le JSON produit par
`iso_engine` (voir `/iso_engine/export.py`) et dessine automatiquement
l'isométrique correspondant dans un `.dgn`.

## Mise en place (une seule fois)

1. **Fichier germe (`seed_iso.dgn`)** : un DGN de départ contenant déjà
   votre format de feuille standard, cartouche, niveaux, styles de texte et
   de cotation. La macro copie ce fichier puis dessine dedans — elle ne crée
   aucun format de plan.
2. **Niveaux** : la macro s'attend à trouver les niveaux `TUYAUTERIE`,
   `RACCORDS`, `COTATION`, `SOUDURES`, `NOMENCLATURE`, `CARTOUCHE` dans le
   seed file (noms modifiables en tête de `IsoBuilder.bas`).
3. **Bibliothèque de cellules** : une cellule par valeur possible de
   `fitting_type` (voir `docs/data_schema.md`), nommée en majuscules par
   défaut (`ELBOW90`, `VALVE_GATE`, `REDUCER_CONCENTRIC`...). Adapter
   `CellNameFor` si votre bibliothèque suit une autre convention.
4. **Tags du cartouche** : le seed file doit contenir une cellule de
   cartouche avec des tags nommés d'après les clés de l'en-tête BLE en
   majuscules (`LINE_NUMBER`, `PROJECT_CODE`, `CLIENT`...).

## Utilisation

Dans l'éditeur VBA de MicroStation (Utilitaires > VBA > Editeur), charger
`IsoBuilder.bas`, puis dans la fenêtre Immédiat :

```
BuildIsoFromJson "C:\chemin\vers\drawing.json", "C:\chemin\vers\seed_iso.dgn", "C:\chemin\vers\sortie.dgn"
```

`drawing.json` est généré par `iso_engine.export.export_json` à partir des
CSV du BLE (voir `/README.md`).

## Limites connues de ce squelette

- **Cotation** : les longueurs réelles sont posées en texte brut, pas en
  vrais éléments de cotation associatifs MicroStation (`AssociativeDimension`).
  Fonctionnellement correct pour valider la chaîne de bout en bout, mais à
  remplacer par de vraies cotes avant mise en production.
- **Orientation des cellules** : les raccords sont placés sans rotation. Une
  bibliothèque de cellules isométriques "pré-tournées" (dessinées directement
  dans le plan iso, une variante par orientation standard) évite d'avoir à
  calculer une matrice de rotation 3D → iso, ce qui est l'approche la plus
  simple à court terme.
- **Nomenclature** : table texte simple, pas le composant table natif de
  MicroStation CONNECT.
- **Non testé sur un poste MicroStation réel** dans le cadre de ce chantier
  initial — l'API utilisée (`Bentley.MicroStationDGN` VBA) est documentée et
  stable depuis MicroStation V8, mais ce script doit être validé et ajusté
  avec votre version exacte, votre seed file et votre bibliothèque de
  cellules avant tout usage en production.

## Pourquoi VBA et pas .NET ou MDL ?

VBA reste embarqué dans toutes les licences MicroStation (pas d'outil
supplémentaire à installer), s'édite sans Visual Studio, et suffit largement
pour ce périmètre (placer des éléments, pas développer une UI complexe).
Si le projet grandit (interface utilisateur, traitement par lot de
centaines d'isométriques, meilleure gestion d'erreurs), migrer vers un
add-in **Bentley.DgnPlatformNET** (C#) devient pertinent : même modèle
d'objets, mais débogage et packaging bien plus confortables.
