from datetime import datetime

from flask import Flask, request, jsonify
from flask_bcrypt import check_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Bid, Auction, Transaction, User, Log
from services import UserService, AuctionService
from extensions import db,jwt
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auction_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'AAAAAAAAAAAAAAA'

db.init_app(app)
jwt.init_app(app)



# Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    return jsonify(UserService.register_user(data)), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    result = UserService.login_user(data)
    if isinstance(result, tuple):
        response, status_code = result
        return jsonify(response), status_code
    else:
        return jsonify({'error': 'Unexpected response from login_user'}), 500


@app.route('/auctions', methods=['POST'])
@jwt_required()
def create_auction():
    data = request.json
    user_id = get_jwt_identity()
    auction = AuctionService.create_auction(data, user_id)
    return jsonify({'message': 'Auction created successfully', 'auction_id': auction.auction_id}), 201

@app.route('/auctions', methods=['GET'])
def get_auctions():
    return jsonify(AuctionService.get_all_auctions()), 200

@app.route('/auction/<int:auction_id>', methods=['GET'])
def get_auction(auction_id):
    auction = Auction.query.get(auction_id)
    if auction:
        return jsonify({
            'title': auction.title,
            'description': auction.description,
            'starting_price': auction.starting_price,
            'end_time': auction.end_time
        }), 200
    return jsonify({'message': 'Auction not found'}), 404

@app.route('/bid', methods=['POST'])
@jwt_required()
def place_bid():
    data = request.json
    user_id = get_jwt_identity()
    auction = Auction.query.get_or_404(data['auction_id'])
    if auction.end_time < datetime.utcnow():
        return jsonify({'message': 'Auction has ended'}), 400
    bid = Bid(auction_id=data['auction_id'], user_id=user_id, bid_price=data['bid_price'])
    db.session.add(bid)
    db.session.commit()
    return jsonify({'message': 'Bid placed successfully'}), 201

@app.route('/close_auction/<int:auction_id>', methods=['POST'])
@jwt_required()
def close_auction(auction_id):
    return jsonify(AuctionService.close_auction(auction_id)), 200

@app.route('/')
def home():
    return jsonify({'message': 'Welcome to the Auction API!'})


@app.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user_id = int(user_id)
    except ValueError:
        return {'message': 'Invalid user ID'}, 400

    user = User.query.get(user_id)
    if not user:
        return {'message': 'User not found'}, 404

    return {
        'email': user.email,
        'username': user.username
    }, 200

@app.route('/user/<int:user_id>/bids', methods=['GET'])
def get_user_bids(user_id):
    bids = Bid.query.filter_by(user_id=user_id).all()
    return [{
        'bid_id': bid.bid_id,
        'auction_id': bid.auction_id,
        'bid_price': bid.bid_price,
        'bid_time': bid.bid_time
    } for bid in bids], 200

@app.route('/logs', methods=['GET'])
@jwt_required()
def get_logs():
    logs = Log.query.all()
    return jsonify([
        {
            'log_id': log.log_id,
            'action': log.action,
            'user_id': log.user_id,
            'timestamp': log.timestamp
        }
        for log in logs
    ]), 200

@app.route('/user/<int:user_id>/transactions', methods=['GET'])
def get_user_transactions(user_id):
    transactions = Transaction.query.filter_by(winner_id=user_id).all()
    return [{
        'transaction_id': transaction.transaction_id,
        'auction_id': transaction.auction_id,
        'payment_status': transaction.payment_status,
        'transaction_time': transaction.transaction_time
    } for transaction in transactions], 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    password = "123456"
    hashed_password = "$2b$12$bVWnlTOIy6BEVIwamh/ED.OT7vblTlfZj.sUfyOwBA3VYAmAIu.hm"

    # Проверяем
    print(check_password_hash(hashed_password, password))
    app.run(host='127.0.0.1', port=5000, debug=True)
