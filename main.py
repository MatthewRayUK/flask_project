from flask import Flask, render_template, redirect, url_for, request
import requests
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField, TimeField, SelectField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import declarative_base, Mapped
from sqlalchemy import Column, Integer, Float, String  # Import the necessary types

# Adding test note here!!!!!

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

Bootstrap(app)

Base = declarative_base()



app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Create DB
class Books(Base):
    __tablename__ = 'books'
    id: Mapped[int] = Column(Integer, primary_key=True)
    title: Mapped[str] = Column(String(250), unique=True, nullable=False)
    year: Mapped[int] = Column(Integer, nullable=False)
    description: Mapped[str] = Column(String(500), nullable=False)
    rating: Mapped[float] = Column(Float, nullable=True)
    ranking: Mapped[int] = Column(Integer, nullable=True)
    isbn: Mapped[int] = Column(Integer, nullable=True)
    review: Mapped[str] = Column(String(250), nullable=True)
    img_url: Mapped[str] = Column(String(250), nullable=False)


with app.app_context():
    db.create_all()





class SearchForm(FlaskForm):
    search = StringField('Type the name of a book or author', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/', methods=["GET", "POST"])
def home():

    # # Manual Add
    # new_book = Books(
    #     title="Project Hail Mary",
    #     year=2021,
    #     img_url="https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1597695864i/54493401.jpg",
    #     description="Great book!!!"
    # )
    # db.session.add(new_book)
    # db.session.commit()

    result = db.session.execute(db.select(Books))
    all_books = result.scalars()


    form = SearchForm()
    if form.validate_on_submit():
        result = form.data.get('search')
        return redirect(url_for('book_search', result=result))
    return render_template('index.html', form=form, all_books=all_books)


# Book API Search
@app.route('/book_search', methods=["GET", "POST"])
def book_search():
    search = request.form.get('search')
    print(search)
    url = f"https://openlibrary.org/search.json?q={search}&limit=8"
    response = requests.get(url)
    data = response.json()
    for x in data["docs"]:
        try:
            author_name, year, title, isbn = x["author_name"], x["first_publish_year"], x["title"], x["isbn"]

            # print(f"Author: {author_name}\nYear: {year}\nTitle: {title}\n")
        except:
            pass
    return render_template('search.html', data=data)

@app.route('/add_book', methods=["GET", "POST"])
def add_book():
    isbn = request.args.get("id")

    # Check if ISBN is provided
    if not isbn:
        return redirect(url_for('home'))

    url = f"https://openlibrary.org/search.json?q={isbn}"
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code != 200:
        return redirect(url_for('home'))

    data = response.json()

    # Check if any books were found
    if not data["docs"]:
        return redirect(url_for('home'))

    try:
        new_book = Books(
            title=data["docs"][0]["title"],
            year=data["docs"][0]["publish_date"][0] if "publish_date" in data["docs"][0] else "Unknown",
            isbn=isbn,
            description=data["docs"][0].get("description", "No description available."),
            img_url=f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
        )

        db.session.add(new_book)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return redirect(url_for('home'))

    return redirect(url_for('home'))


@app.route('/remove_book', methods=["GET", "POST"])
def remove_book():
    isbn = request.args.get("id")

    book_to_remove = Books.query.filter_by(isbn=isbn).first()
    if book_to_remove:
            db.session.delete(book_to_remove)
            db.session.commit()

    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, port =5000)
