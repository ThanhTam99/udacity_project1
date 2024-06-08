# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from forms import ArtistForm, VenueForm, ShowForm
from sqlalchemy import func
from sqlalchemy.orm import noload
from sqlalchemy.exc import SQLAlchemyError
from helper import group_by, group_by_multiple_key
from flask_migrate import Migrate
from datetime import datetime
from models import db, Venue, Artist, Show

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db.init_app(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value) if isinstance(value, str) else value
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


@app.route("/venues")
def venues():
    query_result = (
        Venue.query.with_entities(
            Venue.id,
            Venue.state,
            Venue.city,
            Venue.name,
            func.count(Show.venue_id).label("num_upcoming_shows"),
        )
        .outerjoin(Show, Show.venue_id == Venue.id)
        .group_by(Venue.id, Venue.state, Venue.city, Venue.name, Show.venue_id)
        .order_by(Venue.state, Venue.city)
        .all()
    )

    data = group_by_multiple_key(
        query_result,
        lambda item: (item.city, item.state),
        lambda item: {
            "id": item.id,
            "name": item.name,
            "num_upcoming_shows": item.num_upcoming_shows,
        },
        ["city", "state"],
        "venues",
    )

    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    search = f'%{request.form["search_term"].lower()}%'

    query_result = (
        Venue.query.with_entities(
            Venue.id, Venue.name, func.count(Show.id).label("num_upcoming_shows")
        )
        .outerjoin(Show, Show.venue_id == Venue.id)
        .filter(Venue.name.ilike(search))
        .group_by(Venue.id, Venue.name, Show.venue_id)
        .all()
    )
    response = {"count": len(query_result), "data": query_result}

    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)

    data = venue.__dict__

    print(data['website_link'])

    shows = group_by(
        venue.shows,
        lambda item: item.start_time < datetime.today().astimezone(),
        lambda item: {
            "start_time": item.start_time,
            "artist_id": item.artist_id,
            "artist_name": item.artist.name,
            "artist_image_link": item.artist.image_link,
        },
    )

    data["past_shows"] = shows.get(True, [])
    data["past_shows_count"] = len(data["past_shows"])

    data["upcoming_shows"] = shows.get(False, [])
    data["upcoming_shows_count"] = len(data["upcoming_shows"])

    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    try:
        venue_form = VenueForm(request.form, meta={"csrf": False})

        if venue_form.validate():
            new_venue = Venue()
            venue_form.populate_obj(new_venue)
            db.session.add(new_venue)
            db.session.commit()

            flash("Venue " + request.form["name"] + " was successfully listed!")

            return redirect("/venues")

    except SQLAlchemyError:
        db.session.rollback()

        flash(
            "Failed to create venue with name: "
            + request.form["name"]
            + ". Please contact page admin!"
        )

    return render_template("forms/new_venue.html", form=venue_form)


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get_or_404(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()

    return redirect("/venues")


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    data = Artist.query.with_entities(Artist.id, Artist.name).all()

    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    search = f'%{request.form["search_term"].lower()}%'

    query_result = (
        Artist.query.with_entities(
            Artist.id, Artist.name, func.count(Show.id).label("num_upcoming_shows")
        )
        .join(Show, Show.venue_id == Artist.id)
        .filter(Artist.name.ilike(search))
        .group_by(Artist.id, Artist.name, Show.venue_id)
        .all()
    )
    response = {"count": len(query_result), "data": query_result}
    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    data = artist.__dict__

    shows = group_by(
        artist.shows,
        lambda item: item.start_time < datetime.today().astimezone(),
        lambda item: {
            "start_time": item.start_time,
            "venue_id": item.venue_id,
            "venue_image_link": item.venue.image_link,
            "venue_name": item.venue.name,
        },
    )

    data["past_shows"] = shows.get(True, [])
    data["past_shows_count"] = len(data["past_shows"])

    data["upcoming_shows"] = shows.get(False, [])
    data["upcoming_shows_count"] = len(data["upcoming_shows"])

    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.options(noload(Artist.shows)).get_or_404(artist_id)
    # TODO: populate form with fields from artist with ID <artist_id>

    form.name.data = artist.name
    form.state.data = artist.state
    form.city.data = artist.city
    form.genres.data = artist.genres
    form.phone.data = artist.phone
    form.image_link.data = artist.image_link
    form.website_link.data = artist.website_link
    form.seeking_venue.data = artist.seeking_venue

    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    try:
        artist_form = ArtistForm(request.form, meta={"csrf": False})

        if artist_form.validate():
            editting_artist = Artist.query.options(noload(Artist.shows)).get_or_404(
                artist_id
            )

            artist_form.populate_obj(editting_artist)

            db.session.commit()

            return redirect("/artists")
    except SQLAlchemyError:
        db.session.rollback()

    return render_template(
        "forms/edit_artist.html", form=artist_form, artist=editting_artist
    )


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()

    venue = Venue.query.options(noload(Venue.shows)).get_or_404(venue_id)

    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    try:
        venue_form = VenueForm(request.form, meta={"csrf": False})

        if venue_form.validate():
            editting_venue = Venue.query.options(noload(Venue.shows)).get_or_404(
                venue_id
            )

            venue_form.populate_obj(editting_venue)

            db.session.commit()
            flash("Update venue successfully!")

            return redirect("/venues")
    except SQLAlchemyError:
        db.session.rollback()

    return render_template(
        "forms/edit_venue.html", form=venue_form, venue=editting_venue
    )


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    try:
        artist_form = ArtistForm(request.form, meta={"csrf": False})

        if artist_form.validate():
            new_artist = Artist()
            artist_form.populate_obj(new_artist)
            db.session.add(new_artist)
            db.session.commit()

            flash("Artist " + request.form["name"] + " was successfully listed!")
            return redirect("/artists")

    except SQLAlchemyError:
        db.session.rollback()
        flash(
            "Failed to create artist with name = "
            + request.form["name"]
            + ". Please contact admin!"
        )

    return render_template("forms/new_artist.html", form=artist_form)


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    data = (
        Show.query.with_entities(
            Show.venue_id,
            Venue.name.label("venue_name"),
            Show.artist_id,
            Artist.name.label("artist_name"),
            Artist.image_link.label("artist_image_link"),
            Show.start_time,
        )
        .outerjoin(Venue, Venue.id == Show.venue_id)
        .outerjoin(Artist, Artist.id == Show.artist_id)
        .order_by(Show.start_time)
        .all()
    )

    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    artists = Artist.query.all()
    venues = Venue.query.all()
    form = ShowForm(venues=venues, artists=artists)

    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    try:
        artists = Artist.query.all()
        venues = Venue.query.all()
        show_form = ShowForm(
            request.form, meta={"csrf": False}, venues=venues, artists=artists
        )

        if show_form.validate():
            new_show = Show()
            show_form.populate_obj(new_show)
            db.session.add(new_show)
            db.session.commit()

            flash("Show was successfully listed!")
            return redirect("/shows")

    except SQLAlchemyError:
        db.session.rollback()

        flash("Failed to create show")

    return render_template("pages/new_show.html", form=show_form)


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
