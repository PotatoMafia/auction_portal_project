import logging
import os
from datetime import datetime, timedelta
from functools import wraps
from venv import logger

from flask import Flask, request, jsonify, make_response, abort, send_from_directory
from flask_bcrypt import check_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, verify_jwt_in_request
from werkzeug.utils import secure_filename

from models import Bid, Auction, Transaction, User, Log
from services import UserService, AuctionService
from extensions import db, jwt
from flask_cors import CORS
from flask_jwt_extended.exceptions import NoAuthorizationError, InvalidHeaderError

app = Flask(__name__)
cors = CORS(resources={r"/*": {"origins": "http://localhost:5173"}})
CORS(app, resources={r"/admin/*": {"origins": "*"}})
cors.init_app(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auction_portal.db'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'AAAAAAAAAAAAAAA'
app.config['JWT_TOKEN_LOCATION'] = ['headers']

db.init_app(app)
jwt.init_app(app)


# log_file = 'app_logs.txt'
# file_handler = logging.FileHandler(log_file)
# file_handler.setLevel(logging.INFO)
# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# file_handler.setFormatter(formatter)
#
# app.logger.addHandler(file_handler)

# To jeszcze zmieniam(co niżej jest)


@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        return response


@app.before_request
def admin_routes_auth():
    if request.path.startswith('/admin'):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({'msg': 'Access denied. Admins only.'}), 403
        except Exception as e:
            return jsonify({'msg': 'Authorization error'}), 401


@app.errorhandler(InvalidHeaderError)
def handle_invalid_header_error(e):
    return jsonify({"msg": "Invalid Authorization Header"}), 422


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') != 'admin':
                abort(404)
        except Exception as e:
            abort(404)
        return fn(*args, **kwargs)

    return wrapper


@app.route('/tokencheck/<int:fn>', methods=['GET'])
def user_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') != 'user':
            return jsonify({"msg": "Access denied. user only."}), 403
        return fn(*args, **kwargs)

    return wrapper


# Routes
@app.route('/admin', methods=['GET'])
@admin_required
def admin_panel():
    return {"message": "Welcome to the admin panel"}, 200


UPLOAD_FOLDER = 'imagesForAuctions'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

from werkzeug.utils import secure_filename

@app.route('/imagesForAuctions/<filename>')
def get_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin/auction', methods=['POST'])
@admin_required
def create_admin_auction():
    try:
        app.logger.info("Received POST request to /admin/auction")
        data = request.form

        image = request.files.get('image')

        filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

        auction_data = {
            'title': data.get('title'),
            'description': data.get('description'),
            'starting_price': data.get('starting_price'),
            'start_time': data.get('start_time'),
            'end_time': data.get('end_time'),
            'user_id': data.get('user_id'),
            'status': data.get('status'),
            'image': filename,
        }

        auction = AuctionService.create_auction(auction_data, get_jwt_identity())
        return jsonify({'msg': 'Auction created successfully', 'auction_id': auction.auction_id}), 201
    except Exception as e:
        app.logger.error(f"Error creating auction: {e}")
        return jsonify({'msg': 'Server error'}), 500

@app.route('/admin/auction/<int:auction_id>', methods=['PUT'])
@admin_required
def update_admin_auction(auction_id):
    try:
        data = request.form.to_dict()
        image = request.files.get('image')

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_url = f"/{filename}"
            data['image_url'] = image_url
            app.logger.debug(f"Received data: {data}")
            app.logger.debug(f"Uploaded image: {image.filename}")
        updated_auction = AuctionService.edit_auction(auction_id, data)
        return jsonify({'msg': 'Auction updated successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error updating auction: {e}")
        return jsonify({'msg': 'Server error'}), 500

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    return jsonify(UserService.register_user(data)), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=str(user.user_id), additional_claims={'role': user.role})

    return {
        'access_token': access_token,
        'user_id': user.user_id,
        'username': user.username,
        'role': user.role
    }, 200


@app.route('/auctions', methods=['POST'])
##TODO:Autoryzacja tokeny szwankują
def create_auction():
    filename = None
    image = request.files.get('image')
    if image:
        print("IMAGE!")
    if image and allowed_file(image.filename):
        print("IMAGE2!")
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
    
    data = request.form.to_dict()
    data['image_url'] = filename
    auction = AuctionService.create_auction(data, data['user_id'])
    return jsonify({'message': 'Auction created successfully', 'auction_id': auction.auction_id}), 201


@app.route('/auctions', methods=['GET'])
def get_auctions():
    auctions = Auction.query.all()
    return jsonify([auction.to_dict() for auction in auctions]), 200


@app.route('/auction/<int:auction_id>', methods=['GET'])
def get_auction(auction_id):
    auction = AuctionService.get_auction_details(auction_id)
    if auction:
        return jsonify({
            'title': auction.get("title"),
            'description': auction.get("description"),
            'status': auction.get("status"),
            'starting_price': auction.get("starting_price"),
            'start_time': auction.get("start_time"),
            'end_time': auction.get("end_time"),
            'user_id': auction.get("user_id"),
            'bids': auction.get("bids")
        }), 200
    return jsonify({'message': 'Auction not found'}), 404


@app.route('/bid', methods=['POST'])
### TODO: MAKE IT WORK. Autoryzacja nie działa nwm czemu. @jwt_required()
def place_bid():
    data = request.json
    AuctionService.check_auction_status(auction_id=data['auction_id'])
    ##TODO: Może fajnie byłoby dodać nickname user = get_user(data['user_id'])
    auction = Auction.query.get_or_404(data['auction_id'])
    if auction.status == "nieaktywna":
        return jsonify({'message': 'Aukcja nieaktywna'}), 409
    bid = Bid(auction_id=data['auction_id'], user_id=data['user_id'], bid_price=data['bid_price'])
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
        'auction_title': bid.auction.title,
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
        'auction_title': transaction.auction.title,
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