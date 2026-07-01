# software-tuyauterie

Outillage pour automatiser la production des mises en plan isométriques de
tuyauterie (livrable client au format `.dgn` / MicroStation), à partir des
données du BLE et du relevé terrain.

Contexte et feuille de route complète : [`docs/workflow.md`](docs/workflow.md).

## Principe

```
BLE + relevé terrain (CSV)  --->  iso_engine (Python)  --->  drawing.json  --->  IsoBuilder.bas (MicroStation VBA)  --->  .dgn
```

`iso_engine` calcule tout ce qu'un dessinateur fait à la main avant de
tracer un isométrique : projection isométrique du tracé relevé, longueurs
réelles à coter, numérotation séquentielle des soudures, nomenclature
agrégée. La macro MicroStation ne fait que placer les éléments à partir de
ce résultat déjà calculé — MicroStation reste le moteur de dessin (format
`.dgn` imposé par le client), mais plus personne ne trace à la main.

## Démarrage rapide

```bash
pip install -r requirements-dev.txt   # pytest uniquement, aucune dépendance pour le moteur lui-même
pytest iso_engine/tests               # 23 tests

python3 -c "
from iso_engine.input_parser import parse_iso_line
from iso_engine.export import export_json
line = parse_iso_line('examples/sample_header.csv', 'examples/sample_points.csv')
export_json(line, 'examples/sample_drawing.json')
"
```

Le JSON obtenu (`examples/sample_drawing.json`) est ensuite consommé par
`microstation/IsoBuilder.bas` (voir [`microstation/README.md`](microstation/README.md)
pour la mise en place côté MicroStation).

## Contenu du dépôt

- `iso_engine/` — moteur de calcul Python (testé, sans dépendance MicroStation)
- `microstation/` — macro VBA de dessin + notice de mise en place
- `docs/data_schema.md` — format exact des CSV d'entrée (BLE + relevé)
- `docs/workflow.md` — contexte, décisions techniques, feuille de route
- `examples/` — exemple de ligne complet (entrée CSV + JSON calculé)

## État actuel

Le moteur de calcul (`iso_engine`) est testé et fonctionnel. La macro
MicroStation est un squelette complet mais **non encore validé sur un poste
MicroStation réel** — prochaine étape prioritaire, voir `docs/workflow.md`.
