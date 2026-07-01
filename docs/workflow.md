# Feuille de route : automatiser la mise en plan isométrique

## Contexte

Le client impose un livrable `.dgn` (MicroStation). Les données de départ
viennent du BLE (bordereau de ligne) et d'un relevé terrain (laser ou main) ;
il n'y a pas de maquette 3D tuyauterie en amont (pas de PDMS/E3D/AutoPLANT/
CADWorx). Aujourd'hui, tout — traçage du tracé, placement des raccords,
cotation, numérotation des soudures, nomenclature, cartouche — est fait à la
main dans MicroStation.

Le format `.dgn` V8 est un conteneur OLE2 propriétaire (données graphiques
compressées en zlib, structure interne non documentée publiquement). L'écrire
ou le lire sans passer par MicroStation demanderait un SDK tiers payant
(ODA/Teigha) et un investissement de plusieurs mois pour une fidélité
incertaine avec ce que produit MicroStation. **Décision retenue : automatiser
MicroStation lui-même plutôt que le remplacer.** MicroStation reste le moteur
de rendu, mais un opérateur ne dessine plus rien à la main.

## Ce qui existe dans ce dépôt (phase 1)

- `iso_engine/` : moteur Python testé qui prend les données du BLE + relevé
  (CSV) et calcule tout ce qu'un dessinateur ferait à la main avant de
  tracer : projection isométrique (convention standard tuyauterie, axes à
  30°), longueurs réelles à coter, numérotation séquentielle des soudures,
  nomenclature agrégée. Sortie : un JSON, seul contrat avec MicroStation.
- `microstation/IsoBuilder.bas` : macro VBA qui lit ce JSON et place les
  éléments dans un `.dgn` ouvert depuis un fichier germe (lignes, cellules
  de raccords, repères de soudure, cotes, nomenclature, cartouche).

Le moteur Python est testé (23 tests, `pytest iso_engine/tests`). La macro
VBA est un **squelette fonctionnellement complet mais non validé sur un
poste MicroStation réel** : elle doit être ajustée à votre bibliothèque de
cellules, votre gabarit et testée avant tout usage en production (voir
`microstation/README.md` pour les limites connues et les prérequis).

## Prochaines phases (proposées, à prioriser ensemble)

1. **Valider la chaîne de bout en bout sur un poste MicroStation réel**
   avec une ligne simple : gabarit (seed file) minimal, une cellule de
   raccord, exécuter `BuildIsoFromJson` sur `examples/sample_drawing.json`,
   corriger les écarts d'API VBA au fil de l'eau.
2. **Vraies cotes et vraie table de nomenclature** MicroStation (au lieu du
   texte brut actuel), et rotation correcte des cellules de raccord — soit
   par calcul de matrice, soit (plus simple) via une bibliothèque de
   cellules pré-orientées par direction isométrique standard.
3. **Table de référence des composants** (longueurs hors-tout / lay lengths
   par type-diamètre-spec) pour que la longueur de tube nomenclaturée soit
   nette des raccords, pas la longueur brute point-à-point.
4. **Saisie facilitée du relevé terrain** : le format CSV actuel est un
   contrat technique, pas un outil de saisie. Si le laser de mesure utilisé
   exporte un format structuré (ex: Bluetooth vers Excel), écrire un
   convertisseur dédié plutôt que de resaisir à la main. À creuser une fois
   le matériel de mesure identifié précisément.
5. **Traitement par lot** : une fois la chaîne validée sur une ligne, le
   gain réel vient de l'enchaîner sur toutes les lignes d'une affaire
   d'un coup (un CSV ou une ligne de BLE par ligne de tuyauterie).

## Ce qu'on ne fait pas (pour l'instant, volontairement)

- Pas de lecture/écriture DGN indépendante de MicroStation (SDK ODA/Teigha) :
  coût et incertitude de fidélité trop élevés pour la valeur ajoutée tant que
  la phase 1 n'a pas prouvé le gain de temps sur le terrain.
- Pas de reconstruction automatique du tracé depuis un nuage de points laser
  scanner : le relevé actuel (laser télémètre ou main) donne des mesures
  ponctuelles, pas un nuage de points 3D dense. Si l'entreprise passe un jour
  à un scanner 3D, ce serait un module d'entrée supplémentaire, pas une
  remise en cause du moteur de calcul.
