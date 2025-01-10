import json
from datetime import datetime, timedelta
from os import access
from venv import logger

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
        auction_data = []

        for auction in auctions:
            auction_data.append({
                'auction_id': auction.auction_id,
                'title': auction.title,
                'description': auction.description,
                'image_url': auction.image_url,
                'starting_price': auction.starting_price,
                'start_time': auction.start_time.isoformat() if auction.start_time else None,
                'end_time': auction.end_time.isoformat() if auction.end_time else None
            })

        return auction_data

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
            'status':auction.status,
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
        time_now = datetime.utcnow() + timedelta(hours=1)
        
        if auction.end_time > time_now:
            print("ggggggg")
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
    def check_auction_status(auction_id):
        auction = Auction.query.get_or_404(auction_id)
        transactions = Transaction.query.filter_by(auction_id=auction_id).first()
        time_now = datetime.utcnow() + timedelta(hours=1)
        if auction.end_time > time_now and auction.start_time < time_now:
            auction.status = "aktywna"
        else:
            auction.status = "nieaktywna"
        db.session.commit()
        print("cccccccccccccccccccccccccccccccccccc")
        if transactions is None and auction.end_time < time_now:
            print("ssssssssssssssssssssssssss")
            AuctionService.close_auction(auction_id)
        return auction

    @staticmethod
    def notify_winner(email, item, amount):
        from_email = "auctionsrvc@gmail.com" 
        from_password = "fszp jdid tjbn oobm"  
        body = f"Congratulations! You've won {item} for ${amount}. Plis proceed with payment. Item will be shipped to you soon. Bank account number: 1234567890"
        # Tworzenie wiadomości e-mail
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = email
        msg['Subject'] = f"Auction won! Item: {item}"  # Poprawiona linia, brakujący cudzysłów
        msg.attach(MIMEText(body, 'plain'))

        # Łączenie z serwerem SMTP Gmaila
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465) 
            server.login(from_email, from_password)  # Logowanie do konta Gmail
            text = msg.as_string()  # Zamiana wiadomości na format tekstowy
            server.sendmail(from_email, email, text)  # Wysyłanie e-maila
            server.quit()  # Zakończenie połączenia

            print(f'Email wysłany do {email}')
        except Exception as e:
            print(f'Wystąpił błąd podczas wysyłania e-maila: {e}')

        #print(f"Email sent to {email}: Congratulations! You've won {item} for ${amount}.")
