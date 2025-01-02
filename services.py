from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from models import User, Auction, Bid, Transaction
from extensions import db, bcrypt

class UserService:
    @staticmethod
    def register_user(data):
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user = User(email=data['email'], username=data['username'], password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        return {'message': 'User registered successfully'}

    @staticmethod
    def login_user(data):
        user = User.query.filter_by(email=data['email']).first()
        if user and bcrypt.check_password_hash(user.password_hash, data['password']):
            access_token = create_access_token(identity=user.user_id, expires_delta=timedelta(hours=1))
            return {'access_token': access_token}
        return {'message': 'Invalid credentials'}, 401

class AuctionService:
    @staticmethod
    def get_all_auctions():
        auctions = Auction.query.filter(Auction.end_time > datetime.utcnow()).all()
        return [{
            'auction_id': auction.auction_id,
            'title': auction.title,
            'description': auction.description,
            'image_url': auction.image_url,
            'starting_price': auction.starting_price,
            'start_time': auction.start_time,
            'end_time': auction.end_time
        } for auction in auctions]

    @staticmethod
    def get_auction_details(auction_id):
        auction = Auction.query.get_or_404(auction_id)
        bids = Bid.query.filter_by(auction_id=auction_id).order_by(Bid.bid_price.desc()).all()
        return {
            'auction_id': auction.auction_id,
            'title': auction.title,
            'description': auction.description,
            'image_url': auction.image_url,
            'starting_price': auction.starting_price,
            'start_time': auction.start_time,
            'end_time': auction.end_time,
            'bids': [{'user_id': bid.user_id, 'bid_price': bid.bid_price, 'bid_time': bid.bid_time} for bid in bids]
        }

    @staticmethod
    def close_auction(auction_id):
        auction = Auction.query.get_or_404(auction_id)
        if auction.end_time > datetime.utcnow():
            return {'message': 'Auction is still ongoing'}, 400
        highest_bid = Bid.query.filter_by(auction_id=auction_id).order_by(Bid.bid_price.desc()).first()
        if not highest_bid:
            return {'message': 'No bids placed'}, 400
        transaction = Transaction(auction_id=auction_id, winner_id=highest_bid.user_id)
        db.session.add(transaction)
        db.session.commit()
        winner = User.query.get(highest_bid.user_id)
        AuctionService.notify_winner(winner.email, auction.title, highest_bid.bid_price)
        return {'message': 'Auction closed and winner notified'}

    @staticmethod
    def notify_winner(email, item, amount):
        print(f"Email sent to {email}: Congratulations! You've won {item} for ${amount}.")
