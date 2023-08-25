from datetime import datetime

from flask import Flask, render_template, session, redirect, url_for, request, flash
from flask_wtf.file import FileAllowed
from sqlalchemy import desc

from model import db, User, Order, OrderItem, Product, Category, Status
from flask_bootstrap import Bootstrap
import requests

from flask_wtf import FlaskForm
from flask_uploads import UploadSet, configure_uploads, IMAGES
from wtforms import StringField, TextAreaField, FloatField, IntegerField, FileField
from wtforms.validators import InputRequired, Email, DataRequired, Length

application = Flask(__name__)
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop3.db'
application.config['SECRET_KEY'] = b'5f214cacbd30c2ae4784b520f17912ae0d5d8c16ae98128e3f549546221265e4'
db.init_app(application)
bootstrap = Bootstrap(application)
token = "5752718030:AAEBGLw2EdizW2nMPoKnSCUCvYTG4baDFpc"
url = f"https://api.telegram.org/bot{token}/sendMessage"

photos = UploadSet('photos', IMAGES)
application.config['UPLOADED_PHOTOS_DEST'] = 'static/img'
configure_uploads(application, photos)


class AddProductForm(FlaskForm):
    product_name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=6)])
    price = FloatField('Price', validators=[DataRequired()])
    size = StringField('Size', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    photo = FileField('Photo', validators=[DataRequired(), FileAllowed(photos, 'Images only!')])
    category_id = IntegerField('Category ID', validators=[DataRequired()])


class AddUserForm(FlaskForm):
    FirstName = StringField('FirstName', validators=[DataRequired()])
    LastName = StringField('LastName', validators=[DataRequired()])
    Email = StringField('Email', validators=[DataRequired(), Email()])
    Phone = StringField('Phone', validators=[DataRequired(), Length(min=11)])
    Address = StringField('Address', validators=[DataRequired()])


@application.route('/')
def start():
    return redirect(url_for('index'))


@application.route('/index', methods=['GET', 'POST'])
def index():
    page_choice = request.args.get('page')
    TG_ID_get = request.args.get('TG_ID')
    if 'user' not in session and TG_ID_get:
        session['user'] = [{
            'TG_ID': TG_ID_get
        }]
    if TG_ID_get is None and 'user' not in session:
        TG_ID = 228212492
    else:
        user_data = session.get('user', [{}])[0]
        TG_ID = user_data.get('TG_ID')
        if User.query.filter_by(TG_ID=TG_ID).first() is None:
            user = User(
                TG_ID=TG_ID
            )
            db.session.add(user)
            db.session.flush()
            db.session.commit()
    user = User.query.filter_by(TG_ID=TG_ID).first()
    categorys = Category.query.all()
    item_search = request.args.get('search')
    CategoryID = request.args.get('catID')

    if page_choice == 'cart':
        cart_products = []
        total_price = 0
        form = AddUserForm(obj=user)
        request_form = request.args.get('request_form')
        if request_form and form.validate():
            user.FirstName = form.FirstName.data
            user.LastName = form.LastName.data
            user.Email = form.Email.data
            user.Phone = form.Phone.data
            user.Address = form.Address.data

            db.session.commit()

            total_price = 0
            for item in session['cart']:
                product = Product.query.get(item['product_id'])
                count = item['count']
                total_price += product.Price * count
            try:
                # Create a new order
                order = Order(
                    UserID=user.UserID,  # Replace with the actual user ID
                    OrderDate=datetime.utcnow(),
                    TotalAmount=total_price,
                    StatusID=1,  # Replace with the appropriate status ID
                )
                db.session.add(order)
                db.session.flush()  # To get the auto-generated OrderID

                # Create order items
                for cart_item in session['cart']:
                    product = Product.query.get(cart_item['product_id'])
                    if product and cart_item['count'] <= product.Quantity:
                        order_item = OrderItem(
                            OrderID=order.OrderID,
                            ProductID=cart_item['product_id'],
                            Quantity=cart_item['count'],
                        )
                        db.session.add(order_item)
                        product.Quantity -= cart_item['count']

                db.session.commit()
                chat_id = 228212490
                message = "Новый заказ"
                payload = {
                    "chat_id": chat_id,
                    "text": message
                }
                response = requests.post(url, data=payload)
                print(response.content)
                session.pop('cart', None)
                return redirect(url_for('index', page='order'))
            except Exception as e:
                db.session.rollback()
        if 'cart' in session:
            for item in session['cart']:
                product = Product.query.get(item['product_id'])
                count = item['count']
                total_price += product.Price * count
                cart_products.append({'product': product, 'count': count})

        return render_template('cart.html', cart_products=cart_products, total_price=total_price, user=user,
                               categorys=categorys, form=form)

    elif page_choice == 'order':
        categorys = Category.query.all()
        if TG_ID == '228212490':
            orders = Order.query.order_by(desc(Order.OrderDate)).all()
            user = User.query.filter_by(TG_ID=TG_ID).first()
        else:
            user = User.query.filter_by(TG_ID=TG_ID).first()
            orders = Order.query.filter_by(UserID=user.UserID).order_by(desc(Order.OrderDate)).all()
        return render_template('orders.html', orders=orders, user=user, categorys=categorys)

    elif page_choice == 'edit' and TG_ID == '228212490':
        products = Product.query.all()
        search = request.form.get('search')
        print(search)
        if search:
            products = Product.query.filter(Product.ProductName.ilike(f'%{search}%')).all()
        return render_template('edit.html', products=products, categorys=categorys, user=user)

    elif page_choice == 'add_product' and TG_ID == '228212490':
        form = AddProductForm()
        photo_filename = None
        request_form = request.args.get('request_form')
        if form.photo.data:
            if form.photo.data.filename.endswith(('jpg', 'jpeg', 'png')):
                photo_filename = f"img/{photos.save(form.photo.data)}"
            else:
                flash('Invalid photo format. Only JPG, JPEG, and PNG formats are allowed.', 'danger')
        if request_form and form.validate():
            new_product = Product(
                ProductName=form.product_name.data,
                Description=form.description.data,
                Price=form.price.data,
                Size=form.size.data,
                Quantity=form.quantity.data,
                ImgUrl=photo_filename,
                CategoryID=form.category_id.data
            )
            db.session.add(new_product)
            db.session.commit()
        return render_template('add_product.html', form=form, categorys=categorys, user=user)



    elif page_choice == 'users' and TG_ID == '228212490':
        users = User.query.all()
        massages = request.form.get('massages')  # Name corrected to 'massages'
        TG_ID_user = request.args.get('TG_ID')
        delete = request.args.get('delete')
        search = request.form.get('search')
        massage_all = request.form.get('massages_all')  # Corrected to 'massages_all'
        print(search)

        if massages:
            payload = {
                "chat_id": TG_ID_user,
                "text": massages
            }
            requests.post(url, data=payload)
        elif massage_all:
            for user in users:
                payload = {
                    "chat_id": user.TG_ID,
                    "text": massage_all
                }
                requests.post(url, data=payload)
        elif delete:
            user_del = User.query.get(delete)
            db.session.delete(user_del)
            db.session.commit()
        elif search:
            if User.query.filter(User.TG_ID.ilike(f'%{search}%')).all():
                users = User.query.filter(User.TG_ID.ilike(f'%{search}%')).all()
            elif User.query.filter(User.FirstName.ilike(f'%{search}%')).all():
                users = User.query.filter(User.FirstName.ilike(f'%{search}%')).all()
            elif User.query.filter(User.LastName.ilike(f'%{search}%')).all():
                users = User.query.filter(User.LastName.ilike(f'%{search}%')).all()
            else:
                users = User.query.all()

        return render_template('users.html', categorys=categorys, user=user, users=users)

    if CategoryID is None and item_search is None:
        products = Product.query.all()
    elif item_search is None and CategoryID:
        products = Product.query.filter_by(CategoryID=CategoryID).all()
    elif CategoryID is None and item_search:
        products = Product.query.filter(Product.ProductName.ilike(f'%{item_search}%')).all()
    else:
        products = Product.query.all()

    if 'cart' not in session:
        session['cart'] = []
    cart_count = {item['product_id']: item['count'] for item in session['cart']}
    for product in products:
        try:
            if cart_count[product.ProductID] and cart_count[product.ProductID] > product.Quantity:
                if product.Quantity <= 0:
                    del cart_count[product.ProductID]
                else:
                    cart_count[product.ProductID] = product.Quantity
        except KeyError:
            pass
    session['cart'] = [{'product_id': k, 'count': v} for k, v in cart_count.items()]
    print(f"---Сессия запущена {session['cart']}")

    total_price = 0
    if 'cart' in session:
        for item in session['cart']:
            product = Product.query.get(item['product_id'])
            count = item['count']
            total_price += product.Price * count

    return render_template('index.html', products=products, cart_count=cart_count, total_price=total_price, user=user,
                           categorys=categorys)


@application.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    count = int(request.args.get('count', 1))
    cart_count = {item['product_id']: item['count'] for item in session['cart']}
    if product_id in cart_count:
        cart_count[product_id] = count
        if count == 0:
            del cart_count[product_id]
        session['cart'] = [{'product_id': k, 'count': v} for k, v in cart_count.items()]
    else:
        session['cart'] += [{
            'product_id': product_id,
            'count': count
        }]
    db.session.commit()
    print(f"---Успешно дообавленно в сессию {session['cart']}")

    return "Product added to cart"


@application.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    new_status = request.form['status']
    order = Order.query.get(order_id)
    status = Status.query.filter_by(Status=new_status).first()

    chat_id = order.user.TG_ID

    if order:
        if new_status == "Отменен":
            for item in order.order_items:
                product = Product.query.get(item.ProductID)
                if product:
                    product.Quantity += item.Quantity
            message = "Заказ отменен, попробуйте зказать снова"
            payload = {
                "chat_id": chat_id,
                "text": message
            }
            response = requests.post(url, data=payload)
            print(response.content)
        elif new_status == "Подтвержден":
            message = "Заказ подтвержден! Ожидайте доставку"
            payload = {
                "chat_id": chat_id,
                "text": message
            }
            response = requests.post(url, data=payload)
            print(response.content)
        order.StatusID = status.StatusID
        db.session.commit()

        flash('Order status updated successfully', 'success')
    else:
        flash('Order not found', 'error')

    return redirect(url_for('index', page="order"))


@application.route('/edit_product', methods=['POST'])
def edit_product():
    product_id = request.args.get('product_id')

    product = Product.query.get(product_id)
    product.ProductName = request.form['product_name']
    product.Description = request.form['description']
    product.Price = float(request.form['price'])
    product.Size = request.form['size']
    product.Quantity = int(request.form['quantity'])
    product.ImgUrl = request.form['img_url']
    product.CategoryID = int(request.form['category_id'])

    db.session.commit()
    return redirect(url_for('index', page="edit"))


@application.route('/delete_product', methods=['POST'])
def delete_product():
    delete = request.args.get('delete')
    product = Product.query.get(delete)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('index', page="edit"))


@application.route('/add_product', methods=['POST'])
def add_product():
    form = AddProductForm()
    photo_filename = None
    if form.photo.data:
        if form.photo.data.filename.endswith(('jpg', 'jpeg', 'png')):
            photo_filename = f"img/{photos.save(form.photo.data)}"
        else:
            flash('Invalid photo format. Only JPG, JPEG, and PNG formats are allowed.', 'danger')
            return redirect(url_for('index', page="add_product"))
    if form.validate():
        new_product = Product(
            ProductName=form.product_name.data,
            Description=form.description.data,
            Price=form.price.data,
            Size=form.size.data,
            Quantity=form.quantity.data,
            ImgUrl=photo_filename,
            CategoryID=form.category_id.data
        )
        db.session.add(new_product)
        db.session.commit()

    return redirect(url_for('index', page="add_product"))


if __name__ == "__main__":
    application.run(host='0.0.0.0')
