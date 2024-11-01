from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ingredients.db'
app.config['UPLOAD_FOLDER'] = 'instance/uploads'
db = SQLAlchemy(app)


# Modelle bleiben größtenteils gleich


class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    variants = db.relationship('Variant', backref='ingredient', lazy=True)


class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    variants = db.relationship('Variant', backref='store', lazy=True)


class Variant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey(
        'ingredient.id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    image_path = db.Column(db.String(200))
    reviews = db.relationship('Review', backref='variant', lazy=True)

    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        return sum(review.rating for review in self.reviews) / len(self.reviews)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, db.ForeignKey(
        'variant.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routen


@app.route('/')
def index():
    store_filter = request.args.get('store')
    stores = Store.query.order_by(Store.name).all()

    if store_filter:
        ingredients = Ingredient.query.join(Variant).join(Store).filter(
            Store.id == store_filter
        ).order_by(Ingredient.name).all()
    else:
        ingredients = Ingredient.query.order_by(Ingredient.name).all()

    return render_template('index.html', ingredients=ingredients, stores=stores, selected_store=store_filter)


@app.route('/ingredient/add', methods=['POST'])
def add_ingredient():
    name = request.form.get('name')

    existing_Ingredient = Ingredient.query.filter(
        Ingredient.name.ilike(name)).first()

    print(existing_Ingredient)
    if existing_Ingredient:
        return jsonify({'error': 'Zutat existiert bereits'}), 400

    if name:
        ingredient = Ingredient(name=name)
        db.session.add(ingredient)
        db.session.commit()
        flash('Zutat erfolgreich hinzugefügt!', 'success')
        return jsonify({'success': True}), 200
    return redirect(url_for('index'))


@app.route('/ingredient/<int:id>')
def ingredient_details(id):
    ingredient = Ingredient.query.get_or_404(id)

    # Berechne die durchschnittliche Bewertung in der Datenbankabfrage
    variants = db.session.query(
        Variant,
        func.avg(Review.rating).label('avg_rating')
    ).outerjoin(
        Review
    ).filter(
        Variant.ingredient_id == id
    ).group_by(
        Variant.id
    ).order_by(
        func.avg(Review.rating).desc().nullslast()
    ).all()

    # Extrahiere die Varianten aus dem Abfrageergebnis
    variants = [v[0] for v in variants]

    stores = Store.query.all()
    return render_template('ingredient_details.html', ingredient=ingredient, variants=variants, stores=stores)


@app.route('/variant/add', methods=['POST'])
def add_variant():
    ingredient_id = request.form.get('ingredient_id')
    store_id = request.form.get('store_id')
    name = request.form.get('name')
    price = request.form.get('price')
    quantity = request.form.get('quantity')

    if 'image' in request.files:
        file = request.files['image']
        if file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = filename
        else:
            image_path = None

    variant = Variant(
        ingredient_id=ingredient_id,
        store_id=store_id,
        name=name,
        price=price,
        quantity=quantity,
        image_path=image_path
    )
    db.session.add(variant)
    db.session.commit()
    flash('Variante erfolgreich hinzugefügt!', 'success')
    return redirect(url_for('ingredient_details', id=ingredient_id))


@app.route('/review/add', methods=['POST'])
def add_review():
    variant_id = request.form.get('variant_id')
    rating = request.form.get('rating')
    comment = request.form.get('comment')

    review = Review(
        variant_id=variant_id,
        rating=rating,
        comment=comment
    )
    db.session.add(review)
    db.session.commit()

    variant = Variant.query.get(variant_id)
    flash('Bewertung erfolgreich hinzugefügt!', 'success')
    return redirect(url_for('ingredient_details', id=variant.ingredient_id))


@app.route('/store/add', methods=['POST'])
def add_store():
    data = request.get_json()
    store_name = data.get('name')

    if not store_name:
        return jsonify({'success': False, 'error': 'Geschäftsname ist erforderlich'})

    # Prüfe, ob das Geschäft bereits existiert
    existing_store = Store.query.filter(Store.name.ilike(store_name)).first()
    if existing_store:
        return jsonify({'success': False, 'error': 'Geschäft existiert bereits'})

    try:
        store = Store(name=store_name)
        db.session.add(store)
        db.session.commit()
        return jsonify({
            'success': True,
            'id': store.id,
            'name': store.name
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
