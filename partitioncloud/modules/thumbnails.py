"""
Thumbnails
"""
import os

from flask import current_app, abort, Blueprint, send_file

from .db import get_db
from .auth import login_required

bp = Blueprint("thumbnails", __name__, url_prefix="/thumbnails")


def generate_thumbnail(source, dest):
    """
    Generates a thumbnail with 'convert' (ImageMagick)
    """
    os.system(
        f'/usr/bin/convert -thumbnail\
        "178^>" -background white -alpha \
        remove -crop 178x178+0+0 \
        {source}[0] \
        {dest}'
    )

def serve_thumbnail(partition_file, thumbnail_file):
    """
    Generates thumbnail if non-existent
    """
    if not os.path.exists(partition_file):
        abort(404)

    if not os.path.exists(thumbnail_file):
        generate_thumbnail(partition_file, thumbnail_file)

    return send_file(thumbnail_file)


@bp.route("/search/<uuid>.jpg")
@login_required
def search_thumbnail(uuid):
    """
    Renvoie l'apercu d'un résultat de recherche
    """
    return serve_thumbnail(
        os.path.join(current_app.instance_path, "search-partitions", f"{uuid}.pdf"),
        os.path.join(current_app.instance_path, "cache", "search-thumbnails", f"{uuid}.jpg")
    )

@bp.route("/<uuid>.jpg")
def regular_thumbnail(uuid):
    """
    Renvoie l'apercu d'une partition déjà enregistrée
    """
    return serve_thumbnail(
        os.path.join(current_app.instance_path, "partitions", f"{uuid}.pdf"),
        os.path.join(current_app.instance_path, "cache", "thumbnails", f"{uuid}.jpg")
    )