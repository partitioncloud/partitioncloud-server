#!/usr/bin/python3
"""
Partitions module
"""
import os

from flask import (Blueprint, render_template,
                   send_file)


bp = Blueprint("partition", __name__, url_prefix="/partition")

@bp.route("/<uuid>/preview")
def preview(uuid):
    """
    Renvoie la prévisualisation d'un fichier pdf
    """
    if not os.path.exists(f"partitioncloud/thumbnails/{uuid}.jpg"):
        os.system(
            f'/usr/bin/convert -thumbnail\
            "178^>" -background white -alpha \
            remove -crop 178x178+0+0 \
            partitioncloud/partitions/{uuid}.pdf[0] \
            partitioncloud/thumbnails/{uuid}.jpg'
        )

    return send_file(f"thumbnails/{uuid}.jpg")