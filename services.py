from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from models import User, Auction, Bid, Transaction
from extensions import db, bcrypt

class UserService:
    @staticmethod
    def register_user(data):
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        if User.query.filter_by(email=email).first():
            return {'message': 'Email already exists'}, 400

        user = User(email=email, username=username)
        user.set_password(password)
        print(user)
        db.session.add(user)
        db.session.commit()

        return {'message': 'User registered successfully'}

    @staticmethod
    def login_user(data):
        email = data.get('email')
        password = data.get('password')
        user = User.query.first()
        print(user.password_hash)


        user = User.query.filter_by(email=email).first()
        print(user)
        if not user:
            return {'message': 'Wrong email'}, 401

        if not user.check_password(password):
            return {'message': 'Wrong password'}, 401

        access_token = create_access_token(identity={"user_id": user.user_id, "role": user.role})
        return {'access_token': access_token, 'user_id': user.user_id}, 200


class AuctionService:
    # @staticmethod
    # def get_all_auctions():
    #     auctions = Auction.query.filter(Auction.end_time > datetime.utcnow()).all()
    #     return [{
    #         'auction_id': auction.auction_id,
    #         'title': auction.title,
    #         'description': auction.description,
    #         'image_url': auction.image_url,
    #         'starting_price': auction.starting_price,
    #         'start_time': auction.start_time,
    #         'end_time': auction.end_time
    #     } for auction in auctions]
    @staticmethod
    def get_all_auctions():
        return Auction.query.all()

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
