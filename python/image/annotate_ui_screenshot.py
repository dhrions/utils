"""Encadre un widget dans une capture d'écran, sans saisir ses coordonnées à la main.

Problème résolu
---------------
Annoter une capture pour désigner un élément d'interface (« ceci est la barre de
menu ») suppose de connaître son rectangle. Le lire à l'œil sur l'image donne des
cadres qui débordent ou rognent le widget de plusieurs dizaines de pixels.

Principe
--------
Le fond d'un widget a une couleur unie qui diffère de ce qui l'entoure — sous Qt/
Adwaita, un `QMenu` est en (252,252,252), une `QMenuBar` en (245,245,245), la page
en dessous en (255,255,255). Il suffit donc de partir d'un point *intérieur* au
widget, de sélectionner les pixels de cette couleur, et de prendre la composante
connexe qui contient ce point : sa bounding box est le widget, au pixel près. Le
texte et les séparateurs ne sont que des trous — le fond reste connexe autour.

Seul un point intérieur approximatif est à fournir, le reste est déterminant.

Pièges rencontrés (approches qui échouent)
------------------------------------------
* Seuiller sur « pixel clair » plutôt que sur la couleur exacte : la bordure
  antialiasée passe le seuil et relie le widget au blanc de la page — la
  composante déborde alors sur toute la fenêtre.
* Prendre le mode des extrémités de segments clairs ligne à ligne : une colonne
  de raccourcis clavier alignée verticalement fait converger le mode sur le
  texte, pas sur le bord.
* Prendre le taux d'occupation par ligne : un libellé long fait chuter le taux
  sous le seuil et tronque le widget.
* Combler les trous par fermeture morphologique : la bordure ne fait que
  quelques pixels, la fermeture la franchit et avale la fenêtre entière.

Une ligne surlignée (sélection) a une couleur propre : la passer en
`--extra-color` pour qu'elle ne coupe pas la composante en deux.

Exemple
-------
    python annotate_ui_screenshot.py capture.png annotee.png \
        --box 1400,700:QMenu:above-left \
        --extra-color 144,175,243
"""

from __future__ import annotations

import click
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import find_objects, label

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
POSITIONS = ("above-left", "above-right", "inside-left", "inside-right")


def detect_panel(array, seed, tol=3, extra_colors=(), max_area_ratio=0.9):
    """Bounding box (x0, y0, x1, y1) du widget contenant le point `seed`.

    `seed` est un (x, y) intérieur au widget, sur une zone de fond (pas sur du
    texte). `tol` absorbe le bruit de compression. `extra_colors` ajoute des
    couleurs au masque (ligne surlignée, en-tête coloré) pour que la composante
    ne soit pas scindée.

    Lève `ValueError` si la boîte couvre plus de `max_area_ratio` de l'image :
    c'est le signe que la composante a fui hors du widget (tolérance trop large,
    ou point de départ posé sur un fond partagé avec le reste de la fenêtre).
    """
    sx, sy = seed
    mask = (np.abs(array - array[sy, sx]) <= tol).all(axis=2)
    for color in extra_colors:
        mask |= (np.abs(array - np.array(color)) <= tol).all(axis=2)

    labels, _ = label(mask)
    target = labels[sy, sx]
    ys, xs = find_objects(labels)[target - 1]
    x0, y0, x1, y1 = xs.start, ys.start, xs.stop - 1, ys.stop - 1

    height, width = array.shape[:2]
    if (x1 - x0) * (y1 - y0) > max_area_ratio * width * height:
        raise ValueError(
            f"la zone détectée depuis {seed} couvre presque toute l'image "
            f"({x0}, {y0}, {x1}, {y1}) : la couleur de fond n'isole pas le widget. "
            f"Baisser --tol, ou choisir un point sur un fond propre au widget.")
    return x0, y0, x1, y1


def annotate(src, dst, boxes, *, color=(220, 38, 38), line_width=5, pad=5,
             font_size=34, tol=3, extra_colors=(), font_path=FONT_PATH):
    """Dessine un cadre étiqueté autour de chaque widget désigné par `boxes`.

    `boxes` est une liste de (seed, label, position). L'étiquette est posée hors
    du cadre quand la place existe, pour ne masquer aucun contenu.
    """
    image = Image.open(src).convert("RGB")
    array = np.asarray(image).astype(int)
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except OSError as e:
        raise OSError(
            f"Police introuvable : {font_path!r}. Installer le paquet "
            f"fonts-dejavu-core, ou fournir un autre chemin TTF via --font."
        ) from e
    width, height = image.size

    for seed, text, position in boxes:
        x0, y0, x1, y1 = detect_panel(array, seed, tol, extra_colors)
        x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
        draw.rectangle([x0, y0, x1, y1], outline=color, width=line_width)

        bbox = draw.textbbox((0, 0), text, font=font)
        inner = 10
        box_w = bbox[2] - bbox[0] + 2 * inner
        box_h = bbox[3] - bbox[1] + 2 * inner

        bx = x0 if position.endswith("-left") else x1 - box_w
        by = y0 - box_h if position.startswith("above") else y0
        if by < 0:  # pas de place au-dessus : bascule sous le cadre
            by = y1
        bx = max(0, min(bx, width - box_w))
        by = max(0, min(by, height - box_h))

        draw.rectangle([bx, by, bx + box_w, by + box_h], fill=color)
        draw.text((bx + inner, by + inner - bbox[1]), text, font=font, fill="white")

    image.save(dst)
    return dst


def _color_from_str(value):
    try:
        r, g, b = (int(n) for n in value.split(","))
    except ValueError:
        raise click.BadParameter(f"format attendu 'R,V,B', reçu {value!r}")
    return r, g, b


def _parse_boxes(ctx, param, values):
    """`x,y:Étiquette:position` -> ((x, y), 'Étiquette', 'position')."""
    boxes = []
    for value in values:
        try:
            point, text, position = value.split(":")
            x, y = (int(n) for n in point.split(","))
        except ValueError:
            raise click.BadParameter(
                f"format attendu 'x,y:Étiquette:position', reçu {value!r}")
        if position not in POSITIONS:
            raise click.BadParameter(
                f"position {position!r} inconnue (au choix : {', '.join(POSITIONS)})")
        boxes.append(((x, y), text, position))
    return boxes


def _parse_extra_colors(ctx, param, values):
    return [_color_from_str(v) for v in values]


@click.command()
@click.argument("source", type=click.Path(exists=True, dir_okay=False))
@click.argument("destination", type=click.Path())
@click.option(
    "--box", "boxes", multiple=True, required=True, callback=_parse_boxes,
    metavar="X,Y:TEXTE:POS",
    help="point intérieur au widget, étiquette, et placement de l'étiquette "
         f"({'|'.join(POSITIONS)}) ; répétable")
@click.option(
    "--extra-color", "extra_colors", multiple=True, callback=_parse_extra_colors,
    metavar="R,V,B", help="couleur supplémentaire à inclure au masque (ligne surlignée) ; répétable")
@click.option("--tol", type=int, default=3, help="tolérance de couleur, par défaut 3")
@click.option(
    "--color", type=str, default="220,38,38", callback=lambda ctx, param, value: _color_from_str(value),
    metavar="R,V,B", help="couleur du cadre, par défaut 220,38,38")
@click.option("--font", default=FONT_PATH,
              help=f"chemin de la police TTF, par défaut {FONT_PATH}")
def main(source, destination, boxes, extra_colors, tol, color, font):
    """Encadre un widget dans une capture d'écran, sans saisir ses coordonnées à la main."""
    annotate(source, destination, boxes,
             color=color, tol=tol, extra_colors=extra_colors, font_path=font)
    click.echo(destination)


if __name__ == "__main__":
    main()
