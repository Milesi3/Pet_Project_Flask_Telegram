from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Category(db.Model):
    CategoryID = db.Column(db.Integer, primary_key=True)
    CategoryName = db.Column(db.String(100), nullable=False)
    products = db.relationship("Product", back_populates="category")

class Product(db.Model):
    ProductID = db.Column(db.Integer, primary_key=True)
    ProductName = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.Text, nullable=False)
    Price = db.Column(db.Float, nullable=False)
    Size = db.Column(db.String(100), nullable=False)
    Quantity = db.Column(db.Integer, default=0)
    ImgUrl = db.Column(db.String(100), nullable=False)
    CategoryID = db.Column(db.Integer, db.ForeignKey('category.CategoryID'))
    category = db.relationship("Category", back_populates="products")
    order_items = db.relationship("OrderItem", back_populates="product")



class User(db.Model):
    UserID = db.Column(db.Integer, primary_key=True)
    TG_ID = db.Column(db.Integer, nullable=False)
    FirstName = db.Column(db.String)
    LastName = db.Column(db.String)
    Email = db.Column(db.String)
    Phone = db.Column(db.String)
    Address = db.Column(db.String)
    orders = db.relationship("Order", back_populates="user")


class Order(db.Model):
    OrderID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('user.UserID'))
    OrderDate = db.Column(db.DateTime, default=datetime.utcnow)
    TotalAmount = db.Column(db.Float, nullable=False)
    StatusID = db.Column(db.Integer, db.ForeignKey('status.StatusID'))
    user = db.relationship("User", back_populates="orders")
    order_items = db.relationship("OrderItem", back_populates="order")
    status = db.relationship("Status", back_populates="order")

class Status(db.Model):
    StatusID = db.Column(db.Integer, primary_key=True)
    Status = db.Column(db.String(100), nullable=False)
    order = db.relationship("Order", back_populates="status")



class OrderItem(db.Model):
    OrderItemID = db.Column(db.Integer, primary_key=True)
    OrderID = db.Column(db.Integer, db.ForeignKey('order.OrderID'))
    ProductID = db.Column(db.Integer, db.ForeignKey('product.ProductID'))
    Quantity = db.Column(db.Integer)
    order = db.relationship("Order", back_populates="order_items")
    product = db.relationship("Product", back_populates="order_items")
