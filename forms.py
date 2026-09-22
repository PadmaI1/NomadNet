from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from models import User


class LoginForm(FlaskForm):
    """
    Form for user login.

    The user provides username and password.
    WTF automatically validates that fields are not empty.
    """
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required.'),
            Length(min=1, max=80)
        ]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message='Password is required.')]
    )
    submit = SubmitField('Login')


class SignupForm(FlaskForm):
    """
    Form for user registration.

    Validators run BEFORE the route handler.
    custom_validate_username and custom_validate_email are called by WTF
    automatically to check database state.
    """
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required.'),
            Length(min=3, max=80, message='Username must be between 3 and 80 characters.')
        ]
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Invalid email address.')
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),
            Length(min=6, message='Password must be at least 6 characters.')
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords must match.')
        ]
    )
    submit = SubmitField('Sign Up')

    def validate_username(self, field):
        """
        Custom validator: check if username already exists in database.

        WTF calls this automatically because the method name is validate_<fieldname>.
        If we raise ValidationError, WTF adds it to form.errors.
        """
        existing_user = User.query.filter_by(username=field.data).first()
        if existing_user:
            raise ValidationError('Username already exists. Please choose a different username.')

    def validate_email(self, field):
        """Custom validator: check if email already exists in database."""
        existing_user = User.query.filter_by(email=field.data).first()
        if existing_user:
            raise ValidationError('Email already exists. Please choose a different email.')


class CreatePostForm(FlaskForm):
    """
    Form for creating a new post.

    Content is required and must not be empty.
    Location ID is a hidden field (set by JavaScript).
    Media files are optional (user can post without images/videos).
    """
    content = TextAreaField(
        'What are you experiencing?',
        validators=[
            DataRequired(message='Post cannot be empty.'),
            Length(min=1, max=5000, message='Post must be less than 5000 characters.')
        ],
        render_kw={'rows': 4, 'placeholder': 'Share your thoughts, stories, tips...'}
    )
    location_id = HiddenField(
        'location_id',
        validators=[DataRequired(message='Please select a location.')]
    )
    media = FileField(
        'Add images or videos',
        validators=[
            FileAllowed(
                ['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'webm', 'mov'],
                message='Only image (jpg, jpeg, png, gif, webp) and video (mp4, webm, mov) files are allowed.'
            )
        ],
        render_kw={'multiple': True}
    )
    submit = SubmitField('Post')


class EditPostForm(FlaskForm):
    """
    Form for editing an existing post.

    Similar to CreatePostForm, but also allows deleting media.
    """
    content = TextAreaField(
        'Update your post',
        validators=[
            DataRequired(message='Post cannot be empty.'),
            Length(min=1, max=5000, message='Post must be less than 5000 characters.')
        ],
        render_kw={'rows': 4}
    )
    location_id = HiddenField(
        'location_id',
        validators=[DataRequired(message='Please select a location.')]
    )
    media = FileField(
        'Add more images or videos',
        validators=[
            FileAllowed(
                ['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'webm', 'mov'],
                message='Only image (jpg, jpeg, png, gif, webp) and video (mp4, webm, mov) files are allowed.'
            )
        ],
        render_kw={'multiple': True}
    )
    submit = SubmitField('Save Changes')


class CreateCommentForm(FlaskForm):
    """
    Form for adding a comment to a post.

    Content is required and must not be empty.
    """
    content = TextAreaField(
        'Add a comment',
        validators=[
            DataRequired(message='Comment cannot be empty.'),
            Length(min=1, max=1000, message='Comment must be less than 1000 characters.')
        ],
        render_kw={'rows': 3, 'placeholder': 'Write a comment...'}
    )
    submit = SubmitField('Comment')


class DeleteAccountForm(FlaskForm):
    """
    Form for deleting a user account.

    No fields — this is just a form to hold the CSRF token
    so that the delete button is protected against CSRF attacks.
    """
    submit = SubmitField('Delete My Account')


class LogoutForm(FlaskForm):
    """
    Form for logging out.

    Like DeleteAccountForm, this just holds the CSRF token.
    """
    submit = SubmitField('Logout')
