import re
from datetime import datetime
from flask_wtf import FlaskForm as Form
from wtforms import (
    StringField,
    SelectField,
    SelectMultipleField,
    DateTimeField,
    BooleanField,
    ValidationError,
)
from wtforms.validators import DataRequired, URL
from enums import Genres, States


def is_valid_phone(phone):
    regex = re.compile(r"^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})")
    return regex.match(phone)


class ShowForm(Form):
    def __init__(self, formdata=None, **kwargs):
        super().__init__(formdata, **kwargs)

        if "artists" in kwargs:
            self.artist_id.choices = [
                (artist.id, artist.name) for artist in kwargs["artists"]
            ]

        if "venues" in kwargs:
            self.venue_id.choices = [
                (venue.id, venue.name) for venue in kwargs["venues"]
            ]

    artist_id = SelectField("artist_id", validators=[DataRequired()])
    venue_id = SelectField("venue_id", validators=[DataRequired()])
    start_time = DateTimeField(
        "start_time", validators=[DataRequired()], default=datetime.today()
    )


class VenueForm(Form):
    name = StringField("name", validators=[DataRequired()])
    city = StringField("city", validators=[DataRequired()])
    state = SelectField(
        "state",
        validators=[DataRequired()],
        choices=States.choices(),
    )
    address = StringField("address", validators=[DataRequired()])
    phone = StringField("phone")
    image_link = StringField("image_link")
    genres = SelectMultipleField(
        # TODO implement enum restriction
        "genres",
        validators=[DataRequired()],
        choices=Genres.choices(),
    )
    facebook_link = StringField("facebook_link", validators=[URL()])
    website_link = StringField("website_link")

    seeking_talent = BooleanField("seeking_talent")

    seeking_description = StringField("seeking_description")

    def validate_phone(self, field):
        if not is_valid_phone(field.data):
            raise ValidationError("Invalid phone")

    def validate_state(self, field):
        if field.data not in dict(States.choices()).keys():
            raise ValidationError("Invalid genres")

    def validate_genres(self, field):
        if not set(field.data).issubset(dict(Genres.choices()).keys()):
            raise ValidationError("Invalid genres")
        

    def validate(self, **kwargs):
        return super(VenueForm, self).validate(**kwargs)


class ArtistForm(Form):
    name = StringField("name", validators=[DataRequired()])
    city = StringField("city", validators=[DataRequired()])
    state = SelectField(
        "state",
        validators=[DataRequired()],
        choices=States.choices(),
    )
    phone = StringField(
        # TODO implement validation logic for state
        "phone"
    )
    image_link = StringField("image_link")
    genres = SelectMultipleField(
        "genres",
        validators=[DataRequired()],
        choices=Genres.choices(),
    )
    facebook_link = StringField(
        # TODO implement enum restriction
        "facebook_link",
        validators=[URL()],
    )

    website_link = StringField("website_link")

    seeking_venue = BooleanField("seeking_venue")

    seeking_description = StringField("seeking_description")

    def validate_phone(self, field):
        if not is_valid_phone(field.data):
            raise ValidationError("Invalid phone")

    def validate_state(self, field):
        if field.data not in dict(States.choices()).keys():
            raise ValidationError("Invalid genres")

    def validate_genres(self, field):
        if not set(field.data).issubset(dict(Genres.choices()).keys()):
            raise ValidationError("Invalid genres")

    def validate(self, **kwargs):
        return super(ArtistForm, self).validate(**kwargs)
