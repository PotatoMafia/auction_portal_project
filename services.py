import json
from datetime import datetime, timedelta
from os import access
from venv import logger

from flask_jwt_extended import create_access_token, get_jwt_identity
from models import User, Auction, Bid, Transaction
from extensions import db, bcrypt
import logging

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


    # logging.basicConfig(level=logging.INFO)
    # logger = logging.getLogger(__name__)

    # @staticmethod
    # def login_user(data):
    #     email = data.get('email')
    #     password = data.get('password')
    #
    #     # Wyszukiwanie użytkownika po adresie email
    #     user = User.query.filter_by(email=email).first()
    #
    #     if not user:
    #         logger.warning(f"Nieudana próba logowania - nieprawidłowy email: {email}")
    #         return {'message': 'Nieprawidłowy email'}, 401
    #
    #     # Sprawdzenie hasła
    #     if not user.check_password(password):
    #         logger.warning(f"Nieudana próba logowania - nieprawidłowe hasło dla użytkownika: {email}")
    #         return {'message': 'Nieprawidłowe hasło'}, 401
    #
    #     # Logowanie informacji o użytkowniku
    #     logger.info(f"Użytkownik pomyślnie zalogowany: user_id={user.user_id}, email={user.email}, rola={user.role}")
    #
    #     # Tworzenie tokenu
    #     access_token = create_access_token(
    #         identity=user.user_id,  # Unikalny identyfikator
    #         additional_claims={"rola": user.role}  # Dodatkowe dane
    #     )
    #     logger.info(f"access_token: {access_token}, type: {type(access_token)}")
    #     logger.info(f"user.id: {user.user_id}, type: {type(user.user_id)}")
    #     logger.info(f"user.role: {user.role}, type: {type(user.role)}")
    #
    #     return {'access_token': access_token, 'user_id': user.user_id, 'role:': user.role}, 200



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
        auctions = Auction.query.all()
        return [{
            'auction_id': auction.auction_id,
            'title': auction.title,
            'description': auction.description,
            'image_url': auction.image_url,
            'starting_price': auction.starting_price,
            'start_time': auction.start_time.isoformat(),  # Ensure datetime is serialized
            'end_time': auction.end_time.isoformat()  # Ensure datetime is serialized
        } for auction in auctions]

    @staticmethod
    def edit_auction(auction_id, data):
        auction = Auction.query.get(auction_id)
        if not auction:
            raise ValueError(f"Auction with ID {auction_id} not found.")

        auction.title = data.get('title', auction.title)
        auction.description = data.get('description', auction.description)
        auction.starting_price = data.get('starting_price', auction.starting_price)
        auction.user_id = data.get('user_id', auction.user_id)

        try:
            if 'start_time' in data:
                auction.start_time = datetime.fromisoformat(data['start_time'])
            if 'end_time' in data:
                auction.end_time = datetime.fromisoformat(data['end_time'])
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")

        db.session.commit()

        return auction

    @staticmethod
    def create_auction(data, user_id):
        """
        Tworzenie nowej aukcji przez admina
        """
        title = data.get('title')
        description = data.get('description')
        starting_price = data.get('starting_price')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        # Walidacja danych
        if not title or not description or not starting_price or not start_time or not end_time:
            raise ValueError("Brak wymaganych danych do utworzenia aukcji")

        if datetime.fromisoformat(end_time) <= datetime.fromisoformat(start_time):
            raise ValueError("Data zakończenia musi być późniejsza niż data rozpoczęcia")

        # Tworzenie nowej aukcji
        auction = Auction(
            title=title,
            description=description,
            starting_price=starting_price,
            start_time=datetime.fromisoformat(start_time),
            end_time=datetime.fromisoformat(end_time),
            user_id=user_id
        )
        db.session.add(auction)
        db.session.commit()
        return auction

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
