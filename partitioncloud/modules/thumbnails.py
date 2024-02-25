"""
Thumbnails
"""
import os
import pypdf

from flask import current_app, abort, Blueprint, send_file

from .auth import login_required

bp = Blueprint("thumbnails", __name__, url_prefix="/thumbnails")


def generate_thumbnail(source, dest):
    """
    Generates a thumbnail with 'convert' (ImageMagick)
    """
    try:
        pypdf.PdfReader(source) # Check if file is really a PDF
    except (pypdf.errors.PdfReadError, pypdf.errors.PdfStreamError):
        return

    command = (
        f"gs -dQUIET -dSAFER -dBATCH -dNOPAUSE -dNOPROMPT -dMaxBitmap=500000000 \
        -dAlignToPixels=0 -dGridFitTT=2 -sDEVICE=png16m -dBackgroundColor=16#FFFFFF -dTextAlphaBits=4 \
        -dGraphicsAlphaBits=4 -r72x72 -dPrinted=false -dFirstPage=1 -dPDFFitPage -g356x356 \
        -dLastPage=1 -sOutputFile={dest} {source}"
    )
    os.system(command)

def serve_thumbnail(partition_file, thumbnail_file):
    """
    Generates thumbnail if non-existent
    """
    if not os.path.exists(partition_file):
        abort(404)

    if not os.path.exists(thumbnail_file):
        generate_thumbnail(partition_file, thumbnail_file)

        if not os.path.exists(thumbnail_file):
            abort(404)

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
