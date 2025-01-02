from datetime import datetime
from extensions import db

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    auctions = db.relationship('Auction', backref='creator', lazy=True)
    bids = db.relationship('Bid', backref='bidder', lazy=True)
    transactions = db.relationship('Transaction', backref='winner', lazy=True)
    logs = db.relationship('Log', backref='user', lazy=True)

class Auction(db.Model):
    auction_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    starting_price = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    bids = db.relationship('Bid', backref='auction', lazy=True)
    transaction = db.relationship('Transaction', backref='auction', uselist=False, lazy=True)

class Bid(db.Model):
    bid_id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey('auction.auction_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    bid_price = db.Column(db.Float, nullable=False)
    bid_time = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    transaction_id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey('auction.auction_id'), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    payment_status = db.Column(db.String(20), default="pending")
    transaction_time = db.Column(db.DateTime, default=datetime.utcnow)

class Log(db.Model):
    log_id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
