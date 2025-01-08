import logging
from datetime import datetime
from functools import wraps
from venv import logger

from flask import Flask, request, jsonify, make_response
from flask_bcrypt import check_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, verify_jwt_in_request

from models import Bid, Auction, Transaction, User, Log
from services import UserService, AuctionService
from extensions import db,jwt
from flask_cors import CORS
from flask_jwt_extended.exceptions import NoAuthorizationError, InvalidHeaderError
app = Flask(__name__)
cors = CORS(resources={r"/*": {"origins": "http://localhost:5173"}})
CORS(app, resources={r"/admin/*": {"origins": "*"}})
cors.init_app(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auction_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'AAAAAAAAAAAAAAA'
app.config['JWT_TOKEN_LOCATION'] = ['headers']

db.init_app(app)
jwt.init_app(app)

log_file = 'app_logs.txt'
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

app.logger.addHandler(file_handler)

# To jeszcze zmieniam(co niżej jest)
@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        return response


@app.errorhandler(InvalidHeaderError)
def handle_invalid_header_error(e):
    return jsonify({"msg": "Invalid Authorization Header"}), 422

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"msg": "Access denied. Admins only."}), 403
        return fn(*args, **kwargs)
    return wrapper
# Routes
@app.route('/admin', methods=['GET'])
@admin_required
def admin_panel():
    return {"message": "Welcome to the admin panel"}, 200
# @app.route('/admin', methods=['GET'])
# def admin():
#     try:
#         verify_jwt_in_request()
#         user_identity = get_jwt_identity()
#         print(f"User identity: {user_identity}, Type: {type(user_identity)}")
#
#         if not isinstance(user_identity, str):
#             return {'msg': 'Subject must be a string'}, 422
#
#         claims = get_jwt()
#         if claims.get('role') != 'admin':
#             return {'msg': 'Access denied. Admins only.'}, 403
#
#         return {'message': f'Welcome, admin {user_identity}'}, 200
#     except Exception as e:
#         return {'msg': str(e)}, 400




# @app.route('/admin/auctions', methods=['GET'])
# @jwt_required()
# def get_admin_auctions():
#     try:
#         user_id = get_jwt_identity()
#         claims = get_jwt()
#         role = claims.get('role')
#
#         if role != 'admin':
#             return jsonify({"msg": "Access denied"}), 403
#
#         # Fetch all auctions
#         auctions = AuctionService.get_all_auctions()
#         return jsonify(auctions), 200
#     except Exception as e:
#         app.logger.error(f"Error retrieving auctions: {str(e)}")
#         return jsonify({"msg": "Server error"}), 500




# def get_all_auctions():
#     user_id = get_jwt_identity()
#     user = User.query.get(user_id)
#     if user.role != "admin":
#         return jsonify({'message': 'Unauthorized access'}), 403
#
#     auctions = Auction.query.all()
#     return jsonify([{
#         'auction_id': auction.auction_id,
#         'title': auction.title,
#         'description': auction.description,
#         'starting_price': auction.starting_price,
#         'end_time': auction.end_time,
#         'user_id': auction.user_id
#     } for auction in auctions]), 200


# @app.route('/admin/auction', methods=['POST'])
# @jwt_required()
# def create_auction_admin():
#     user_id = get_jwt_identity()
#     user = User.query.get(user_id)
#     logging.INFO(f"rola={user.role}")
#     logging.INFO(f"")
#     if user.role != "admin":
#         logging.warning(f"rola={user.role}")
#         return jsonify({'message': 'Unauthorized access'}), 403
#
#     data = request.json
#     auction = Auction(
#         title=data['title'],
#         description=data['description'],
#         starting_price=data['starting_price'],
#         start_time=datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S'),
#         end_time=datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S'),
#         user_id=user_id
#     )
#     db.session.add(auction)
#     db.session.commit()
#     return jsonify({'message': 'Auction created successfully', 'auction_id': auction.auction_id}), 201


# @app.route('/admin/auction/<int:auction_id>', methods=['PUT'])
# @jwt_required()
# def edit_auction(auction_id):
#     user_id = get_jwt_identity()
#     user = User.query.get(user_id)
#
#     if user.role != "admin":
#         logging.warning(f"rola={user.role}")
#         return jsonify({'message': 'Unauthorized access'}), 403
#
#     data = request.json
#     auction = Auction.query.get_or_404(auction_id)
#
#     auction.title = data.get('title', auction.title)
#     auction.description = data.get('description', auction.description)
#     auction.starting_price = data.get('starting_price', auction.starting_price)
#     if 'start_time' in data:
#         auction.start_time = datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%S')
#     if 'end_time' in data:
#         auction.end_time = datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M:%S')
#
#     try:
#         db.session.commit()
#         return jsonify({'message': 'Auction updated successfully'}), 200
#     except Exception as e:
#         return jsonify({'message': f'Error updating auction: {str(e)}'}), 500

# @app.before_request
# def admin_routes_auth():
#     if request.path.startswith('/admin/'):
#         try:
#             verify_jwt_in_request()
#             claims = get_jwt()
#             if claims.get('role') != 'admin':
#                 return jsonify({'msg': 'Access denied. Admins only.'}), 403
#         except Exception as e:
#             app.logger.error(f'Authorization error: {e}')
#             return jsonify({'msg': 'Authorization error'}), 401

@app.route('/admin/auctions', methods=['GET'])
@admin_required
def get_admin_auctions():
    try:
        auctions = AuctionService.get_all_auctions()
        return jsonify(auctions), 200
    except Exception as e:
        app.logger.error(f"Error retrieving auctions: {e}")
        return jsonify({"msg": "Server error"}), 500


@app.route('/admin/auction', methods=['POST'])
def create_admin_auction():
    try:
        data = request.json
        auction = AuctionService.create_auction(data, get_jwt_identity())
        return jsonify({'msg': 'Auction created successfully', 'auction_id': auction.auction_id}), 201
    except Exception as e:
        app.logger.error(f"Error creating auction: {e}")
        return jsonify({'msg': 'Server error'}), 500

@app.route('/admin/auction/<int:auction_id>', methods=['PUT'])
def update_admin_auction(auction_id):
    try:
        data = request.json
        updated_auction = AuctionService.edit_auction(auction_id, data)
        return jsonify({'msg': 'Auction updated successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error updating auction: {e}")
        return jsonify({'msg': 'Server error'}), 500




@app.route('/register', methods=['POST'])
def register():
    data = request.json
    return jsonify(UserService.register_user(data)), 201


active_tokens = {}
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Znalezienie użytkownika
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid credentials'}), 401

    # Sprawdzanie, czy istnieje już aktywny token dla użytkownika
    user_id = str(user.user_id)
    if user_id in active_tokens:
        return {
            'access_token': active_tokens[user_id],
            'message': 'Reusing existing token'
        }, 200

    # Generowanie nowego tokena
    access_token = create_access_token(identity=str(user_id), additional_claims={'role': user.role})
    active_tokens[user_id] = access_token

    return {'access_token': access_token , 'user_id': user.user_id, 'role': user.role}, 200



@app.route('/auctions', methods=['POST'])
@jwt_required()
def create_auction():
    data = request.json
    user_id = get_jwt_identity()
    auction = AuctionService.create_auction(data, user_id)
    return jsonify({'message': 'Auction created successfully', 'auction_id': auction.auction_id}), 201

@app.route('/auctions', methods=['GET'])
def get_auctions():
    auctions = Auction.query.all()
    return jsonify([auction.to_dict() for auction in auctions]), 200


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
        'username': user.username,
        'role': user.role
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


from flask_jwt_extended import get_jwt_identity, get_jwt




if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # password = "123456"
    # hashed_password = "$2b$12$bVWnlTOIy6BEVIwamh/ED.OT7vblTlfZj.sUfyOwBA3VYAmAIu.hm"

    # print(check_password_hash(hashed_password, password))
    app.run(host='0.0.0.0', port=5000, debug=True)
